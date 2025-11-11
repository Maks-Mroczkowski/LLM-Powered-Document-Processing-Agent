from typing import Any, Dict, List
from langchain.tools import BaseTool
from pydantic import Field
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
from loguru import logger
from app.config import settings
import torch


class HuggingFaceQATool(BaseTool):
    """Tool to extract information from documents using HuggingFace QA models."""

    name: str = "huggingface_qa_extractor"
    description: str = (
        "Extract specific information from document text using question answering. "
        "Input should be a JSON string with 'context' (document text) and 'questions' (list of questions). "
        "Returns extracted answers with confidence scores."
    )

    model_name: str = Field(default=settings.hf_model_name)
    qa_pipeline: Any = Field(default=None, exclude=True)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the QA model."""
        try:
            logger.info(f"Loading HuggingFace model: {self.model_name}")

            # For document understanding, we use a model that can handle layout
            # In production, you might want to use LayoutLMv3 or similar
            # For now, we'll use a standard QA model
            device = 0 if torch.cuda.is_available() else -1

            self.qa_pipeline = pipeline(
                "question-answering",
                model=self.model_name,
                device=device,
            )
            logger.info("QA model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to a simpler model
            logger.info("Falling back to distilbert-base model")
            self.qa_pipeline = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=-1,
            )

    def _extract_field(self, context: str, question: str) -> Dict[str, Any]:
        """Extract a single field using QA."""
        try:
            result = self.qa_pipeline(question=question, context=context)
            return {
                "answer": result["answer"],
                "confidence": result["score"],
                "start": result["start"],
                "end": result["end"],
            }
        except Exception as e:
            logger.error(f"Error extracting field: {e}")
            return {
                "answer": None,
                "confidence": 0.0,
                "error": str(e),
            }

    def _run(self, input_str: str) -> Dict[str, Any]:
        """Extract information from document."""
        try:
            import json
            input_data = json.loads(input_str)
            context = input_data.get("context", "")
            questions = input_data.get("questions", [])

            if not context or not questions:
                return {
                    "success": False,
                    "error": "Missing context or questions",
                }

            results = {}
            for q in questions:
                field_name = q.get("field", "unknown")
                question_text = q.get("question", "")

                logger.info(f"Extracting field: {field_name}")
                extraction = self._extract_field(context, question_text)
                results[field_name] = extraction

            return {
                "success": True,
                "extractions": results,
            }

        except Exception as e:
            logger.error(f"Error in HF QA tool: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _arun(self, input_str: str) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(input_str)


# Predefined question templates for common document types
INVOICE_QUESTIONS = [
    {"field": "invoice_number", "question": "What is the invoice number?"},
    {"field": "invoice_date", "question": "What is the invoice date?"},
    {"field": "total_amount", "question": "What is the total amount?"},
    {"field": "vendor_name", "question": "What is the vendor name?"},
    {"field": "due_date", "question": "What is the due date?"},
    {"field": "tax_amount", "question": "What is the tax amount?"},
]

CONTRACT_QUESTIONS = [
    {"field": "contract_number", "question": "What is the contract number?"},
    {"field": "contract_date", "question": "What is the contract date?"},
    {"field": "contract_value", "question": "What is the contract value?"},
    {"field": "parties", "question": "Who are the parties involved?"},
    {"field": "effective_date", "question": "What is the effective date?"},
    {"field": "termination_date", "question": "What is the termination date?"},
]

INSURANCE_CLAIM_QUESTIONS = [
    {"field": "claim_number", "question": "What is the claim number?"},
    {"field": "claim_date", "question": "What is the claim date?"},
    {"field": "claim_amount", "question": "What is the claim amount?"},
    {"field": "policy_number", "question": "What is the policy number?"},
    {"field": "claimant_name", "question": "What is the claimant name?"},
    {"field": "incident_date", "question": "What is the incident date?"},
]
