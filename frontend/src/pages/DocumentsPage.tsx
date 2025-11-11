import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '@/services/api';
import { ProcessingStatus } from '@/types';
import { formatDistanceToNow } from 'date-fns';

const statusColors = {
  [ProcessingStatus.PENDING]: 'bg-gray-100 text-gray-800',
  [ProcessingStatus.PROCESSING]: 'bg-blue-100 text-blue-800',
  [ProcessingStatus.COMPLETED]: 'bg-green-100 text-green-800',
  [ProcessingStatus.FAILED]: 'bg-red-100 text-red-800',
  [ProcessingStatus.FLAGGED]: 'bg-yellow-100 text-yellow-800',
};

export default function DocumentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.listDocuments(),
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="text-center py-12">Loading documents...</div>;
  }

  return (
    <div className="px-4 py-6">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
        <Link
          to="/upload"
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Upload Document
        </Link>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {data?.documents.map((doc) => (
            <li key={doc.id}>
              <Link
                to={`/documents/${doc.id}`}
                className="block hover:bg-gray-50 px-6 py-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {doc.original_filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      {doc.document_type} • Uploaded{' '}
                      {formatDistanceToNow(new Date(doc.uploaded_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div className="ml-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        statusColors[doc.status]
                      }`}
                    >
                      {doc.status}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {data?.documents.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No documents yet. Upload your first document to get started.
        </div>
      )}
    </div>
  );
}
