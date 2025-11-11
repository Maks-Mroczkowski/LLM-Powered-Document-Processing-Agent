from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import (
    User, Document, ProcessingStatus, DocumentType,
    ExtractedEntity, ProcessingLog
)
from app.api.schemas import (
    DocumentResponse, DocumentListResponse, DocumentStatsResponse,
    ExtractedEntityResponse, ProcessingLogResponse, TaskStatusResponse
)
from app.utils.auth import get_current_active_user
from app.services.storage_service import storage_service
from app.services.celery_worker import process_document_task
from app.agents.document_agent import document_agent
from app.config import settings
from loguru import logger
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    process_async: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a document for processing."""

    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext.replace(".", "") not in settings.supported_formats_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {settings.supported_formats}"
        )

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
        )

    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Valid types: {[t.value for t in DocumentType]}"
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"documents/{current_user.id}/{unique_filename}"

    # Upload to storage
    try:
        storage_service.upload_file(file.file, storage_path, file.content_type)
        logger.info(f"Uploaded file to storage: {storage_path}")
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=storage_path,
        file_size=file_size,
        mime_type=file.content_type,
        document_type=doc_type,
        status=ProcessingStatus.PENDING,
        user_id=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info(f"Created document record: {document.id}")

    # Process document (async or sync)
    if process_async:
        # Queue for async processing
        task = process_document_task.delay(
            document_id=document.id,
            file_path=storage_path,
            document_type=doc_type.value,
            user_email=current_user.email
        )
        logger.info(f"Queued document {document.id} for processing. Task ID: {task.id}")
    else:
        # Process synchronously (download file first)
        import tempfile
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, unique_filename)
        storage_service.download_file(storage_path, local_path)

        # Process with agent
        result = document_agent.process_document(
            file_path=local_path,
            document_type=doc_type,
            document_id=document.id,
            user_email=current_user.email
        )

        # Update document status
        if result.get("success"):
            document.status = ProcessingStatus.COMPLETED
            document.processed_at = datetime.utcnow()
        else:
            document.status = ProcessingStatus.FAILED
            document.error_message = result.get("error")

        db.commit()
        db.refresh(document)

    return document


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[ProcessingStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's documents."""
    query = db.query(Document).filter(Document.user_id == current_user.id)

    if status_filter:
        query = query.filter(Document.status == status_filter)

    total = query.count()
    documents = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "documents": documents
    }


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document by ID."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete from storage
    storage_service.delete_file(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    logger.info(f"Deleted document: {document_id}")
    return None


@router.get("/{document_id}/entities", response_model=List[ExtractedEntityResponse])
def get_document_entities(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get extracted entities for a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    entities = db.query(ExtractedEntity).filter(
        ExtractedEntity.document_id == document_id
    ).all()

    return entities


@router.get("/{document_id}/logs", response_model=List[ProcessingLogResponse])
def get_document_logs(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get processing logs for a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    logs = db.query(ProcessingLog).filter(
        ProcessingLog.document_id == document_id
    ).order_by(ProcessingLog.timestamp.asc()).all()

    return logs


@router.get("/stats/summary", response_model=DocumentStatsResponse)
def get_document_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document processing statistics."""
    user_docs = db.query(Document).filter(Document.user_id == current_user.id)

    total = user_docs.count()
    pending = user_docs.filter(Document.status == ProcessingStatus.PENDING).count()
    processing = user_docs.filter(Document.status == ProcessingStatus.PROCESSING).count()
    completed = user_docs.filter(Document.status == ProcessingStatus.COMPLETED).count()
    failed = user_docs.filter(Document.status == ProcessingStatus.FAILED).count()
    flagged = user_docs.filter(Document.status == ProcessingStatus.FLAGGED).count()

    # Calculate average processing time
    completed_docs = user_docs.filter(
        Document.status == ProcessingStatus.COMPLETED,
        Document.processed_at.isnot(None)
    ).all()

    avg_time = None
    if completed_docs:
        times = [
            (doc.processed_at - doc.uploaded_at).total_seconds()
            for doc in completed_docs
            if doc.processed_at and doc.uploaded_at
        ]
        if times:
            avg_time = sum(times) / len(times)

    return {
        "total_documents": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "flagged": flagged,
        "avg_processing_time_seconds": avg_time
    }
