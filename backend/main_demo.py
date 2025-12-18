"""
Simple FastAPI demo backend for RAG Chat-with-Notes application.
Demonstrates API structure without complex AI dependencies.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chat-with-Notes API (Demo)",
    description="AI-powered document chat system - Demo version",
    version="2.0.0-demo",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"}
    )

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

# In-memory storage for demo
uploaded_documents = {}
sessions = {}

@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0-demo"
    )

@app.get("/api/test")
async def test_connection():
    """Simple test endpoint to verify API connectivity."""
    return {"message": "API connection successful!", "timestamp": datetime.now()}

@app.post("/api/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document (demo version)."""
    try:
        logger.info(f"Upload endpoint called. File received: {file}")
        logger.info(f"File details - filename: {file.filename}, content_type: {file.content_type}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file name
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        supported_types = ['pdf', 'txt', 'docx', 'md']
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{file_extension}'. Supported: {', '.join(supported_types)}"
            )
        
        # Validate file size (10MB limit)
        content = await file.read()
        file_size = len(content)
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size / (1024*1024)}MB"
            )
        
        # Save the file to uploads directory for demo
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        doc_info = DocumentInfo(
            filename=file.filename,
            file_size=file_size,
            upload_time=datetime.now(),
            status="processed"
        )
        
        # Store document info with content preview for demo
        try:
            if file_extension in ['txt', 'md']:
                content_preview = content.decode('utf-8', errors='ignore')[:1000]
            else:
                content_preview = f"Binary file content ({file_extension})"
        except:
            content_preview = "Could not read file content"
            
        uploaded_documents[file_id] = {
            "info": doc_info,
            "content": content_preview,
            "file_path": file_path
        }
        
        logger.info(f"Demo: Successfully uploaded {file.filename} ({file_size} bytes)")
        return doc_info
        
    except HTTPException as he:
        logger.error(f"HTTP Exception during upload: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Chat with uploaded documents (demo version)."""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now(),
                "chat_history": []
            }
        
        # Demo response based on uploaded documents
        if not uploaded_documents:
            demo_response = "Please upload a document first to start chatting with your content!"
        else:
            # Simple demo response
            doc_count = len(uploaded_documents)
            doc_names = [doc["info"].filename for doc in uploaded_documents.values()]
            
            demo_response = f"""Demo Response: I can see you have {doc_count} document(s) uploaded: {', '.join(doc_names)}. 

Your question: "{request.message}"

This is a demo response. In the full version, I would:
1. Search through your documents using semantic similarity
2. Find relevant sections related to your question
3. Generate a contextual response using AI
4. Provide source citations

To enable full AI functionality, configure the Google Gemini API key and install the complete dependencies."""
        
        # Store in session history
        sessions[session_id]["chat_history"].append({
            "user_message": request.message,
            "assistant_response": demo_response,
            "timestamp": datetime.now(),
        })
        
        return ChatResponse(
            response=demo_response,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=[{"filename": doc["info"].filename, "type": "demo"} 
                    for doc in uploaded_documents.values()][:2]  # Max 2 sources for demo
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
        
        filename = uploaded_documents[file_id]["info"].filename
        del uploaded_documents[file_id]
        
        return {"message": f"Document '{filename}' deleted successfully"}
        
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
    print("Starting RAG Chat Backend Server...")
    print("Backend will be available at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/api/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)