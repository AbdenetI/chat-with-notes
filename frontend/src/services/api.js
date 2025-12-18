import axios from 'axios';

// Utility function to safely extract error messages
const extractErrorMessage = (error, defaultMessage = 'An error occurred') => {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    if (typeof detail === 'string') {
      return detail;
    } else if (Array.isArray(detail)) {
      return detail.map(err => {
        if (typeof err === 'string') return err;
        if (typeof err === 'object' && err.msg) return `${err.loc?.join('.')}: ${err.msg}`;
        return 'Validation error';
      }).join(', ');
    } else if (typeof detail === 'object' && detail.msg) {
      return `${detail.loc?.join('.')}: ${detail.msg}`;
    }
  }
  
  if (error?.message && typeof error.message === 'string') {
    return error.message;
  }
  
  return defaultMessage;
};

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    
    // Handle FastAPI validation errors with proper error extraction
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      
      // If detail is an array of validation errors, extract messages
      if (Array.isArray(detail)) {
        const errorMessages = detail.map(err => {
          if (typeof err === 'object' && err.msg) {
            return `${err.loc?.join('.')}: ${err.msg}`;
          }
          return typeof err === 'string' ? err : JSON.stringify(err);
        });
        error.response.data.detail = errorMessages.join(', ');
      } else if (typeof detail === 'object' && detail.msg) {
        // Single validation error object
        error.response.data.detail = detail.msg;
      }
    }
    
    return Promise.reject(error);
  }
);

// API functions
export const healthCheck = () => api.get('/health');

export const uploadDocument = (file) => {
  console.log('Upload function called with:', {
    file: file,
    name: file?.name,
    size: file?.size,
    type: file?.type,
    fileType: typeof file,
    isFile: file instanceof File
  });
  
  if (!file) {
    throw new Error('No file provided');
  }
  
  const formData = new FormData();
  formData.append('file', file);
  
  // Debug FormData contents
  console.log('FormData entries:');
  for (let [key, value] of formData.entries()) {
    console.log(key, value);
  }
  
  console.log('Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type);
  
  // Use axios directly without the api instance to avoid the default Content-Type: application/json
  return axios.post(`${API_BASE_URL}/upload`, formData, {
    // Don't set any headers - let axios automatically set multipart/form-data
  });
};

export const chatWithDocuments = (message, sessionId = null) => {
  return api.post('/chat', {
    message,
    session_id: sessionId,
  });
};

export const getDocuments = () => api.get('/documents');

export const deleteDocument = (fileId) => api.delete(`/documents/${fileId}`);

export const getChatHistory = (sessionId) => api.get(`/sessions/${sessionId}/history`);

export { extractErrorMessage };
export default api;