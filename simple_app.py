"""
Simple RAG Application - Basic Version
A simplified version that works without ChromaDB or complex LangChain dependencies.
"""
import streamlit as st
import os
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import tempfile

# Basic imports that are available
import PyPDF2
from docx import Document
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Simple document storage (in-memory for now)
if 'documents' not in st.session_state:
    st.session_state.documents = {}

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

class SimpleDocumentProcessor:
    """Basic document processing without complex dependencies."""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            st.error(f"Error reading TXT: {e}")
            return ""
    
    def process_file(self, uploaded_file) -> Dict:
        """Process uploaded file and return text content."""
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        
        try:
            file_extension = Path(uploaded_file.name).suffix.lower()
            
            if file_extension == '.pdf':
                text = self.extract_text_from_pdf(temp_path)
            elif file_extension == '.docx':
                text = self.extract_text_from_docx(temp_path)
            elif file_extension == '.txt':
                text = self.extract_text_from_txt(temp_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Generate file ID
            file_id = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:12]
            
            # Split text into chunks (simple approach)
            chunks = self.split_text_into_chunks(text, chunk_size=1000)
            
            return {
                'file_id': file_id,
                'filename': uploaded_file.name,
                'text': text,
                'chunks': chunks,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(uploaded_file.getvalue())
            }
        
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    @staticmethod
    def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence or word boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_space = chunk.rfind(' ')
                
                if last_period > len(chunk) * 0.8:
                    end = start + last_period + 1
                elif last_space > len(chunk) * 0.8:
                    end = start + last_space
                
                chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            start = end - overlap
        
        return chunks

class SimpleRAGEngine:
    """Basic RAG engine using OpenAI API directly."""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        # Set OpenAI API key
        openai.api_key = OPENAI_API_KEY
    
    def find_relevant_chunks(self, query: str, documents: Dict, max_chunks: int = 3) -> List[Dict]:
        """Simple keyword-based search for relevant chunks."""
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for doc_id, doc_data in documents.items():
            for i, chunk in enumerate(doc_data['chunks']):
                chunk_words = set(chunk.lower().split())
                # Simple scoring based on word overlap
                score = len(query_words.intersection(chunk_words)) / len(query_words) if query_words else 0
                
                if score > 0:
                    scored_chunks.append({
                        'chunk': chunk,
                        'score': score,
                        'filename': doc_data['filename'],
                        'doc_id': doc_id,
                        'chunk_index': i
                    })
        
        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:max_chunks]
    
    def generate_response(self, query: str, documents: Dict) -> Dict:
        """Generate response using OpenAI with retrieved context."""
        try:
            # Find relevant chunks
            relevant_chunks = self.find_relevant_chunks(query, documents)
            
            if not relevant_chunks:
                return {
                    'answer': "I couldn't find relevant information in your documents to answer this question. Please make sure you have uploaded documents or try rephrasing your question.",
                    'sources': []
                }
            
            # Prepare context
            context = "\n\n".join([f"From {chunk['filename']}:\n{chunk['chunk']}" for chunk in relevant_chunks])
            
            # Create prompt
            prompt = f"""Based on the following document excerpts, please answer the user's question. If the information is not sufficient to answer the question, please say so.

Context:
{context}

Question: {query}

Answer:"""
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided document context. Be accurate and cite your sources."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Prepare sources
            sources = [{
                'filename': chunk['filename'],
                'chunk_preview': chunk['chunk'][:200] + "..." if len(chunk['chunk']) > 200 else chunk['chunk'],
                'score': chunk['score']
            } for chunk in relevant_chunks]
            
            return {
                'answer': answer,
                'sources': sources,
                'usage': response.usage
            }
        
        except Exception as e:
            return {
                'answer': f"Error generating response: {str(e)}",
                'sources': [],
                'error': str(e)
            }

def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title="📚 Chat with Your Notes - Simple Version",
        page_icon="📚",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 1rem;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Chat with Your Notes</h1>
        <p>Simple RAG Application - Upload documents and ask questions!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for API key
    if not OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not found!")
        st.info("""
        Please set your OpenAI API key:
        1. Edit the `.env` file in the project root
        2. Add: `OPENAI_API_KEY=your-api-key-here`
        3. Restart the application
        """)
        st.stop()
    
    # Configure Streamlit to handle file uploads properly
    st.set_option('client.showErrorDetails', False)
    st.set_option('server.maxUploadSize', 50)
    
    # Initialize components
    processor = SimpleDocumentProcessor()
    rag_engine = SimpleRAGEngine()
    
    # Sidebar for document management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload with better error handling
        st.write("**Upload Documents:**")
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT (max 50MB each)",
            key="file_uploader"
        )
        
        # Process uploaded files with better error handling
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if file_key not in st.session_state.get('processed_files', set()):
                    # Check file size
                    if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
                        st.error(f"❌ File {uploaded_file.name} is too large. Maximum size is 50MB.")
                        continue
                    
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        try:
                            # Reset file pointer to beginning
                            uploaded_file.seek(0)
                            
                            doc_data = processor.process_file(uploaded_file)
                            st.session_state.documents[doc_data['file_id']] = doc_data
                            
                            # Track processed files
                            if 'processed_files' not in st.session_state:
                                st.session_state.processed_files = set()
                            st.session_state.processed_files.add(file_key)
                            
                            st.success(f"✅ Processed {uploaded_file.name} ({len(doc_data['chunks'])} chunks)")
                            
                            # Clear the uploader to prevent re-processing
                            time.sleep(1)
                            
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                            st.write("Please try uploading the file again or check if it's corrupted.")
        
        st.markdown("---")
        
        # Document list
        st.subheader("📋 Uploaded Documents")
        if st.session_state.documents:
            for doc_id, doc_data in st.session_state.documents.items():
                with st.expander(f"📄 {doc_data['filename']}", expanded=False):
                    st.write(f"**Chunks:** {len(doc_data['chunks'])}")
                    st.write(f"**Size:** {doc_data['file_size']} bytes")
                    st.write(f"**Uploaded:** {doc_data['upload_time'][:19]}")
                    
                    if st.button(f"🗑️ Delete", key=f"delete_{doc_id}"):
                        del st.session_state.documents[doc_id]
                        st.rerun()
        else:
            st.info("No documents uploaded yet.")
        
        st.markdown("---")
        
        # Statistics
        st.subheader("📊 Statistics")
        st.metric("📁 Documents", len(st.session_state.documents))
        total_chunks = sum(len(doc['chunks']) for doc in st.session_state.documents.values())
        st.metric("📄 Text Chunks", total_chunks)
        st.metric("💬 Chat Messages", len(st.session_state.chat_history))
        
        # Clear all button
        if st.button("🗑️ Clear All", type="secondary"):
            st.session_state.documents = {}
            st.session_state.chat_history = []
            st.session_state.processed_files = set()
            st.rerun()
    
    # Main chat interface
    st.header("💬 Chat with Your Documents")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
                
                # Show sources if available
                if 'sources' in message and message['sources']:
                    with st.expander("📚 Sources", expanded=False):
                        for i, source in enumerate(message['sources'], 1):
                            st.markdown(f"**Source {i}:** {source['filename']}")
                            st.markdown(f"*{source['chunk_preview']}*")
                            st.markdown(f"*Relevance Score: {source['score']:.2f}*")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Check if documents are uploaded
        if not st.session_state.documents:
            st.warning("Please upload some documents first!")
            st.stop()
        
        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = rag_engine.generate_response(prompt, st.session_state.documents)
                
                st.write(response['answer'])
                
                # Show sources
                if response.get('sources'):
                    with st.expander("📚 Sources", expanded=False):
                        for i, source in enumerate(response['sources'], 1):
                            st.markdown(f"**Source {i}:** {source['filename']}")
                            st.markdown(f"*{source['chunk_preview']}*")
                            st.markdown(f"*Relevance Score: {source['score']:.2f}*")
                
                # Show token usage if available
                if 'usage' in response:
                    usage = response['usage']
                    st.caption(f"Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response['answer'],
            'sources': response.get('sources', []),
            'timestamp': datetime.now().isoformat()
        })
        
        st.rerun()

if __name__ == "__main__":
    main()