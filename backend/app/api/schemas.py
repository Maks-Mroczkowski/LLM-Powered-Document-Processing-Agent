from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.models import DocumentType, ProcessingStatus, WorkflowAction


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Document schemas
class DocumentUpload(BaseModel):
    document_type: DocumentType
    process_async: bool = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    status: ProcessingStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    agent_reasoning: Optional[str] = None
    workflow_action: Optional[WorkflowAction] = None
    error_message: Optional[str] = None
    user_id: int

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


# Processing Rule schemas
class ProcessingRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    document_type: DocumentType
    conditions: Dict[str, Any]
    action: WorkflowAction
    action_params: Optional[Dict[str, Any]] = None
    priority: int = 0


class ProcessingRuleResponse(ProcessingRuleCreate):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Task schemas
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    result: Optional[Any] = None
    error: Optional[str] = None


# Extraction schemas
class ExtractedEntityResponse(BaseModel):
    id: int
    entity_type: str
    entity_value: str
    confidence_score: float
    validated: bool
    validation_result: Optional[str] = None

    class Config:
        from_attributes = True


# Processing Log schemas
class ProcessingLogResponse(BaseModel):
    id: int
    step_name: str
    step_status: str
    details: Optional[str] = None
    execution_time_ms: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Stats schemas
class DocumentStatsResponse(BaseModel):
    total_documents: int
    pending: int
    processing: int
    completed: int
    failed: int
    flagged: int
    avg_processing_time_seconds: Optional[float] = None
