# 📚 Chat with Your Notes - RAG Application

A powerful **Retrieval Augmented Generation (RAG)** system that lets you upload documents and have intelligent conversations with your content using AI. Built with LangChain, ChromaDB, OpenAI, and Streamlit.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-Latest-green)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red)

## 🚀 Features

### Core RAG Functionality
- **📄 Multi-format Support**: Upload PDF, DOCX, and TXT files
- **🔍 Intelligent Chunking**: Smart text splitting for optimal embedding
- **🧠 Vector Search**: ChromaDB-powered similarity search
- **💬 Contextual Chat**: AI answers based on your documents
- **📊 Source Attribution**: See exactly which documents inform each answer

### Advanced Features
- **🔄 Conversation Memory**: Maintains context across chat sessions
- **📝 Document Summaries**: Generate AI summaries of uploaded files
- **🗂️ Document Management**: Upload, view, and delete documents easily
- **📈 Usage Analytics**: Track tokens, costs, and performance metrics
- **💾 Export Conversations**: Download chat history as JSON

### User Experience
- **🎨 Modern UI**: Clean, responsive Streamlit interface
- **⚡ Real-time Processing**: Live document processing with progress indicators
- **📱 Mobile Friendly**: Responsive design works on all devices
- **🔒 Privacy First**: All processing happens locally (except OpenAI API calls)

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python 3.8+ | Core application logic |
| **RAG Framework** | LangChain | Document processing and AI orchestration |
| **Vector Database** | ChromaDB | Embedding storage and similarity search |
| **LLM Provider** | OpenAI GPT-3.5/4 | Text generation and embeddings |
| **Web Interface** | Streamlit | Interactive user interface |
| **Document Processing** | PyPDF2, python-docx | Multi-format document parsing |

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **OpenAI API Key** (get one at [platform.openai.com](https://platform.openai.com/api-keys))
- **Git** (for cloning the repository)

## 🚦 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd chat-with-notes
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv rag_env

# Activate it
# On Windows:
rag_env\\Scripts\\activate
# On macOS/Linux:
source rag_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### 5. Run the Application
```bash
streamlit run streamlit_app.py
```

### 6. Open in Browser
The application will open automatically at `http://localhost:8501`

## 📖 How to Use

### Step 1: Upload Documents
1. Use the **sidebar file uploader** to select your documents
2. Supported formats: PDF, DOCX, TXT (up to 50MB each)
3. Files are automatically processed and indexed

### Step 2: Start Chatting
1. Type your question in the **chat input** at the bottom
2. The AI will search your documents for relevant information
3. Get intelligent answers with **source references**

### Step 3: Manage Your Knowledge Base
- **View uploaded documents** in the sidebar
- **Generate document summaries** with one click
- **Delete individual documents** or clear everything
- **Export conversation history** for later reference

## 🏗️ Project Structure

```
chat-with-notes/
├── 📁 src/                          # Core application modules
│   ├── 📄 __init__.py               # Package initialization
│   ├── 📄 config.py                 # Configuration settings
│   ├── 📄 document_processor.py     # Document upload & processing
│   ├── 📄 vector_store.py           # ChromaDB vector database
│   ├── 📄 rag_engine.py             # RAG logic & LLM integration
│   └── 📄 app.py                    # Main application class
├── 📁 uploads/                      # Temporary file storage
├── 📁 vector_db/                    # ChromaDB storage (auto-created)
├── 📄 streamlit_app.py              # Streamlit web interface
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env.example                  # Environment template
├── 📄 .gitignore                    # Git ignore rules
└── 📄 README.md                     # This file
```

## ⚙️ Configuration Options

Customize your application by editing the `.env` file:

```bash
# Model Settings
CHAT_MODEL=gpt-3.5-turbo              # Or gpt-4 for better quality
EMBEDDING_MODEL=text-embedding-3-small # OpenAI embedding model
MAX_TOKENS=2000                       # Response length limit
TEMPERATURE=0.1                       # Creativity vs consistency

# Document Processing
CHUNK_SIZE=1000                       # Text chunk size for embeddings
CHUNK_OVERLAP=200                     # Overlap between chunks
MAX_FILE_SIZE=52428800               # 50MB file size limit

# Retrieval Settings
SIMILARITY_THRESHOLD=0.7              # Minimum relevance score
MAX_RETRIEVED_DOCS=4                 # Documents per query
```

## 🔧 Advanced Usage

### Custom Document Processing
```python
from src.document_processor import DocumentProcessor

processor = DocumentProcessor()
documents = processor.process_uploaded_file(file, filename)
```

### Direct RAG Engine Access
```python
from src.rag_engine import RAGEngine
from src.vector_store import VectorStore

vector_store = VectorStore()
rag_engine = RAGEngine(vector_store)
response = rag_engine.ask_question("Your question here")
```

### Programmatic API Usage
```python
from src.app import ChatWithNotesApp

app = ChatWithNotesApp()
result = app.upload_and_process_document(file, filename)
answer = app.ask_question("What is the main topic?")
```

## 🛡️ Security & Privacy

- **Local Processing**: Documents are processed locally on your machine
- **API Calls**: Only text chunks are sent to OpenAI for embeddings and generation
- **Data Retention**: OpenAI doesn't store data from API calls (as per their policy)
- **Environment Variables**: API keys are stored securely in `.env` files
- **Git Safety**: Sensitive files are automatically excluded via `.gitignore`

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're in the correct directory and virtual environment is activated
pip install -r requirements.txt
```

**2. OpenAI API Key Issues**
```bash
# Verify your .env file contains the correct API key
cat .env | grep OPENAI_API_KEY
```

**3. ChromaDB Errors**
```bash
# Clear the vector database if corrupted
rm -rf vector_db/
# Restart the application
```

**4. File Upload Issues**
- Check file size (max 50MB)
- Verify file format (PDF, DOCX, TXT only)
- Ensure file isn't corrupted or password-protected

### Performance Optimization

**For Large Documents:**
- Reduce `CHUNK_SIZE` in `.env` for faster processing
- Increase `MAX_RETRIEVED_DOCS` for more comprehensive answers

**For Cost Optimization:**
- Use `gpt-3.5-turbo` instead of `gpt-4`
- Reduce `MAX_TOKENS` for shorter responses
- Set higher `SIMILARITY_THRESHOLD` to retrieve fewer chunks

## 💡 Tips for Best Results

### Document Preparation
- **Clean Text**: Remove headers, footers, and unnecessary formatting
- **Clear Structure**: Well-organized documents work better
- **Relevant Content**: Upload documents related to your questions

### Asking Questions
- **Be Specific**: Detailed questions get better answers
- **Use Keywords**: Include terms likely to appear in your documents
- **Follow Up**: Ask clarifying questions to dive deeper

### Managing Conversations
- **Clear History**: Start fresh for unrelated topics
- **Export Important Chats**: Save valuable conversations
- **Review Sources**: Check which documents inform answers

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit**: `git commit -m 'Add amazing feature'`
5. **Push**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest

# Format code
black src/ streamlit_app.py

# Lint code
flake8 src/ streamlit_app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[LangChain](https://langchain.com/)** for the RAG framework
- **[ChromaDB](https://www.trychroma.com/)** for vector database
- **[OpenAI](https://openai.com/)** for LLM and embedding APIs
- **[Streamlit](https://streamlit.io/)** for the web interface
- **[Hugging Face](https://huggingface.co/)** for inspiration and community

## 📞 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: [Open an issue](https://github.com/your-username/chat-with-notes/issues) on GitHub
- **Discussions**: [Join the discussion](https://github.com/your-username/chat-with-notes/discussions)
- **Email**: your-email@example.com

---

## 🎯 What Makes This Project Special?

### 🏆 **Professional RAG Implementation**
This isn't just another chatbot wrapper. It's a complete, production-ready RAG system that demonstrates:

- **Modern AI Architecture**: Proper separation of concerns with modular components
- **Industry Best Practices**: Error handling, logging, configuration management
- **Scalable Design**: Easy to extend with new document types or AI providers
- **User-Centric**: Intuitive interface with real-time feedback and progress tracking

### 💼 **Career-Ready Features**
Perfect for showcasing in interviews and portfolios:

- **Full-Stack AI Application**: Frontend, backend, database, and AI integration
- **Production Considerations**: Security, error handling, performance optimization
- **Modern Tech Stack**: Uses the latest tools companies are adopting
- **Documentation**: Comprehensive README and inline documentation

### 🚀 **Ready to Deploy**
This application can be easily deployed to:

- **Streamlit Cloud** (free hosting for Streamlit apps)
- **Heroku, Railway, or Render** (with minimal configuration)
- **Docker containers** (add Dockerfile for containerization)
- **Local enterprise** environments

---

**Built with ❤️ and cutting-edge AI technology**

*Happy chatting with your notes! 📚✨*