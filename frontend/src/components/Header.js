import React from 'react';
import { DocumentTextIcon, SparklesIcon } from '@heroicons/react/24/outline';

const Header = () => {
  return (
    <header className="gradient-bg text-white shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <DocumentTextIcon className="h-8 w-8" />
              <SparklesIcon className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">RAG Chat with Notes</h1>
              <p className="text-blue-100 text-sm">
                AI-powered document analysis and conversation
              </p>
            </div>
          </div>
          
          <div className="hidden md:flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-blue-100">Enterprise AI Architecture</p>
              <p className="text-xs text-blue-200">React + FastAPI + RAG</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;