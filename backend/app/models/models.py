from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class DocumentType(str, PyEnum):
    """Supported document types."""
    INVOICE = "invoice"
    CONTRACT = "contract"
    INSURANCE_CLAIM = "insurance_claim"
    RECEIPT = "receipt"
    OTHER = "other"


class ProcessingStatus(str, PyEnum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FLAGGED = "flagged"


class WorkflowAction(str, PyEnum):
    """Possible workflow actions."""
    APPROVE = "approve"
    REJECT = "reject"
    FLAG_FOR_REVIEW = "flag_for_review"
    REQUEST_MORE_INFO = "request_more_info"
    SEND_EMAIL = "send_email"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user")
    rules = relationship("ProcessingRule", back_populates="user")


class Document(Base):
    """Document model to track uploaded documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path in MinIO/S3
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)

    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Processing results
    extracted_data = Column(JSON, nullable=True)  # Structured extracted data
    confidence_scores = Column(JSON, nullable=True)  # Confidence for each field
    agent_reasoning = Column(Text, nullable=True)  # Agent's reasoning steps
    workflow_action = Column(Enum(WorkflowAction), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    extracted_entities = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="document", cascade="all, delete-orphan")


class ExtractedEntity(Base):
    """Stores individual extracted entities from documents."""
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # e.g., "invoice_number", "total_amount", "vendor_name"
    entity_value = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    validated = Column(Boolean, default=False)  # Validated against SQL database
    validation_result = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="extracted_entities")


class ProcessingRule(Base):
    """User-defined rules for document processing."""
    __tablename__ = "processing_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(Enum(DocumentType), nullable=False)

    # Rule conditions (stored as JSON)
    # Example: {"field": "total_amount", "operator": "greater_than", "value": 10000}
    conditions = Column(JSON, nullable=False)

    # Action to take when rule matches
    action = Column(Enum(WorkflowAction), nullable=False)
    action_params = Column(JSON, nullable=True)  # e.g., email template, recipient

    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules execute first
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="rules")


class ProcessingLog(Base):
    """Logs for document processing steps."""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    step_name = Column(String, nullable=False)  # e.g., "document_loading", "extraction", "validation"
    step_status = Column(String, nullable=False)  # "started", "completed", "failed"
    details = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Time taken for the step
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="processing_logs")


class VendorDatabase(Base):
    """Sample vendor database for validation."""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, nullable=False, index=True)
    vendor_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
