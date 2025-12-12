"""
Alternative RAG Application with improved file handling
Fixes the 403 error by using a different file upload approach.
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
import io

# Basic imports that are available
import PyPDF2
from docx import Document
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client (will be created when needed)
client = None
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = set()

class SimpleDocumentProcessor:
    """Basic document processing without complex dependencies."""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF bytes."""
        text = ""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {e}")
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from TXT bytes."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    return file_content.decode(encoding).strip()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode text file")
        except Exception as e:
            raise ValueError(f"Error reading TXT: {e}")
    
    def process_file(self, uploaded_file) -> Dict:
        """Process uploaded file and return text content."""
        try:
            # Get file content as bytes
            file_content = uploaded_file.getvalue()
            file_extension = Path(uploaded_file.name).suffix.lower()
            
            # Extract text based on file type
            if file_extension == '.pdf':
                text = self.extract_text_from_pdf(file_content)
            elif file_extension == '.docx':
                text = self.extract_text_from_docx(file_content)
            elif file_extension == '.txt':
                text = self.extract_text_from_txt(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Validate extracted text
            if not text.strip():
                raise ValueError("No text content found in the file")
            
            # Generate file ID
            file_id = hashlib.md5(file_content).hexdigest()[:12]
            
            # Split text into chunks
            chunks = self.split_text_into_chunks(text, chunk_size=1000)
            
            return {
                'file_id': file_id,
                'filename': uploaded_file.name,
                'text': text,
                'chunks': chunks,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(file_content)
            }
        
        except Exception as e:
            raise ValueError(f"Processing failed: {str(e)}")
    
    @staticmethod
    def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []
        
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
            raise ValueError("OpenAI API key not found")
        global client
        if client is None:
            client = OpenAI(api_key=OPENAI_API_KEY)
    
    def find_relevant_chunks(self, query: str, documents: Dict, max_chunks: int = 3) -> List[Dict]:
        """Simple keyword-based search for relevant chunks."""
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for doc_id, doc_data in documents.items():
            for i, chunk in enumerate(doc_data['chunks']):
                chunk_words = set(chunk.lower().split())
                # Score based on word overlap
                score = len(query_words.intersection(chunk_words)) / len(query_words) if query_words else 0
                
                if score > 0.1:  # Lower threshold for better results
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
            prompt = f"""Based on the following document excerpts, please answer the user's question. If the information is not sufficient, please say so clearly.

Context from uploaded documents:
{context}

Question: {query}

Please provide a helpful and accurate answer based only on the information in the context above:"""
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided document context. Be accurate and cite your sources when possible."},
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
                'score': round(chunk['score'], 3)
            } for chunk in relevant_chunks]
            
            return {
                'answer': answer,
                'sources': sources,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
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
        page_title="📚 Chat with Your Notes",
        page_icon="📚",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .upload-section {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border: 2px dashed #dee2e6;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .success-message {
            padding: 0.5rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            color: #155724;
            margin: 0.5rem 0;
        }
        
        .error-message {
            padding: 0.5rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            color: #721c24;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Chat with Your Notes</h1>
        <p>Upload documents and have intelligent conversations with AI</p>
        <p><em>Powered by OpenAI GPT-3.5 Turbo</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for API key
    if not OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not found!")
        st.info("""
        **Setup Required:**
        1. Edit the `.env` file in the project root
        2. Add your OpenAI API key: `OPENAI_API_KEY=your-api-key-here`
        3. Get your key from: https://platform.openai.com/api-keys
        4. Restart the application
        """)
        st.stop()
    
    # Initialize components
    try:
        processor = SimpleDocumentProcessor()
        rag_engine = SimpleRAGEngine()
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()
    
    # Sidebar for document management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # Upload section with better styling
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.write("**📤 Upload Documents**")
        st.write("Drag and drop files or click to browse")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="📝 PDF, DOCX, TXT files • Max 50MB each",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process uploaded files
        if uploaded_files:
            st.write("**Processing Files:**")
            
            for uploaded_file in uploaded_files:
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if file_key not in st.session_state.processed_files:
                    # File size check
                    if uploaded_file.size > 50 * 1024 * 1024:
                        st.markdown(f'<div class="error-message">❌ {uploaded_file.name} is too large (max 50MB)</div>', unsafe_allow_html=True)
                        continue
                    
                    with st.spinner(f"⚙️ Processing {uploaded_file.name}..."):
                        try:
                            doc_data = processor.process_file(uploaded_file)
                            st.session_state.documents[doc_data['file_id']] = doc_data
                            st.session_state.processed_files.add(file_key)
                            
                            st.markdown(f'<div class="success-message">✅ {uploaded_file.name} processed ({len(doc_data["chunks"])} chunks)</div>', unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.markdown(f'<div class="error-message">❌ Error processing {uploaded_file.name}: {str(e)}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Document list
        st.subheader("📋 Uploaded Documents")
        if st.session_state.documents:
            for doc_id, doc_data in st.session_state.documents.items():
                with st.expander(f"📄 {doc_data['filename']}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Chunks:** {len(doc_data['chunks'])}")
                        st.write(f"**Size:** {doc_data['file_size']:,} bytes")
                        st.write(f"**Uploaded:** {doc_data['upload_time'][:19].replace('T', ' ')}")
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc_id}", help="Delete document"):
                            del st.session_state.documents[doc_id]
                            # Remove from processed files
                            st.session_state.processed_files = {
                                f for f in st.session_state.processed_files 
                                if not f.startswith(doc_data['filename'])
                            }
                            st.rerun()
        else:
            st.info("📁 No documents uploaded yet")
        
        st.markdown("---")
        
        # Statistics
        st.subheader("📊 Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📁 Documents", len(st.session_state.documents))
            st.metric("💬 Messages", len(st.session_state.chat_history))
        
        with col2:
            total_chunks = sum(len(doc['chunks']) for doc in st.session_state.documents.values())
            st.metric("📄 Text Chunks", total_chunks)
            total_size = sum(doc['file_size'] for doc in st.session_state.documents.values())
            st.metric("💾 Total Size", f"{total_size/1024:.1f} KB")
        
        st.markdown("---")
        
        # Clear buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", help="Clear chat history"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All", help="Clear everything", type="secondary"):
                st.session_state.documents = {}
                st.session_state.chat_history = []
                st.session_state.processed_files = set()
                st.rerun()
    
    # Main chat interface
    st.header("💬 Chat with Your Documents")
    
    # Instructions if no documents
    if not st.session_state.documents:
        st.info("""
        **🚀 Get Started:**
        1. **Upload documents** using the file uploader in the sidebar
        2. **Wait for processing** (you'll see success messages)
        3. **Ask questions** about your documents in the chat below
        
        **💡 Example questions:**
        - "What are the main topics covered?"
        - "Can you summarize the key points?"
        - "What does it say about [specific topic]?"
        """)
    
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
                            st.markdown(f"**📄 Source {i}:** `{source['filename']}`")
                            st.markdown(f"*Relevance: {source['score']:.1%}*")
                            st.markdown(f"```\n{source['chunk_preview']}\n```")
                            st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("💭 Ask a question about your documents..."):
        # Check if documents are uploaded
        if not st.session_state.documents:
            st.warning("⚠️ Please upload some documents first!")
            st.stop()
        
        # Add user message
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = rag_engine.generate_response(prompt, st.session_state.documents)
                
                st.write(response['answer'])
                
                # Show sources
                if response.get('sources'):
                    with st.expander("📚 Sources", expanded=False):
                        for i, source in enumerate(response['sources'], 1):
                            st.markdown(f"**📄 Source {i}:** `{source['filename']}`")
                            st.markdown(f"*Relevance: {source['score']:.1%}*")
                            st.markdown(f"```\n{source['chunk_preview']}\n```")
                            if i < len(response['sources']):
                                st.markdown("---")
                
                # Show usage info
                if 'usage' in response:
                    usage = response['usage']
                    st.caption(f"💰 Tokens: {usage.get('total_tokens', 'N/A')} | Cost: ~${usage.get('total_tokens', 0) * 0.000002:.4f}")
        
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