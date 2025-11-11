import axios, { AxiosInstance } from 'axios';
import type {
  User,
  Document,
  DocumentStats,
  ExtractedEntity,
  ProcessingLog,
  LoginCredentials,
  RegisterData,
  AuthToken,
  ProcessingStatus,
} from '@/types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.api.post<AuthToken>('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async register(data: RegisterData): Promise<User> {
    const response = await this.api.post<User>('/auth/register', data);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  // Documents
  async uploadDocument(
    file: File,
    documentType: string,
    processAsync: boolean = true
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('process_async', String(processAsync));

    const response = await this.api.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async listDocuments(
    skip: number = 0,
    limit: number = 50,
    statusFilter?: ProcessingStatus
  ): Promise<{ total: number; documents: Document[] }> {
    const params: any = { skip, limit };
    if (statusFilter) {
      params.status_filter = statusFilter;
    }

    const response = await this.api.get<{ total: number; documents: Document[] }>(
      '/documents/',
      { params }
    );
    return response.data;
  }

  async getDocument(documentId: number): Promise<Document> {
    const response = await this.api.get<Document>(`/documents/${documentId}`);
    return response.data;
  }

  async deleteDocument(documentId: number): Promise<void> {
    await this.api.delete(`/documents/${documentId}`);
  }

  async getDocumentEntities(documentId: number): Promise<ExtractedEntity[]> {
    const response = await this.api.get<ExtractedEntity[]>(
      `/documents/${documentId}/entities`
    );
    return response.data;
  }

  async getDocumentLogs(documentId: number): Promise<ProcessingLog[]> {
    const response = await this.api.get<ProcessingLog[]>(
      `/documents/${documentId}/logs`
    );
    return response.data;
  }

  async getDocumentStats(): Promise<DocumentStats> {
    const response = await this.api.get<DocumentStats>('/documents/stats/summary');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await axios.get('/health');
    return response.data;
  }
}

export const api = new ApiService();
