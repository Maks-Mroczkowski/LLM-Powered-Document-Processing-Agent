export enum DocumentType {
  INVOICE = 'invoice',
  CONTRACT = 'contract',
  INSURANCE_CLAIM = 'insurance_claim',
  RECEIPT = 'receipt',
  OTHER = 'other',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  FLAGGED = 'flagged',
}

export enum WorkflowAction {
  APPROVE = 'approve',
  REJECT = 'reject',
  FLAG_FOR_REVIEW = 'flag_for_review',
  REQUEST_MORE_INFO = 'request_more_info',
  SEND_EMAIL = 'send_email',
}

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  document_type: DocumentType;
  status: ProcessingStatus;
  uploaded_at: string;
  processed_at?: string;
  extracted_data?: Record<string, any>;
  confidence_scores?: Record<string, number>;
  agent_reasoning?: string;
  workflow_action?: WorkflowAction;
  error_message?: string;
  user_id: number;
}

export interface DocumentStats {
  total_documents: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  flagged: number;
  avg_processing_time_seconds?: number;
}

export interface ExtractedEntity {
  id: number;
  entity_type: string;
  entity_value: string;
  confidence_score: number;
  validated: boolean;
  validation_result?: string;
}

export interface ProcessingLog {
  id: number;
  step_name: string;
  step_status: string;
  details?: string;
  execution_time_ms?: number;
  timestamp: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
