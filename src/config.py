"""
Configuration settings for the Chat with Notes RAG application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"

# Create directories if they don't exist
UPLOADS_DIR.mkdir(exist_ok=True)
VECTOR_DB_DIR.mkdir(exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model
CHAT_MODEL = "gpt-3.5-turbo"  # OpenAI chat model
MAX_TOKENS = 2000  # Maximum tokens for responses
TEMPERATURE = 0.1  # Low temperature for more consistent responses

# Document Processing Configuration
CHUNK_SIZE = 1000  # Size of text chunks for embedding
CHUNK_OVERLAP = 200  # Overlap between chunks
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
SUPPORTED_FILE_TYPES = [".pdf", ".txt", ".docx"]

# Vector Database Configuration
VECTOR_DB_NAME = "notes_collection"
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score for retrieval
MAX_RETRIEVED_DOCS = 4  # Number of relevant chunks to retrieve

# Streamlit Configuration
PAGE_TITLE = "Chat with Your Notes"
PAGE_ICON = "📚"
LAYOUT = "wide"