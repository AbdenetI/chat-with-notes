"""
Streamlit web interface for the Chat with Notes RAG application.
"""
import streamlit as st
import os
from datetime import datetime
import json

# Import our application components
from src.app import ChatWithNotesApp
from src.config import (
    PAGE_TITLE, PAGE_ICON, LAYOUT, 
    SUPPORTED_FILE_TYPES, MAX_FILE_SIZE
)

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background-color: #e8f4f8;
        border-left-color: #00acc1;
    }
    
    .source-box {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
        font-size: 0.9em;
    }
    
    .stats-metric {
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'app' not in st.session_state:
    try:
        st.session_state.app = ChatWithNotesApp()
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        st.info("Please make sure your OpenAI API key is set in the .env file")
        st.stop()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}

def main():
    """Main application interface."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 Chat with Your Notes</h1>
        <p>Upload your documents and have intelligent conversations with your content using AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for file management and settings
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload section
        uploaded_files = st.file_uploader(
            "Upload your documents",
            type=[ext.replace('.', '') for ext in SUPPORTED_FILE_TYPES],
            accept_multiple_files=True,
            help=f"Supported formats: {', '.join(SUPPORTED_FILE_TYPES)}\nMax file size: {MAX_FILE_SIZE/1024/1024:.1f}MB"
        )
        
        # Process uploaded files
        if uploaded_files:
            process_uploaded_files(uploaded_files)
        
        st.markdown("---")
        
        # Document list and management
        show_document_management()
        
        st.markdown("---")
        
        # Application statistics
        show_statistics()
        
        st.markdown("---")
        
        # Settings and actions
        show_settings_and_actions()
    
    # Main chat interface
    show_chat_interface()

def process_uploaded_files(uploaded_files):
    """Process and index uploaded files."""
    for uploaded_file in uploaded_files:
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if file_key not in st.session_state.uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Process the file
                    result = st.session_state.app.upload_and_process_document(
                        uploaded_file, uploaded_file.name
                    )
                    
                    if result['success']:
                        st.session_state.uploaded_files[file_key] = result
                        st.success(f"✅ Successfully processed '{uploaded_file.name}' ({result['chunk_count']} chunks)")
                        
                        # Add to chat messages
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"Document '{uploaded_file.name}' has been uploaded and processed. You can now ask questions about it!",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        st.error(f"❌ Failed to process '{uploaded_file.name}': {result['message']}")
                        
                except Exception as e:
                    st.error(f"❌ Error processing '{uploaded_file.name}': {str(e)}")

def show_document_management():
    """Show document list and management options."""
    st.subheader("📋 Uploaded Documents")
    
    # Get document list
    documents = st.session_state.app.get_document_list()
    
    if documents:
        for file_id, doc_info in documents.items():
            with st.expander(f"📄 {doc_info['filename']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Chunks:** {doc_info['chunk_count']}")
                    if doc_info.get('file_size'):
                        st.write(f"**Size:** {doc_info['file_size'] / 1024:.1f} KB")
                    if doc_info.get('upload_timestamp'):
                        st.write(f"**Uploaded:** {doc_info['upload_timestamp'][:19].replace('T', ' ')}")
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{file_id}"):
                        with st.spinner("Deleting..."):
                            result = st.session_state.app.delete_document(file_id)
                            if result['success']:
                                st.success("Document deleted!")
                                st.rerun()
                            else:
                                st.error(result['message'])
                    
                    if st.button(f"📝 Summary", key=f"summary_{file_id}"):
                        with st.spinner("Generating summary..."):
                            summary = st.session_state.app.summarize_document(file_id)
                            if 'error' not in summary:
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"**Summary of {doc_info['filename']}:**\n\n{summary['answer']}",
                                    "timestamp": datetime.now().isoformat(),
                                    "sources": summary.get('sources', [])
                                })
                                st.rerun()
    else:
        st.info("No documents uploaded yet. Upload some files to get started!")

def show_statistics():
    """Show application statistics."""
    st.subheader("📊 Statistics")
    
    try:
        stats = st.session_state.app.get_app_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📁 Files", stats.get('total_files', 0))
        with col2:
            st.metric("📄 Chunks", stats.get('total_chunks', 0))
        
        st.metric("💬 Conversations", stats.get('conversation_turns', 0))
        
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

def show_settings_and_actions():
    """Show settings and action buttons."""
    st.subheader("⚙️ Settings")
    
    # Clear conversation history
    if st.button("🗑️ Clear Chat History"):
        st.session_state.app.clear_conversation_history()
        st.session_state.messages = []
        st.success("Chat history cleared!")
        st.rerun()
    
    # Clear all documents
    if st.button("🗑️ Clear All Documents", type="secondary"):
        if st.session_state.get('confirm_clear', False):
            result = st.session_state.app.clear_all_documents()
            if result['success']:
                st.session_state.uploaded_files = {}
                st.session_state.messages = []
                st.success("All documents cleared!")
                st.rerun()
            else:
                st.error(result['message'])
            st.session_state.confirm_clear = False
        else:
            st.session_state.confirm_clear = True
            st.warning("Click again to confirm deletion of all documents")
    
    # Export conversation
    if st.button("📥 Export Chat"):
        export_conversation()

def show_chat_interface():
    """Show the main chat interface."""
    st.header("💬 Chat with Your Documents")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.write(message["content"])
                    
                    # Show sources if available
                    if "sources" in message and message["sources"]:
                        with st.expander("📚 Sources", expanded=False):
                            for i, source in enumerate(message["sources"], 1):
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>Source {i}:</strong> {source['filename']} (Section {source['chunk_index']})<br>
                                    <em>{source['preview']}</em>
                                </div>
                                """, unsafe_allow_html=True)
            elif message["role"] == "system":
                st.info(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate response
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.app.ask_question(prompt)
                
                if 'error' in response:
                    st.error(f"Error: {response['error']}")
                else:
                    st.write(response['answer'])
                    
                    # Show sources
                    if response.get('sources'):
                        with st.expander("📚 Sources", expanded=False):
                            for i, source in enumerate(response['sources'], 1):
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>Source {i}:</strong> {source['filename']} (Section {source['chunk_index']})<br>
                                    <em>{source['preview']}</em>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Show token usage if available
                    if 'token_usage' in response and response['token_usage']:
                        usage = response['token_usage']
                        st.caption(f"Tokens used: {usage.get('total_tokens', 'N/A')} | Cost: ${usage.get('total_cost', 0):.4f}")
        
        # Add assistant response to messages
        st.session_state.messages.append({
            "role": "assistant",
            "content": response['answer'],
            "timestamp": datetime.now().isoformat(),
            "sources": response.get('sources', []),
            "token_usage": response.get('token_usage', {})
        })
        
        st.rerun()

def export_conversation():
    """Export conversation history as JSON."""
    try:
        conversation_data = {
            "export_timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "statistics": st.session_state.app.get_app_statistics()
        }
        
        json_str = json.dumps(conversation_data, indent=2)
        st.download_button(
            label="📥 Download Chat History",
            data=json_str,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"Error exporting conversation: {e}")

# Initialize and run the app
if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found!")
        st.info("""
        Please set your OpenAI API key:
        1. Create a `.env` file in the project root
        2. Add: `OPENAI_API_KEY=your-api-key-here`
        3. Restart the application
        """)
        st.stop()
    
    main()