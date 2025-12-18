"""
FastAPI backend for RAG Chat-with-Notes application.
Modern REST API replacing Streamlit for better enterprise architecture.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime
import logging

# Import our RAG components
from src.app import ChatWithNotesApp
from src.config import SUPPORTED_FILE_TYPES, MAX_FILE_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chat-with-Notes API",
    description="AI-powered document chat system with RAG capabilities",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG application
rag_app = None

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    sources: List[dict] = []

class DocumentInfo(BaseModel):
    filename: str
    file_size: int
    upload_time: datetime
    status: str

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str

# Global variables for session management
sessions = {}
uploaded_documents = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG application on startup."""
    global rag_app
    try:
        rag_app = ChatWithNotesApp()
        logger.info("RAG application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG application: {e}")
        raise e

@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0"
    )

@app.post("/api/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for RAG."""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_FILE_TYPES)}"
            )
        
        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Process document with RAG
        if rag_app is None:
            raise HTTPException(status_code=500, detail="RAG application not initialized")
            
        # Add document to RAG system
        success = rag_app.add_document(file_path)
        
        if not success:
            os.remove(file_path)  # Clean up on failure
            raise HTTPException(status_code=500, detail="Failed to process document")
        
        # Store document info
        doc_info = DocumentInfo(
            filename=file.filename,
            file_size=file_size,
            upload_time=datetime.now(),
            status="processed"
        )
        
        uploaded_documents[file_id] = {
            "info": doc_info,
            "file_path": file_path
        }
        
        logger.info(f"Successfully uploaded and processed: {file.filename}")
        return doc_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Chat with uploaded documents using RAG."""
    try:
        if rag_app is None:
            raise HTTPException(status_code=500, detail="RAG application not initialized")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now(),
                "chat_history": []
            }
        
        # Get response from RAG system
        response_data = rag_app.chat(request.message)
        
        # Extract response and sources
        if isinstance(response_data, dict):
            response_text = response_data.get('response', str(response_data))
            sources = response_data.get('sources', [])
        else:
            response_text = str(response_data)
            sources = []
        
        # Store in session history
        sessions[session_id]["chat_history"].append({
            "user_message": request.message,
            "assistant_response": response_text,
            "timestamp": datetime.now(),
            "sources": sources
        })
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    """Get list of uploaded documents."""
    try:
        docs = []
        for file_id, doc_data in uploaded_documents.items():
            doc_info = doc_data["info"]
            docs.append({
                "id": file_id,
                "filename": doc_info.filename,
                "file_size": doc_info.file_size,
                "upload_time": doc_info.upload_time.isoformat(),
                "status": doc_info.status
            })
        
        return {"documents": docs}
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

@app.delete("/api/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete an uploaded document."""
    try:
        if file_id not in uploaded_documents:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove file from filesystem
        file_path = uploaded_documents[file_id]["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from tracking
        del uploaded_documents[file_id]
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@app.get("/api/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = sessions[session_id]["chat_history"]
        return {"session_id": session_id, "history": history}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)