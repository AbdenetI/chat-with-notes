"""
Vector database integration using ChromaDB for storing and retrieving document embeddings.
"""
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document as LangChainDocument

from .config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, VECTOR_DB_DIR, 
    VECTOR_DB_NAME, SIMILARITY_THRESHOLD, MAX_RETRIEVED_DOCS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database operations for document embeddings and retrieval."""
    
    def __init__(self):
        """Initialize the vector store with ChromaDB and OpenAI embeddings."""
        try:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=OPENAI_API_KEY,
                model=EMBEDDING_MODEL
            )
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(VECTOR_DB_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection_name = VECTOR_DB_NAME
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except ValueError:
                self.collection = self.client.create_collection(self.collection_name)
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Initialize LangChain Chroma vectorstore
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def add_documents(self, documents: List[LangChainDocument]) -> List[str]:
        """Add documents to the vector store."""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            # Add documents to vectorstore
            doc_ids = self.vectorstore.add_documents(documents)
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = None) -> List[LangChainDocument]:
        """Perform similarity search to find relevant documents."""
        try:
            k = k or MAX_RETRIEVED_DOCS
            
            # Perform similarity search
            results = self.vectorstore.similarity_search(
                query=query,
                k=k
            )
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """Perform similarity search with similarity scores."""
        try:
            k = k or MAX_RETRIEVED_DOCS
            
            # Perform similarity search with scores
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )
            
            # Filter by similarity threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= SIMILARITY_THRESHOLD
            ]
            
            logger.info(f"Found {len(filtered_results)} documents above similarity threshold")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error performing similarity search with scores: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the current collection."""
        try:
            count = self.collection.count()
            
            return {
                'total_documents': count,
                'collection_name': self.collection_name,
                'embedding_model': EMBEDDING_MODEL
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}
    
    def delete_documents_by_metadata(self, metadata_filter: Dict) -> int:
        """Delete documents based on metadata filter."""
        try:
            # Get documents matching the filter
            results = self.vectorstore.get(where=metadata_filter)
            
            if results['ids']:
                # Delete the documents
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                logger.info(f"Deleted {deleted_count} documents matching filter")
                return deleted_count
            else:
                logger.info("No documents found matching the filter")
                return 0
                
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0
    
    def delete_documents_by_file_id(self, file_id: str) -> int:
        """Delete all documents associated with a specific file."""
        return self.delete_documents_by_metadata({'file_id': file_id})
    
    def list_documents_by_file(self) -> Dict[str, Dict]:
        """List documents grouped by file."""
        try:
            # Get all documents
            all_docs = self.collection.get()
            
            files_info = {}
            
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    file_id = metadata.get('file_id', 'unknown')
                    filename = metadata.get('filename', 'unknown')
                    
                    if file_id not in files_info:
                        files_info[file_id] = {
                            'filename': filename,
                            'chunk_count': 0,
                            'upload_timestamp': metadata.get('upload_timestamp'),
                            'file_type': metadata.get('file_type'),
                            'file_size': metadata.get('file_size')
                        }
                    
                    files_info[file_id]['chunk_count'] += 1
            
            return files_info
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(self.collection_name)
            
            # Reinitialize the vectorstore
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            
            logger.info("Collection cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def search_by_metadata(self, metadata_filter: Dict, limit: int = 10) -> List[Dict]:
        """Search documents by metadata criteria."""
        try:
            results = self.collection.get(
                where=metadata_filter,
                limit=limit
            )
            
            documents = []
            if results['documents'] and results['metadatas']:
                for i, doc_text in enumerate(results['documents']):
                    documents.append({
                        'id': results['ids'][i],
                        'text': doc_text,
                        'metadata': results['metadatas'][i]
                    })
            
            logger.info(f"Found {len(documents)} documents matching metadata filter")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []
    
    def get_retriever(self, search_kwargs: Optional[Dict] = None):
        """Get a LangChain retriever for the vector store."""
        search_kwargs = search_kwargs or {'k': MAX_RETRIEVED_DOCS}
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)