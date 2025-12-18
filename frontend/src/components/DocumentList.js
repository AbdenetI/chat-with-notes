import React from 'react';
import toast from 'react-hot-toast';
import { 
  DocumentIcon, 
  TrashIcon, 
  CalendarIcon,
  DocumentTextIcon 
} from '@heroicons/react/24/outline';
import { deleteDocument, extractErrorMessage } from '../services/api';

const DocumentList = ({ documents, isLoading, onDocumentDeleted }) => {
  const handleDeleteDocument = async (fileId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteDocument(fileId);
      toast.success('Document deleted successfully');
      onDocumentDeleted?.();
    } catch (error) {
      console.error('Delete error:', error);
      
      const errorMessage = extractErrorMessage(error, 'Failed to delete document');
      toast.error(errorMessage);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          <DocumentTextIcon className="h-6 w-6 mr-2 text-primary-500" />
          Your Documents
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
        <DocumentTextIcon className="h-6 w-6 mr-2 text-primary-500" />
        Your Documents
        <span className="ml-2 bg-primary-100 text-primary-700 text-sm px-2 py-1 rounded-full">
          {documents.length}
        </span>
      </h2>

      {documents.length === 0 ? (
        <div className="text-center py-8">
          <DocumentIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">No documents uploaded yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Upload your first document to start chatting
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="document-card border border-gray-200 rounded-lg p-4 hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1 min-w-0">
                  <DocumentIcon className="h-8 w-8 text-primary-500 flex-shrink-0 mt-1" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {doc.filename}
                    </h3>
                    <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span className="flex items-center">
                        <CalendarIcon className="h-3 w-3 mr-1" />
                        {formatDate(doc.upload_time)}
                      </span>
                    </div>
                    <div className="mt-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                        ${doc.status === 'processed' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {doc.status}
                      </span>
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                  className="flex-shrink-0 p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete document"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentList;