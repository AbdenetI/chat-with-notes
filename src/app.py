"""
Main application module that ties together all components of the RAG system.
"""
import logging
from typing import Optional, Dict, List
from pathlib import Path

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .rag_engine import RAGEngine
from .config import UPLOADS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatWithNotesApp:
    """Main application class that coordinates all RAG components."""
    
    def __init__(self):
        """Initialize the application with all components."""
        try:
            # Initialize components
            self.document_processor = DocumentProcessor()
            self.vector_store = VectorStore()
            self.rag_engine = RAGEngine(self.vector_store)
            
            logger.info("Chat with Notes application initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            raise
    
    def upload_and_process_document(self, uploaded_file, filename: str) -> Dict:
        """Upload and process a document, adding it to the vector store."""
        try:
            # Process the uploaded file
            processed_data = self.document_processor.process_uploaded_file(
                uploaded_file, filename
            )
            
            # Add documents to vector store
            doc_ids = self.vector_store.add_documents(processed_data['documents'])
            
            # Return processing results
            result = {
                'success': True,
                'message': f"Successfully processed and indexed '{filename}'",
                'metadata': processed_data['metadata'],
                'chunk_count': processed_data['chunk_count'],
                'text_preview': processed_data['text_preview'],
                'document_ids': doc_ids
            }
            
            logger.info(f"Successfully processed document: {filename}")
            return result
            
        except Exception as e:
            error_msg = f"Error processing document '{filename}': {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
    
    def ask_question(self, question: str) -> Dict:
        """Ask a question and get an AI-generated answer based on uploaded documents."""
        try:
            response = self.rag_engine.generate_response(question, include_retrieval_info=True)
            return response
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'error': str(e)
            }
    
    def get_document_list(self) -> Dict[str, Dict]:
        """Get a list of all uploaded documents."""
        return self.vector_store.list_documents_by_file()
    
    def delete_document(self, file_id: str) -> Dict:
        """Delete a document and all its chunks from the vector store."""
        try:
            deleted_count = self.vector_store.delete_documents_by_file_id(file_id)
            
            if deleted_count > 0:
                return {
                    'success': True,
                    'message': f"Successfully deleted document and {deleted_count} associated chunks",
                    'deleted_count': deleted_count
                }
            else:
                return {
                    'success': False,
                    'message': "No documents found with the specified ID"
                }
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return {
                'success': False,
                'message': f"Error deleting document: {str(e)}",
                'error': str(e)
            }
    
    def clear_all_documents(self) -> Dict:
        """Clear all documents from the vector store."""
        try:
            success = self.vector_store.clear_collection()
            
            if success:
                # Also clear conversation history
                self.rag_engine.clear_conversation_history()
                
                return {
                    'success': True,
                    'message': "All documents and conversation history cleared successfully"
                }
            else:
                return {
                    'success': False,
                    'message': "Failed to clear documents"
                }
                
        except Exception as e:
            logger.error(f"Error clearing all documents: {e}")
            return {
                'success': False,
                'message': f"Error clearing documents: {str(e)}",
                'error': str(e)
            }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.rag_engine.get_conversation_history()
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.rag_engine.clear_conversation_history()
    
    def summarize_document(self, file_id: str) -> Dict:
        """Generate a summary of a specific document."""
        return self.rag_engine.summarize_document(file_id)
    
    def get_app_statistics(self) -> Dict:
        """Get comprehensive application statistics."""
        try:
            rag_stats = self.rag_engine.get_statistics()
            document_list = self.get_document_list()
            
            return {
                'total_files': len(document_list),
                'total_chunks': rag_stats['vector_store'].get('total_documents', 0),
                'conversation_turns': rag_stats['conversation_turns'],
                'files_info': document_list,
                'model_info': rag_stats['model_info'],
                'vector_store_info': rag_stats['vector_store']
            }
            
        except Exception as e:
            logger.error(f"Error getting app statistics: {e}")
            return {'error': str(e)}
    
    def search_documents(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for documents containing specific content."""
        try:
            # Use the RAG engine to retrieve relevant documents
            retrieved_docs, retrieval_info = self.rag_engine.retrieve_relevant_documents(
                query, k=max_results
            )
            
            search_results = []
            for doc in retrieved_docs:
                search_results.append({
                    'filename': doc.metadata.get('filename', 'Unknown'),
                    'file_id': doc.metadata.get('file_id', 'Unknown'),
                    'chunk_index': doc.metadata.get('chunk_index', 'Unknown'),
                    'content': doc.page_content,
                    'content_preview': doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []