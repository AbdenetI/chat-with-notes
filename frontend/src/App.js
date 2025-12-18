import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import { getDocuments, extractErrorMessage } from './services/api';

function App() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await getDocuments();
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      
      // Ensure error doesn't get rendered as React child
      const errorMessage = extractErrorMessage(error, 'Failed to load documents');
      
      // Could show toast error here if desired
      // toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDocumentUploaded = () => {
    // Refresh document list when a new document is uploaded
    fetchDocuments();
  };

  const handleDocumentDeleted = () => {
    // Refresh document list when a document is deleted
    fetchDocuments();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <Toaster position="top-right" />
      
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Document Management */}
          <div className="lg:col-span-1 space-y-6">
            <DocumentUpload onUploadSuccess={handleDocumentUploaded} />
            <DocumentList 
              documents={documents}
              isLoading={isLoading}
              onDocumentDeleted={handleDocumentDeleted}
            />
          </div>
          
          {/* Right Column - Chat Interface */}
          <div className="lg:col-span-2">
            <ChatInterface 
              sessionId={currentSessionId}
              onSessionChange={setCurrentSessionId}
              hasDocuments={documents.length > 0}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;