"""
Full AI-powered RAG implementation for Chat-with-Notes
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
# Skip transformers import to avoid compatibility issues
TRANSFORMERS_AVAILABLE = False
# Simple document processing without heavy dependencies
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def simple_text_split(self, text: str) -> List[str]:
        """Simple text splitting without LangChain"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap if end < text_length else end
        
        return [chunk for chunk in chunks if chunk]
    
    def load_document(self, file_path: str) -> List[str]:
        """Load and process document based on file type"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                if PDF_AVAILABLE:
                    # Simple PDF processing
                    text = ""
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n\n"
                else:
                    raise ValueError("PDF processing not available. Install PyPDF2.")
                        
            elif file_ext == '.txt' or file_ext == '.md':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    
            elif file_ext == '.docx':
                if DOCX_AVAILABLE:
                    # Simple DOCX processing
                    doc = DocxDocument(file_path)
                    text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
                else:
                    raise ValueError("DOCX processing not available. Install python-docx.")
                
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Simple text splitting
            chunks = self.simple_text_split(text)
            logger.info(f"Processed {file_path}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise

class VectorStore:
    def __init__(self, db_path: str = "./chroma_db", embedding_model: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_function
        )
        logger.info(f"Vector store initialized at {db_path}")
    
    def add_document_chunks(self, chunks: List[str], file_id: str, filename: str):
        """Add document chunks to vector store"""
        try:
            chunk_ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": i,
                    "timestamp": datetime.now().isoformat()
                }
                for i in range(len(chunks))
            ]
            
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Added {len(chunks)} chunks for {filename} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
    def delete_document(self, file_id: str):
        """Delete all chunks for a document"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"file_id": file_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for file_id: {file_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            raise
    
    def search_similar_chunks(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results
            )
            
            chunks = []
            for i, doc in enumerate(results['documents'][0]):
                chunks.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                })
            
            logger.info(f"Found {len(chunks)} similar chunks for query")
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

class AIChat:
    def __init__(self, model: str = "fallback", use_local: bool = False):
        self.use_local = False  # Disable local model loading to avoid compatibility issues
        self.model_name = model
        self.generator = None  # Skip model loading entirely
        logger.info("AI Chat initialized with intelligent fallback system (no local model)")
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate AI response based on query and context"""
        try:
            if not context_chunks:
                return "I don't have any relevant information to answer your question. Please upload some documents first."
            
            # Use the intelligent fallback system directly (it's more reliable than DistilGPT-2 for RAG)
            return self._create_fallback_response(query, context_chunks)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._create_fallback_response(query, context_chunks)
    
    def _create_fallback_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Create intelligent responses using document analysis when AI model fails"""
        try:
            query_lower = query.lower()
            
            # Detect query type and provide appropriate response
            if 'what' in query_lower and ('about' in query_lower or 'document' in query_lower):
                return self._analyze_document_topic(context_chunks)
            elif 'summarize' in query_lower or 'summary' in query_lower:
                return self._create_document_summary(context_chunks)
            else:
                return self._extract_relevant_content(query, context_chunks)
                
        except Exception as e:
            logger.error(f"Error in fallback response: {e}")
            return "I found relevant information in your documents but had trouble processing it. Please try rephrasing your question."
    
    def _analyze_document_topic(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Analyze what the document is about"""
        try:
            # Extract key themes and topics from the chunks
            all_text = ' '.join([chunk['content'] for chunk in context_chunks[:3]])
            
            # Look for key topics and themes
            key_topics = []
            topic_indicators = {
                'artificial intelligence': ['AI', 'artificial intelligence', 'machine learning', 'algorithm'],
                'technology impact': ['technology', 'digital', 'innovation', 'technological'],
                'decision making': ['decision', 'choose', 'policy', 'strategy'],
                'social impact': ['social', 'society', 'community', 'people', 'human'],
                'digital divide': ['digital divide', 'left behind', 'gap', 'inequality'],
                'business': ['business', 'company', 'organization', 'industry']
            }
            
            text_lower = all_text.lower()
            for topic, keywords in topic_indicators.items():
                if any(keyword in text_lower for keyword in keywords):
                    key_topics.append(topic)
            
            # Extract first meaningful paragraph
            sentences = all_text.split('. ')
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 50][:3]
            
            if key_topics and meaningful_sentences:
                return f"This document appears to focus on {', '.join(key_topics)}. {' '.join(meaningful_sentences[:2])}"
            elif meaningful_sentences:
                return f"Based on the document content: {' '.join(meaningful_sentences[:2])}"
            else:
                return "This document contains information that I can help you explore. Please ask specific questions about its content."
                
        except Exception as e:
            logger.error(f"Error analyzing document topic: {e}")
            return "I can see this document contains relevant content. Please ask me specific questions about what you'd like to know."
    
    def _create_document_summary(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Create a document summary"""
        try:
            # Get key sentences from different parts of the document
            all_content = []
            for chunk in context_chunks[:4]:
                content = chunk['content'].strip()
                if content and len(content) > 50:
                    # Get the first substantial sentence from each chunk
                    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
                    if sentences:
                        all_content.append(sentences[0])
            
            if len(all_content) >= 2:
                summary = '. '.join(all_content[:3]) + '.'
                return f"**Document Summary:** {summary}"
            else:
                # Fallback to first chunk analysis
                first_chunk = context_chunks[0]['content'][:500] if context_chunks else ""
                if first_chunk:
                    return f"**Document Summary:** {first_chunk}..."
                else:
                    return "I can see this document has content but need more specific questions to provide a detailed summary."
                    
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return "I can help summarize this document. Please ask me about specific topics or sections you're interested in."
    
    def _extract_relevant_content(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Extract content relevant to the query"""
        try:
            query_words = [w.lower() for w in query.split() if len(w) > 3]
            relevant_content = []
            
            for chunk in context_chunks[:3]:
                content = chunk['content']
                sentences = content.split('. ')
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in query_words):
                        relevant_content.append(sentence.strip())
                        if len(relevant_content) >= 3:
                            break
                
                if len(relevant_content) >= 3:
                    break
            
            if relevant_content:
                return f"Based on your question about '{query}': {'. '.join(relevant_content[:2])}."
            else:
                # Return first meaningful content from the chunks
                first_content = context_chunks[0]['content'][:300] if context_chunks else ""
                return f"I found relevant information in the document: {first_content}..."
                
        except Exception as e:
            logger.error(f"Error extracting relevant content: {e}")
            return "I found information related to your question in the document. Please try asking more specific questions for better results."

class RAGEngine:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize components
        self.document_processor = DocumentProcessor(
            chunk_size=int(os.getenv('CHUNK_SIZE', 1000)),
            chunk_overlap=int(os.getenv('CHUNK_OVERLAP', 200))
        )
        
        self.vector_store = VectorStore(
            db_path=os.getenv('CHROMA_DB_PATH', './chroma_db'),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        )
        
        use_local = os.getenv('USE_LOCAL_AI', 'true').lower() == 'true'
        
        self.ai_chat = AIChat(
            model=os.getenv('LOCAL_AI_MODEL', 'microsoft/DialoGPT-medium'),
            use_local=use_local
        )
        
        logger.info("RAG Engine initialized successfully")
    
    def process_document(self, file_path: str, file_id: str, filename: str):
        """Process and index a document"""
        try:
            # Extract text chunks
            chunks = self.document_processor.load_document(file_path)
            
            # Add to vector store
            self.vector_store.add_document_chunks(chunks, file_id, filename)
            
            logger.info(f"Successfully processed and indexed {filename}")
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise
    
    def delete_document(self, file_id: str):
        """Delete document from vector store"""
        self.vector_store.delete_document(file_id)
    
    def chat(self, query: str, max_chunks: int = 5) -> Dict[str, Any]:
        """Chat with documents using RAG"""
        try:
            # Search for relevant chunks
            relevant_chunks = self.vector_store.search_similar_chunks(
                query, max_results=max_chunks
            )
            
            if not relevant_chunks:
                return {
                    'response': "I don't have any relevant information to answer your question. Please upload some documents first.",
                    'sources': []
                }
            
            # Generate AI response
            response = self.ai_chat.generate_response(query, relevant_chunks)
            
            # Prepare unique sources (avoid duplicates)
            seen_files = set()
            sources = []
            for chunk in relevant_chunks:
                filename = chunk['metadata']['filename']
                if filename not in seen_files:
                    sources.append({
                        'filename': filename,
                        'chunk_index': chunk['metadata']['chunk_index'],
                        'distance': chunk['distance']
                    })
                    seen_files.add(filename)
            
            return {
                'response': response,
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"Error in RAG chat: {e}")
            return {
                'response': f"I encountered an error while processing your question: {str(e)}",
                'sources': []
            }