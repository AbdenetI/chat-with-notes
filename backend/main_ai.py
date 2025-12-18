"""
Full AI-powered FastAPI backend for RAG Chat-with-Notes application.
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

# Import RAG engine
try:
    from rag_engine import RAGEngine
    AI_ENABLED = True
except ImportError as e:
    logging.warning(f"AI functionality not available: {e}")
    AI_ENABLED = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chat-with-Notes API (Full AI)",
    description="AI-powered document chat system with full RAG functionality",
    version="2.0.0-ai",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
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

# Pydantic models
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
    ai_enabled: bool

# Initialize RAG engine
if AI_ENABLED:
    try:
        rag_engine = RAGEngine()
        logger.info("RAG Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")
        AI_ENABLED = False
        rag_engine = None
else:
    rag_engine = None

# Storage
uploaded_documents = {}
sessions = {}

@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0-ai",
        ai_enabled=AI_ENABLED
    )

@app.get("/api/test")
async def test_connection():
    """Test endpoint for API connectivity."""
    return {
        "message": "API connection successful!", 
        "timestamp": datetime.now(),
        "ai_enabled": AI_ENABLED
    }

@app.post("/api/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document with full AI functionality."""
    try:
        logger.info(f"Upload endpoint called. File received: {file}")
        logger.info(f"File details - filename: {file.filename}, content_type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        supported_types = ['pdf', 'txt', 'docx', 'md']
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_extension}'. Supported: {', '.join(supported_types)}"
            )
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size / (1024*1024)}MB"
            )
        
        # Save file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Process with AI if enabled
        status = "processed"
        if AI_ENABLED and rag_engine:
            try:
                rag_engine.process_document(file_path, file_id, file.filename)
                logger.info(f"AI processing completed for {file.filename}")
            except Exception as e:
                logger.error(f"AI processing failed for {file.filename}: {e}")
                status = "processing_failed"
        else:
            status = "uploaded_no_ai"
        
        # Store document info
        doc_info = DocumentInfo(
            filename=file.filename,
            file_size=file_size,
            upload_time=datetime.now(),
            status=status
        )
        
        uploaded_documents[file_id] = {
            "info": doc_info,
            "file_path": file_path
        }
        
        logger.info(f"Successfully uploaded and processed {file.filename}")
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
    """Chat with uploaded documents using full AI functionality."""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now(),
                "chat_history": []
            }
        
        # Generate response
        if AI_ENABLED and rag_engine:
            # Use full AI functionality
            result = rag_engine.chat(request.message)
            ai_response = result['response']
            sources = result['sources']
        else:
            # Fallback to demo response
            if not uploaded_documents:
                ai_response = "Please upload a document first to start chatting with your content!"
                sources = []
            else:
                doc_count = len(uploaded_documents)
                doc_names = [doc["info"].filename for doc in uploaded_documents.values()]
                
                ai_response = f"""Demo Response (AI not configured): I can see you have {doc_count} document(s) uploaded: {', '.join(doc_names)}.

Your question: "{request.message}"

To enable full AI functionality:
1. Set your GOOGLE_API_KEY in the .env file
2. Install AI dependencies: pip install -r backend/requirements-ai.txt
3. Restart the server

The system will then provide intelligent responses based on your document content."""
                
                sources = [{"filename": doc["info"].filename, "type": "demo"} 
                          for doc in uploaded_documents.values()][:2]
        
        # Store in session history
        sessions[session_id]["chat_history"].append({
            "user_message": request.message,
            "assistant_response": ai_response,
            "timestamp": datetime.now(),
            "sources": sources
        })
        
        return ChatResponse(
            response=ai_response,
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
        
        filename = uploaded_documents[file_id]["info"].filename
        
        # Delete from AI index if enabled
        if AI_ENABLED and rag_engine:
            try:
                rag_engine.delete_document(file_id)
                logger.info(f"Deleted {filename} from AI index")
            except Exception as e:
                logger.warning(f"Failed to delete from AI index: {e}")
        
        # Delete file
        file_path = uploaded_documents[file_id]["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from memory
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
    print("Starting RAG Chat Backend Server with Full AI...")
    print("Backend will be available at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/api/docs")
    print(f"AI Functionality: {'Enabled' if AI_ENABLED else 'Disabled (install dependencies and configure API key)'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)