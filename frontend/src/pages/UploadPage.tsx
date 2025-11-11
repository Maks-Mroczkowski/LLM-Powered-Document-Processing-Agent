import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { api } from '@/services/api';
import { DocumentType } from '@/types';
import { Upload, FileText } from 'lucide-react';

export default function UploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType>(DocumentType.INVOICE);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file, documentType, true),
    onSuccess: (data) => navigate(`/documents/${data.id}`),
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => setSelectedFile(files[0]),
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    maxFiles: 1,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="px-4 py-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Upload Document</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
            isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-sm text-gray-600">
            {selectedFile ? (
              <span className="font-medium text-primary-600">{selectedFile.name}</span>
            ) : (
              <>Drag and drop a file here, or click to select</>
            )}
          </p>
          <p className="mt-2 text-xs text-gray-500">PDF, PNG, JPG up to 50MB</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Type
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as DocumentType)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            {Object.values(DocumentType).map((type) => (
              <option key={type} value={type}>
                {type.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={!selectedFile || uploadMutation.isPending}
          className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Upload and Process'}
        </button>
      </form>
    </div>
  );
}
