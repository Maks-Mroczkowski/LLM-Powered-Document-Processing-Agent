from typing import Any, Dict, List, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from loguru import logger
from app.tools.document_loader import DocumentLoaderTool
from app.tools.hf_qa_tool import HuggingFaceQATool, INVOICE_QUESTIONS, CONTRACT_QUESTIONS, INSURANCE_CLAIM_QUESTIONS
from app.tools.sql_validator import SQLValidatorTool
from app.tools.email_sender import EmailSenderTool
from app.models.models import DocumentType, WorkflowAction
import json


class DocumentProcessingAgent:
    """Intelligent agent for processing documents with reasoning capabilities."""

    def __init__(self, llm_model: str = "gpt-3.5-turbo", temperature: float = 0):
        """
        Initialize the document processing agent.

        Args:
            llm_model: LLM model to use (default: gpt-3.5-turbo)
            temperature: Model temperature for reasoning (0 = deterministic)
        """
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.tools = self._initialize_tools()
        self.agent_executor = self._create_agent()
        self.reasoning_log: List[Dict[str, Any]] = []

    def _initialize_tools(self) -> List:
        """Initialize all LangChain tools."""
        tools = [
            DocumentLoaderTool(),
            HuggingFaceQATool(),
            SQLValidatorTool(),
            EmailSenderTool(),
        ]
        logger.info(f"Initialized {len(tools)} tools for agent")
        return tools

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with reasoning capabilities."""

        system_prompt = """You are an intelligent document processing agent. Your job is to:

1. **Load and analyze documents** (invoices, contracts, insurance claims, receipts)
2. **Extract structured information** using question-answering
3. **Validate extracted data** against the database
4. **Make decisions** based on validation results and business rules
5. **Take actions** (approve, flag for review, send emails)

**Your workflow should be:**

Step 1: Load the document using the document_loader tool
Step 2: Analyze the document type and extract relevant fields using huggingface_qa_extractor
Step 3: Validate critical fields using sql_validator (e.g., vendor names, amounts, dates)
Step 4: Apply business rules and make a decision:
   - If total amount > $10,000: FLAG FOR REVIEW
   - If vendor not found in database: FLAG FOR REVIEW
   - If validation fails: FLAG FOR REVIEW
   - Otherwise: APPROVE
Step 5: Send notification email using email_sender

**Important:**
- Always explain your reasoning for each step
- Log all extracted data with confidence scores
- Be transparent about validation results
- Recommend actions based on business rules
- If uncertain, err on the side of caution (flag for review)

**Output format:**
Provide a detailed summary of:
- What you extracted
- What you validated
- Your reasoning process
- Your recommended action
- Any concerns or flags
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=10,
        )

        logger.info("Created agent executor")
        return agent_executor

    def _get_questions_for_document_type(self, doc_type: DocumentType) -> List[Dict[str, str]]:
        """Get appropriate questions based on document type."""
        question_map = {
            DocumentType.INVOICE: INVOICE_QUESTIONS,
            DocumentType.CONTRACT: CONTRACT_QUESTIONS,
            DocumentType.INSURANCE_CLAIM: INSURANCE_CLAIM_QUESTIONS,
        }
        return question_map.get(doc_type, INVOICE_QUESTIONS)

    def process_document(
        self,
        file_path: str,
        document_type: DocumentType,
        document_id: int,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document end-to-end.

        Args:
            file_path: Path to the document file
            document_type: Type of document
            document_id: Database ID of the document
            user_email: Email for notifications

        Returns:
            Processing results including extracted data, validation, and recommended action
        """
        try:
            logger.info(f"Processing document: {file_path} (type: {document_type})")

            # Create input for the agent
            input_text = f"""
Process this {document_type.value} document:

File path: {file_path}
Document ID: {document_id}
Document type: {document_type.value}

Please:
1. Load and analyze the document
2. Extract all relevant fields for a {document_type.value}
3. Validate the extracted data
4. Make a recommendation (approve/flag for review)
5. If user email is provided ({user_email}), send appropriate notification

Provide detailed reasoning for your decisions.
"""

            # Execute the agent
            result = self.agent_executor.invoke({"input": input_text})

            # Extract reasoning from intermediate steps
            reasoning_steps = []
            for step in result.get("intermediate_steps", []):
                action, observation = step
                reasoning_steps.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output": observation,
                })

            # Parse the final output
            output = result.get("output", "")

            return {
                "success": True,
                "document_id": document_id,
                "document_type": document_type.value,
                "agent_output": output,
                "reasoning_steps": reasoning_steps,
                "intermediate_steps": result.get("intermediate_steps", []),
            }

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id,
            }

    def extract_and_validate(
        self,
        file_path: str,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Extract and validate data without taking actions.

        Args:
            file_path: Path to the document
            document_type: Type of document

        Returns:
            Extracted and validated data
        """
        try:
            # Step 1: Load document
            loader = DocumentLoaderTool()
            load_result = loader._run(file_path)

            if not load_result.get("success"):
                return {"success": False, "error": "Failed to load document"}

            document_text = load_result["text"]

            # Step 2: Extract fields
            qa_tool = HuggingFaceQATool()
            questions = self._get_questions_for_document_type(document_type)

            extraction_input = json.dumps({
                "context": document_text,
                "questions": questions
            })

            extraction_result = qa_tool._run(extraction_input)

            if not extraction_result.get("success"):
                return {"success": False, "error": "Failed to extract data"}

            extractions = extraction_result["extractions"]

            # Step 3: Validate key fields
            validator = SQLValidatorTool()
            validations = {}

            for field, data in extractions.items():
                if field in ["vendor_name", "total_amount", "invoice_date"]:
                    validation_input = json.dumps({
                        "entity_type": field,
                        "entity_value": str(data.get("answer", ""))
                    })
                    validation_result = validator._run(validation_input)
                    validations[field] = validation_result

            return {
                "success": True,
                "extracted_data": extractions,
                "validations": validations,
                "document_text": document_text[:500],  # First 500 chars
            }

        except Exception as e:
            logger.error(f"Error in extract_and_validate: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
document_agent = DocumentProcessingAgent()
