"""
Demo RAG Application - No API Key Required
This version simulates AI responses without calling OpenAI API
"""
import streamlit as st
import os
import json
import hashlib
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import tempfile
import io
import re

# Basic imports that are available
import PyPDF2
from docx import Document

# Configuration
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
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = ""
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
            raise ValueError("Could not decode text file")
        except Exception as e:
            raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    def process_uploaded_file(self, uploaded_file) -> Dict:
        """Process uploaded file and return document data."""
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Extract text based on file type
            file_extension = uploaded_file.name.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(file_content)
            elif file_extension in ['docx', 'doc']:
                text = self.extract_text_from_docx(file_content)
            elif file_extension == 'txt':
                text = self.extract_text_from_txt(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
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

class DemoRAGEngine:
    """Demo RAG engine that simulates AI responses."""
    
    def analyze_query_type(self, query: str) -> str:
        """Analyze the type of query to generate appropriate responses."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['summary', 'summarize', 'overview']):
            return "summary"
        elif any(word in query_lower for word in ['main topic', 'primary topic', 'about', 'subject']):
            return "main_topic"
        elif any(word in query_lower for word in ['key points', 'important', 'highlights', 'main points']):
            return "key_points"
        else:
            return "general"
    
    def generate_summary_response(self, snippets: List[str], sources: set, query: str) -> str:
        """Generate a summary-type response."""
        return f"""## 📋 Document Summary

Based on my analysis of your uploaded documents, here's a comprehensive summary:

### Main Content:
{chr(10).join(f'• {snippet}' for snippet in snippets[:4])}

### Document Coverage:
This summary is derived from **{len(sources)}** document(s): {', '.join(f'`{src}`' for src in sources)}

### Key Insights:
The documents appear to focus on interconnected themes and provide detailed information across multiple areas of discussion.

---
*🔧 Demo Mode: This response uses keyword matching and pattern recognition. With OpenAI API, you'd get more sophisticated content analysis and better summarization.*"""
    
    def generate_topic_response(self, snippets: List[str], sources: set, query: str) -> str:
        """Generate a main topic response."""
        return f"""## 🎯 Main Topic Analysis

After analyzing your documents, I can identify the following main topics:

### Primary Focus Areas:
{chr(10).join(f'• {snippet}' for snippet in snippets[:3])}

### Topic Sources:
Found in **{len(sources)}** document(s): {', '.join(f'`{src}`' for src in sources)}

### Topic Assessment:
The documents appear to center around themes that are well-developed and provide substantial detail on the subject matter.

---
*🔧 Demo Mode: Real AI would provide deeper topic extraction and thematic analysis.*"""
    
    def generate_keypoints_response(self, snippets: List[str], sources: set, query: str) -> str:
        """Generate a key points response."""
        return f"""## 🔑 Key Points Summary

Here are the most important points I found in your documents:

### Critical Information:
{chr(10).join(f'**Point {i+1}:** {snippet}' for i, snippet in enumerate(snippets[:4]))}

### Supporting Documents:
These points are extracted from **{len(sources)}** source(s): {', '.join(f'`{src}`' for src in sources)}

### Importance Level:
All identified points appear to be central to the document's main arguments and conclusions.

---
*🔧 Demo Mode: Advanced AI would rank importance and identify relationships between key points.*"""
    
    def generate_general_response(self, snippets: List[str], sources: set, query: str) -> str:
        """Generate a general response."""
        return f"""## 💡 Analysis Results

Based on your question: *"{query}"*

### Relevant Information Found:
{chr(10).join(f'• {snippet}' for snippet in snippets[:3])}

### Source Analysis:
Information gathered from **{len(sources)}** document(s): {', '.join(f'`{src}`' for src in sources)}

### Response Quality:
The available content provides relevant context for your question, though deeper analysis would reveal additional insights.

---
*🔧 Demo Mode: Full AI capabilities would provide more contextual understanding and nuanced answers.*"""
    
    def find_relevant_chunks(self, query: str, documents: Dict, max_chunks: int = 3) -> List[Dict]:
        """Simple keyword-based search for relevant chunks."""
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for doc_id, doc_data in documents.items():
            for i, chunk in enumerate(doc_data['chunks']):
                chunk_words = set(chunk.lower().split())
                
                # Simple scoring based on word overlap
                overlap = len(query_words.intersection(chunk_words))
                if overlap > 0:
                    score = overlap / len(query_words)
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
    
    def generate_demo_response(self, query: str, relevant_chunks: List[Dict]) -> Dict:
        """Generate a demo response without calling OpenAI API."""
        try:
            if not relevant_chunks:
                answer = f"""I apologize, but I couldn't find specific information related to "{query}" in the uploaded documents. 

This is a demo response since no OpenAI API key is available. In a real scenario, I would:
1. Analyze the document content more thoroughly
2. Use advanced AI to understand context and nuance
3. Provide more accurate and detailed answers

Please ensure your documents contain relevant information about your question."""
                
                return {
                    'answer': answer,
                    'sources': [],
                    'usage': {'demo_mode': True, 'chunks_found': 0}
                }
            
            # Extract key information from chunks
            context_snippets = []
            source_files = set()
            
            for chunk in relevant_chunks:
                # Extract key sentences that might be relevant
                sentences = re.split(r'[.!?]+', chunk['chunk'])
                for sentence in sentences[:2]:  # Take first 2 sentences
                    if sentence.strip() and len(sentence.strip()) > 20:
                        context_snippets.append(sentence.strip())
                source_files.add(chunk['filename'])
            
            # Generate demo answer with better formatting
            query_type = self.analyze_query_type(query)
            
            if query_type == "summary":
                answer = self.generate_summary_response(context_snippets, source_files, query)
            elif query_type == "main_topic":
                answer = self.generate_topic_response(context_snippets, source_files, query)
            elif query_type == "key_points":
                answer = self.generate_keypoints_response(context_snippets, source_files, query)
            else:
                answer = self.generate_general_response(context_snippets, source_files, query)
            
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
                    'demo_mode': True,
                    'chunks_analyzed': len(relevant_chunks),
                    'documents_searched': len(set(chunk['filename'] for chunk in relevant_chunks))
                }
            }
        
        except Exception as e:
            return {
                'answer': f"Demo mode error: {str(e)}",
                'sources': [],
                'error': str(e)
            }

def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title="📚 Chat with Your Notes (Demo)",
        page_icon="📚",
        layout="wide"
    )
    
    # Header
    st.title("📚 Chat with Your Notes - Demo Mode")
    st.markdown("""
    **Demo Version** - This version works without OpenAI API for testing document processing.
    
    🔍 **What works:** File upload, text extraction, keyword search
    🤖 **What's simulated:** AI responses (limited to keyword matching)
    ⚡ **To enable full AI:** Add OpenAI API key to .env file
    """)
    
    # Initialize components
    processor = SimpleDocumentProcessor()
    rag_engine = DemoRAGEngine()
    
    # Sidebar for file upload and management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        # Process uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if file_key not in st.session_state.processed_files:
                    try:
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            doc_data = processor.process_uploaded_file(uploaded_file)
                            st.session_state.documents[doc_data['file_id']] = doc_data
                            st.session_state.processed_files.add(file_key)
                            st.success(f"✅ {uploaded_file.name} processed successfully!")
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        # Show uploaded documents
        if st.session_state.documents:
            st.subheader("📄 Uploaded Documents")
            for doc_id, doc_data in st.session_state.documents.items():
                with st.expander(f"📄 {doc_data['filename']}"):
                    st.write(f"**Size:** {doc_data['file_size']} bytes")
                    st.write(f"**Chunks:** {len(doc_data['chunks'])}")
                    st.write(f"**Uploaded:** {doc_data['upload_time'][:19]}")
                    
                    if st.button(f"Remove {doc_data['filename']}", key=f"remove_{doc_id}"):
                        del st.session_state.documents[doc_id]
                        st.rerun()
        
        # Clear all button
        if st.session_state.documents:
            if st.button("🗑️ Clear All Documents", type="secondary"):
                st.session_state.documents = {}
                st.session_state.processed_files = set()
                st.session_state.chat_history = []
                st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Questions About Your Documents")
        
        # Check if documents are uploaded
        if not st.session_state.documents:
            st.info("👈 Please upload some documents using the sidebar to get started!")
            return
        
        # Chat input
        user_question = st.text_input(
            "Ask a question about your documents:",
            placeholder="e.g., What is the main topic discussed in the documents?",
            key="user_input"
        )
        
        col_ask, col_clear = st.columns([1, 1])
        with col_ask:
            ask_button = st.button("🔍 Ask Question", type="primary")
        with col_clear:
            if st.button("🧹 Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Process question
        if ask_button and user_question:
            with st.spinner("🤔 Analyzing documents..."):
                # Find relevant chunks
                relevant_chunks = rag_engine.find_relevant_chunks(
                    user_question, 
                    st.session_state.documents
                )
                
                # Generate response
                response = rag_engine.generate_demo_response(user_question, relevant_chunks)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'question': user_question,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("💬 Conversation History")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                # Create a more readable question preview
                question_preview = chat['question'][:80] + "..." if len(chat['question']) > 80 else chat['question']
                
                with st.expander(f"❓ {question_preview}", expanded=(i==0)):
                    # Display question with better formatting
                    st.markdown(f"### 🔍 **Question**")
                    st.markdown(f"> {chat['question']}")
                    
                    # Display answer with better formatting
                    st.markdown("### 🤖 **Answer**")
                    
                    # Format the answer with proper line breaks and emphasis
                    formatted_answer = chat['response']['answer']
                    
                    # Add some basic formatting improvements
                    if ". " in formatted_answer:
                        # Split into sentences and format
                        sentences = formatted_answer.split(". ")
                        formatted_sentences = []
                        for sentence in sentences:
                            if sentence.strip():
                                formatted_sentences.append(sentence.strip() + ".")
                        formatted_answer = "\n\n".join(formatted_sentences)
                    
                    # Display the formatted answer in a nice container
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background-color: #f0f2f6; 
                            padding: 15px; 
                            border-radius: 10px; 
                            border-left: 4px solid #1f77b4;
                            margin: 10px 0;
                        ">
                            {formatted_answer}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Display sources with better formatting
                    if chat['response']['sources']:
                        st.markdown("### 📚 **Sources**")
                        for j, source in enumerate(chat['response']['sources']):
                            with st.container():
                                col_source1, col_source2 = st.columns([3, 1])
                                with col_source1:
                                    st.markdown(f"**📄 {source['filename']}**")
                                with col_source2:
                                    st.markdown(f"*Score: {source['score']:.2f}*")
                                
                                # Show source preview in a nice format
                                with st.expander("View source excerpt", expanded=False):
                                    st.markdown(f"""
                                    <div style="
                                        background-color: #ffffff; 
                                        padding: 10px; 
                                        border-radius: 5px; 
                                        border: 1px solid #e0e0e0;
                                        font-family: 'Courier New', monospace;
                                        font-size: 0.9em;
                                        line-height: 1.4;
                                    ">
                                        {source['chunk_preview']}
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    # Add timestamp
                    if 'timestamp' in chat:
                        timestamp = chat['timestamp'][:19].replace('T', ' ')
                        st.caption(f"⏰ Asked on {timestamp}")
    
    with col2:
        st.header("📊 Statistics")
        
        if st.session_state.documents:
            total_docs = len(st.session_state.documents)
            total_chunks = sum(len(doc['chunks']) for doc in st.session_state.documents.values())
            total_size = sum(doc['file_size'] for doc in st.session_state.documents.values())
            
            st.metric("Documents", total_docs)
            st.metric("Text Chunks", total_chunks)
            st.metric("Total Size", f"{total_size:,} bytes")
            
            st.subheader("🔧 Demo Mode Info")
            st.info("""
            **Current Capabilities:**
            ✅ Document upload & processing
            ✅ Text extraction (PDF, DOCX, TXT)
            ✅ Keyword-based search
            ✅ Basic response generation
            
            **Limitations:**
            ⚠️ Simulated AI responses
            ⚠️ Simple keyword matching
            ⚠️ No advanced reasoning
            
            **To unlock full power:**
            Add OpenAI API key to enable advanced AI analysis!
            """)
        
        if st.session_state.chat_history:
            st.subheader("💭 Recent Activity")
            for chat in st.session_state.chat_history[-3:]:
                st.text(f"Q: {chat['question'][:50]}...")
                st.text(f"Sources: {len(chat['response']['sources'])}")
                st.text("---")

if __name__ == "__main__":
    main()