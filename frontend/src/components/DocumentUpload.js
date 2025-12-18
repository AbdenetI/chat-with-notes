import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { CloudArrowUpIcon, DocumentIcon } from '@heroicons/react/24/outline';
import { uploadDocument, extractErrorMessage } from '../services/api';

const DocumentUpload = ({ onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // File validation
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['pdf', 'txt', 'docx', 'md'];
    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    if (file.size > maxSize) {
      toast.error('File size must be less than 10MB');
      return;
    }

    if (!allowedTypes.includes(fileExtension)) {
      toast.error('Supported formats: PDF, TXT, DOCX, MD');
      return;
    }

    setIsUploading(true);
    
    try {
      await uploadDocument(file);
      toast.success(`${file.name} uploaded successfully!`);
      onUploadSuccess?.();
    } catch (error) {
      console.error('Upload error:', error);
      
      const errorMessage = extractErrorMessage(error, 'Upload failed');
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
    },
    multiple: false,
  });

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
        <CloudArrowUpIcon className="h-6 w-6 mr-2 text-primary-500" />
        Upload Document
      </h2>
      
      <div
        {...getRootProps()}
        className={`
          file-upload-zone border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} disabled={isUploading} />
        
        <DocumentIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        
        {isUploading ? (
          <div className="space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
            <p className="text-gray-600">Uploading and processing...</p>
          </div>
        ) : isDragActive ? (
          <p className="text-primary-600 font-medium">Drop the file here...</p>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">
              <span className="font-medium text-primary-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-sm text-gray-500">
              PDF, TXT, DOCX, MD (max 10MB)
            </p>
          </div>
        )}
      </div>
      
      <div className="mt-4 text-xs text-gray-500">
        <p>• Documents are processed using advanced AI for intelligent questioning</p>
        <p>• Uploaded files are securely stored and processed locally</p>
      </div>
    </div>
  );
};

export default DocumentUpload;