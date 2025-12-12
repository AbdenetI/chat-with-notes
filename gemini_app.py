"""
RAG Application with Gemini API Support
Uses Google's Gemini API instead of OpenAI - often has better free quotas!
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
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX bytes."""
        text = ""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from TXT bytes."""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return file_content.decode(encoding).strip()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode text file with any common encoding")
        except Exception as e:
            raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    def process_uploaded_file(self, uploaded_file) -> Dict:
        """Process an uploaded file and return document data."""
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Extract text based on file type
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(file_content)
            elif file_extension == 'docx':
                text = self.extract_text_from_docx(file_content)
            elif file_extension in ['txt', 'text']:
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

class GeminiRAGEngine:
    """RAG engine using Google's Gemini API."""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key not found. Please add GEMINI_API_KEY to your .env file")
        
        try:
            # Try different model names based on available models for your API key
            model_names = [
                'models/gemini-2.5-flash',      # Latest stable
                'models/gemini-2.0-flash',      # Alternative stable
                'models/gemini-flash-latest',   # Always latest
                'models/gemini-pro-latest'      # Fallback
            ]
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    print(f"✅ Successfully initialized with model: {model_name}")
                    break
                except Exception as e:
                    print(f"❌ Failed to initialize {model_name}: {str(e)}")
                    continue
            else:
                raise ValueError("No working Gemini model found. Please check your API key and available models.")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini model: {str(e)}")
    
    def find_relevant_chunks(self, query: str, documents: Dict, max_chunks: int = 1) -> List[Dict]:
        """Simple keyword-based search for relevant chunks."""
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for doc_id, doc_data in documents.items():
            for i, chunk in enumerate(doc_data['chunks']):
                chunk_words = set(chunk.lower().split())
                
                # Calculate simple word overlap score
                overlap = len(query_words.intersection(chunk_words))
                score = overlap / len(query_words) if query_words else 0
                
                if score > 0:
                    scored_chunks.append({
                        'chunk': chunk,
                        'score': score,
                        'filename': doc_data['filename'],
                        'chunk_index': i
                    })
        
        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:max_chunks]
    
    def generate_response(self, query: str, documents: Dict) -> Dict:
        """Generate response using Gemini API."""
        try:
            # Find relevant chunks (only 1 source)
            relevant_chunks = self.find_relevant_chunks(query, documents, max_chunks=1)
            
            if not relevant_chunks:
                return {
                    'answer': "I couldn't find relevant information in your uploaded documents to answer this question. Please try rephrasing your question or upload more relevant documents.",
                    'sources': [],
                    'model': getattr(self, 'model_name', 'gemini-model')
                }
            
            # Prepare context from relevant chunks
            context = "\n\n".join([f"From {chunk['filename']}:\n{chunk['chunk']}" for chunk in relevant_chunks])
            
            # Create prompt
            prompt = f"""Based on the following document excerpts, please answer the user's question. Be accurate and provide helpful information based only on the context provided.

Document Context:
{context}

User Question: {query}

Please provide a clear, accurate answer based on the information in the documents above. If you cannot find the specific information requested, please say so clearly."""
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return {
                    'answer': "Sorry, I couldn't generate a response. Please try rephrasing your question.",
                    'sources': [],
                    'model': getattr(self, 'model_name', 'gemini-model'),
                    'error': 'Empty response from Gemini'
                }
            
            # Get the raw response text and clean it
            answer = response.text
            if answer:
                answer = answer.strip()
            
            # Prepare sources
            sources = [{
                'filename': chunk['filename'],
                'chunk_preview': chunk['chunk'][:200] + "..." if len(chunk['chunk']) > 200 else chunk['chunk'],
                'score': round(chunk['score'], 3)
            } for chunk in relevant_chunks]
            
            return {
                'answer': answer,
                'sources': sources,
                'model': getattr(self, 'model_name', 'gemini-model'),
                'usage': {
                    'input_tokens': len(prompt.split()),
                    'output_tokens': len(answer.split()),
                    'total_tokens': len(prompt.split()) + len(answer.split())
                }
            }
        
        except Exception as e:
            return {
                'answer': f"Error generating response: {str(e)}",
                'sources': [],
                'error': str(e),
                'model': getattr(self, 'model_name', 'gemini-model')
            }

def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title="📚 Chat with Your Notes (Gemini)",
        page_icon="📚",
        layout="wide"
    )
    
    # Header
    st.title("📚 Chat with Your Notes")
    st.markdown("### 🤖 **Powered by Google Gemini API**")
    
    # Check API key
    if not GEMINI_API_KEY:
        st.error("🚨 **Gemini API Key Required!**")
        st.markdown("""
        **To use this app:**
        1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Add it to your `.env` file: `GEMINI_API_KEY=your_key_here`
        3. Restart the application
        
        **Why Gemini?** 
        - More generous free tier than OpenAI
        - High-quality responses
        - Better quota limits
        """)
        return
    
    # Sidebar for file management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload PDF, DOCX, or TXT files to chat with them"
        )
        
        # Process uploaded files
        processor = SimpleDocumentProcessor()
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if file_key not in st.session_state.processed_files:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        try:
                            # Reset file pointer
                            uploaded_file.seek(0)
                            
                            # Process the file
                            doc_data = processor.process_uploaded_file(uploaded_file)
                            st.session_state.documents[doc_data['file_id']] = doc_data
                            st.session_state.processed_files.add(file_key)
                            
                            st.success(f"✅ Processed {uploaded_file.name}")
                            
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        # Display loaded documents
        if st.session_state.documents:
            st.subheader("📄 Loaded Documents")
            for doc_id, doc_data in st.session_state.documents.items():
                with st.expander(f"📄 {doc_data['filename']}"):
                    st.write(f"**Size:** {doc_data['file_size']:,} bytes")
                    st.write(f"**Chunks:** {len(doc_data['chunks'])}")
                    st.write(f"**Uploaded:** {doc_data['upload_time'][:16]}")
                    
                    # Show preview
                    preview_text = doc_data['text'][:300] + "..." if len(doc_data['text']) > 300 else doc_data['text']
                    st.text_area("Preview:", preview_text, height=100, disabled=True)
                    
                    if st.button(f"🗑️ Remove", key=f"remove_{doc_id}"):
                        del st.session_state.documents[doc_id]
                        # Remove from processed files
                        keys_to_remove = [k for k in st.session_state.processed_files if doc_data['filename'] in k]
                        for key in keys_to_remove:
                            st.session_state.processed_files.discard(key)
                        st.rerun()
        
        # Clear all button
        if st.session_state.documents and st.button("🗑️ Clear All Documents"):
            st.session_state.documents = {}
            st.session_state.processed_files = set()
            st.session_state.chat_history = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("📝 Conversation History")
            for i, (question, response_data) in enumerate(st.session_state.chat_history):
                with st.expander(f"Q{i+1}: {question[:50]}..." if len(question) > 50 else f"Q{i+1}: {question}"):
                    st.markdown("**Question:**")
                    st.write(question)
                    
                    st.markdown("**Answer:**")
                    # Display answer with proper formatting
                    answer = response_data['answer']
                    if answer:
                        # Use text_area for better formatting, or just write normally
                        st.text(answer)
                    
                    if response_data.get('sources'):
                        st.markdown("**Sources:**")
                        for j, source in enumerate(response_data['sources']):
                            st.write(f"- **{source['filename']}** (Relevance: {source['score']})")
                    
                    if response_data.get('usage'):
                        st.caption(f"Model: {response_data.get('model', 'gemini-1.5-flash')} | Tokens: {response_data['usage']['total_tokens']}")
        
        # Query input
        if st.session_state.documents:
            st.subheader("🤖 Ask a Question")
            
            # Sample questions
            st.write("**💡 Try these sample questions:**")
            sample_questions = [
                "What is the main topic of this document?",
                "Can you summarize the key points?",
                "What are the most important details?",
                "What does this document discuss?",
                "Give me an overview of the content."
            ]
            
            cols = st.columns(2)
            for i, question in enumerate(sample_questions):
                with cols[i % 2]:
                    if st.button(question, key=f"sample_{i}"):
                        # Process the sample question
                        with st.spinner("🤖 Gemini is analyzing your documents..."):
                            try:
                                rag_engine = GeminiRAGEngine()
                                response_data = rag_engine.generate_response(question, st.session_state.documents)
                                st.session_state.chat_history.append((question, response_data))
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            # Custom question input
            query = st.text_input("Or ask your own question:", placeholder="What would you like to know about your documents?")
            
            col_ask, col_clear = st.columns([3, 1])
            
            with col_ask:
                if st.button("🤖 Ask Gemini", disabled=not query.strip()):
                    if query.strip():
                        with st.spinner("🤖 Gemini is analyzing your documents..."):
                            try:
                                rag_engine = GeminiRAGEngine()
                                response_data = rag_engine.generate_response(query, st.session_state.documents)
                                st.session_state.chat_history.append((query, response_data))
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            with col_clear:
                if st.button("🗑️ Clear Chat") and st.session_state.chat_history:
                    st.session_state.chat_history = []
                    st.rerun()
        
        else:
            st.info("👈 **Upload documents using the sidebar to start chatting!**")
            st.write("**📚 How to get started:**")
            st.write("1. 🔑 **Get Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)")
            st.write("2. 📁 **Upload** PDF, DOCX, or TXT files") 
            st.write("3. 💬 **Ask** questions about your documents")
            st.write("4. 🤖 **Get** AI-powered responses from Gemini")
    
    with col2:
        st.header("📊 System Status")
        
        # Document statistics
        if st.session_state.documents:
            st.metric("Documents Loaded", len(st.session_state.documents))
            
            total_chunks = sum(len(doc['chunks']) for doc in st.session_state.documents.values())
            st.metric("Text Chunks", total_chunks)
            
            total_size = sum(doc['file_size'] for doc in st.session_state.documents.values())
            st.metric("Total Size", f"{total_size:,} bytes")
            
            st.metric("Questions Asked", len(st.session_state.chat_history))
        else:
            st.metric("Documents Loaded", 0)
            st.metric("Text Chunks", 0)
            st.metric("Total Size", "0 bytes")
            st.metric("Questions Asked", 0)
        
        # API info
        st.subheader("🤖 AI Model Info")
        if GEMINI_API_KEY:
            st.write("✅ **Model:** Auto-detected Gemini")
            st.write("✅ **Provider:** Google AI")
            st.write("✅ **API Key:** Configured")
        else:
            st.write("❌ **API Key:** Missing")
        
        st.subheader("🔧 Features")
        st.write("✅ Document upload & processing")
        st.write("✅ Text extraction (PDF, DOCX, TXT)")
        st.write("✅ Content chunking")
        st.write("✅ Keyword-based search")
        st.write("✅ Real AI responses (Gemini)")
        st.write("✅ Source citations")
        st.write("✅ Chat history")
        
        st.subheader("💰 Why Gemini?")
        st.write("🆓 **Generous free tier**")
        st.write("⚡ **Fast responses**")
        st.write("🎯 **High quality answers**") 
        st.write("💸 **Better quota limits**")

if __name__ == "__main__":
    main()