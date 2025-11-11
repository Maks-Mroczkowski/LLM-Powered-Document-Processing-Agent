import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { ProcessingStatus } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle, AlertCircle, Clock, FileText } from 'lucide-react';

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const documentId = parseInt(id || '0');

  const { data: document, isLoading } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => api.getDocument(documentId),
    refetchInterval: (data) =>
      data?.status === ProcessingStatus.PROCESSING || data?.status === ProcessingStatus.PENDING
        ? 3000
        : false,
  });

  if (isLoading) {
    return <div className="text-center py-12">Loading document...</div>;
  }

  if (!document) {
    return <div className="text-center py-12">Document not found</div>;
  }

  const StatusIcon = {
    [ProcessingStatus.COMPLETED]: CheckCircle,
    [ProcessingStatus.FAILED]: AlertCircle,
    [ProcessingStatus.PROCESSING]: Clock,
    [ProcessingStatus.PENDING]: Clock,
    [ProcessingStatus.FLAGGED]: AlertCircle,
  }[document.status];

  return (
    <div className="px-4 py-6 max-w-5xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <FileText className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {document.original_filename}
              </h1>
              <p className="text-sm text-gray-500">
                Uploaded {formatDistanceToNow(new Date(document.uploaded_at), { addSuffix: true })}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <StatusIcon className="h-6 w-6" />
            <span className="text-lg font-medium capitalize">{document.status}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Type:</span>{' '}
            <span className="font-medium">{document.document_type}</span>
          </div>
          <div>
            <span className="text-gray-500">Size:</span>{' '}
            <span className="font-medium">{(document.file_size / 1024).toFixed(2)} KB</span>
          </div>
        </div>
      </div>

      {document.extracted_data && Object.keys(document.extracted_data).length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Extracted Data</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(document.extracted_data).map(([key, value]) => (
              <div key={key} className="border rounded-lg p-4">
                <p className="text-sm text-gray-500 mb-1">{key.replace(/_/g, ' ').toUpperCase()}</p>
                <p className="text-lg font-medium">{value as string}</p>
                {document.confidence_scores?.[key] && (
                  <p className="text-xs text-gray-500 mt-1">
                    Confidence: {(document.confidence_scores[key] * 100).toFixed(1)}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {document.agent_reasoning && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Agent Reasoning</h2>
          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-md text-sm">
              {document.agent_reasoning}
            </pre>
          </div>
        </div>
      )}

      {document.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Error</h3>
          <p className="text-red-700 text-sm">{document.error_message}</p>
        </div>
      )}

      {document.status === ProcessingStatus.PROCESSING && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <Clock className="h-8 w-8 text-blue-600 mx-auto mb-2 animate-spin" />
          <p className="text-blue-800 font-medium">Processing document...</p>
          <p className="text-blue-600 text-sm">This may take a few minutes</p>
        </div>
      )}
    </div>
  );
}
