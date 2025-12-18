import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { 
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { chatWithDocuments, getChatHistory, extractErrorMessage } from '../services/api';

const ChatInterface = ({ sessionId, onSessionChange, hasDocuments }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat history when session changes
  useEffect(() => {
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    }
  }, [currentSessionId]);

  const loadChatHistory = async (sessionId) => {
    try {
      const response = await getChatHistory(sessionId);
      const history = response.data.history || [];
      
      const formattedMessages = history.flatMap(item => {
        // Ensure sources is always a valid array of objects/strings
        const safeSources = Array.isArray(item.sources) 
          ? item.sources.filter(source => source && (typeof source === 'string' || (typeof source === 'object' && source.filename)))
          : [];
          
        return [
          {
            id: `user-${item.timestamp}`,
            type: 'user',
            content: String(item.user_message || ''),
            timestamp: new Date(item.timestamp),
          },
          {
            id: `assistant-${item.timestamp}`,
            type: 'assistant',
            content: String(item.assistant_response || ''),
            timestamp: new Date(item.timestamp),
            sources: safeSources,
          }
        ];
      });
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;
    
    if (!hasDocuments) {
      toast.error('Please upload a document first to start chatting');
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatWithDocuments(inputMessage, currentSessionId);
      const { response: aiResponse, session_id, sources } = response.data;

      // Update session ID if this is a new session
      if (!currentSessionId || currentSessionId !== session_id) {
        setCurrentSessionId(session_id);
        onSessionChange?.(session_id);
      }

      // Ensure sources is always a valid array and response is a string
      const safeSources = Array.isArray(sources) 
        ? sources.filter(source => source && (typeof source === 'string' || (typeof source === 'object' && source.filename)))
        : [];

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: String(aiResponse || 'Response unavailable'),
        timestamp: new Date(),
        sources: safeSources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMessage = extractErrorMessage(error, 'Failed to get response');
      toast.error(errorMessage);
      
      const errorMessageObj = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        sources: [],
      };
      
      setMessages(prev => [...prev, errorMessageObj]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    
    return (
      <div
        key={message.id}
        className={`chat-message flex items-start space-x-3 ${
          isUser ? 'justify-end' : 'justify-start'
        }`}
      >
        {!isUser && (
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
              <SparklesIcon className="h-4 w-4 text-white" />
            </div>
          </div>
        )}
        
        <div
          className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-primary-500 text-white rounded-br-sm'
              : 'bg-gray-100 text-gray-800 rounded-bl-sm'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {typeof message.content === 'string' ? message.content : String(message.content || 'Message content unavailable')}
          </p>
          
          {message.sources && message.sources.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-500 mb-1">Sources:</p>
              {message.sources.map((source, index) => {
                // Ensure source data is always strings to prevent object rendering errors
                const sourceText = typeof source === 'object' && source.filename 
                  ? String(source.filename)
                  : typeof source === 'string' 
                    ? source 
                    : `Source ${index + 1}`;
                
                return (
                  <div key={index} className="text-xs text-gray-600">
                    • {sourceText}
                  </div>
                );
              })}
            </div>
          )}
          
          <p className="text-xs mt-2 opacity-70">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
        
        {isUser && (
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <UserIcon className="h-4 w-4 text-gray-600" />
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center">
          <ChatBubbleLeftRightIcon className="h-6 w-6 mr-2 text-primary-500" />
          AI Chat Assistant
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Ask questions about your uploaded documents
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-container">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <SparklesIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-500">
              {hasDocuments 
                ? 'Start a conversation about your documents'
                : 'Upload a document to begin chatting'
              }
            </p>
            {hasDocuments && (
              <div className="mt-4 space-y-2 text-sm text-gray-400">
                <p>• "What is this document about?"</p>
                <p>• "Summarize the key points"</p>
                <p>• "Explain the main concepts"</p>
              </div>
            )}
          </div>
        ) : (
          messages.filter(message => message && typeof message === 'object' && message.id).map(renderMessage)
        )}
        
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                <SparklesIcon className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="bg-gray-100 rounded-lg rounded-bl-sm px-4 py-3">
              <div className="typing-indicator text-gray-600">
                Thinking
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <form onSubmit={handleSendMessage} className="flex space-x-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={
              hasDocuments 
                ? "Ask a question about your documents..." 
                : "Upload a document first..."
            }
            disabled={!hasDocuments || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!hasDocuments || !inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;