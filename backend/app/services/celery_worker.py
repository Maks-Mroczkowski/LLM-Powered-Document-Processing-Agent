from celery import Celery
from app.config import settings
from loguru import logger

# Initialize Celery
celery_app = Celery(
    "document_processor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True, name="process_document_task")
def process_document_task(
    self,
    document_id: int,
    file_path: str,
    document_type: str,
    user_email: str = None
):
    """
    Celery task to process a document asynchronously.

    Args:
        document_id: Database ID of the document
        file_path: Local file path or storage path
        document_type: Type of document (invoice, contract, etc.)
        user_email: Optional user email for notifications
    """
    from app.database import SessionLocal
    from app.models.models import Document, ProcessingStatus, DocumentType
    from app.agents.document_agent import document_agent
    from datetime import datetime
    import tempfile
    import os

    db = SessionLocal()
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.status = ProcessingStatus.PROCESSING
        db.commit()

        logger.info(f"[Task {self.request.id}] Processing document {document_id}")

        # If file_path is from storage, download it
        local_file_path = file_path
        if file_path.startswith("documents/"):
            from app.services.storage_service import storage_service
            temp_dir = tempfile.mkdtemp()
            local_file_path = os.path.join(temp_dir, os.path.basename(file_path))
            storage_service.download_file(file_path, local_file_path)
            logger.info(f"Downloaded file from storage to {local_file_path}")

        # Process document with agent
        doc_type = DocumentType(document_type)
        result = document_agent.process_document(
            file_path=local_file_path,
            document_type=doc_type,
            document_id=document_id,
            user_email=user_email
        )

        # Update document with results
        if result.get("success"):
            # Extract data from reasoning steps
            extracted_data = {}
            confidence_scores = {}

            for step in result.get("reasoning_steps", []):
                if step.get("tool") == "huggingface_qa_extractor":
                    output = step.get("output", {})
                    if output.get("success"):
                        extractions = output.get("extractions", {})
                        for field, data in extractions.items():
                            extracted_data[field] = data.get("answer")
                            confidence_scores[field] = data.get("confidence", 0.0)

            document.status = ProcessingStatus.COMPLETED
            document.extracted_data = extracted_data
            document.confidence_scores = confidence_scores
            document.agent_reasoning = result.get("agent_output", "")
            document.processed_at = datetime.utcnow()

            # Determine workflow action based on agent reasoning
            agent_output = result.get("agent_output", "").lower()
            if "flag" in agent_output or "review" in agent_output:
                document.status = ProcessingStatus.FLAGGED
            elif "approve" in agent_output:
                document.status = ProcessingStatus.COMPLETED

        else:
            document.status = ProcessingStatus.FAILED
            document.error_message = result.get("error", "Unknown error")

        db.commit()

        logger.info(f"[Task {self.request.id}] Completed processing document {document_id}")

        return {
            "document_id": document_id,
            "status": document.status.value,
            "extracted_data": extracted_data if result.get("success") else None,
        }

    except Exception as e:
        logger.error(f"[Task {self.request.id}] Error processing document: {e}")

        # Update document status to failed
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = ProcessingStatus.FAILED
                document.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating document status: {db_error}")

        raise

    finally:
        db.close()


@celery_app.task(name="cleanup_old_documents")
def cleanup_old_documents():
    """Periodic task to clean up old documents."""
    from app.database import SessionLocal
    from app.models.models import Document
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        # Delete documents older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_docs = db.query(Document).filter(Document.uploaded_at < cutoff_date).all()

        for doc in old_docs:
            # Delete from storage
            from app.services.storage_service import storage_service
            storage_service.delete_file(doc.file_path)

            # Delete from database
            db.delete(doc)

        db.commit()
        logger.info(f"Cleaned up {len(old_docs)} old documents")

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
    finally:
        db.close()
