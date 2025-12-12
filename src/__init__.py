"""
Chat with Notes - A RAG (Retrieval Augmented Generation) Application

This package provides a complete RAG system that allows users to upload documents
and have intelligent conversations with their content using AI.

Components:
- Document processing (PDF, DOCX, TXT)
- Vector database (ChromaDB)
- RAG engine (LangChain + OpenAI)
- Web interface (Streamlit)
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Chat with your Notes - RAG Application"

from .app import ChatWithNotesApp
from .config import *

__all__ = ['ChatWithNotesApp']