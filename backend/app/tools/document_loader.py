from typing import Any, Dict, List
from langchain.tools import BaseTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredImageLoader
from pydantic import Field
from loguru import logger
import tempfile
import os


class DocumentLoaderTool(BaseTool):
    """Tool to load and split documents for processing."""

    name: str = "document_loader"
    description: str = (
        "Load and parse documents (PDF, images) into text chunks. "
        "Input should be the file path to the document. "
        "Returns a dictionary with 'text' (full text) and 'chunks' (split text chunks)."
    )

    file_path: str = Field(default="")

    def _load_pdf(self, file_path: str) -> str:
        """Load PDF document and extract text."""
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            text = "\n\n".join([page.page_content for page in pages])
            logger.info(f"Loaded PDF with {len(pages)} pages from {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise

    def _load_image(self, file_path: str) -> str:
        """Load image document and extract text using OCR."""
        try:
            loader = UnstructuredImageLoader(file_path)
            docs = loader.load()
            text = "\n".join([doc.page_content for doc in docs])
            logger.info(f"Loaded image and extracted text from {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise

    def _split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """Split text into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks

    def _run(self, file_path: str) -> Dict[str, Any]:
        """Load and process document."""
        try:
            # Determine file type
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == ".pdf":
                text = self._load_pdf(file_path)
            elif file_ext in [".png", ".jpg", ".jpeg"]:
                text = self._load_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Split into chunks
            chunks = self._split_text(text)

            return {
                "text": text,
                "chunks": chunks,
                "num_chunks": len(chunks),
                "file_type": file_ext,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in document loader: {e}")
            return {
                "text": "",
                "chunks": [],
                "error": str(e),
                "success": False,
            }

    async def _arun(self, file_path: str) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(file_path)
