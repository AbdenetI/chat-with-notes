@echo off
REM Start script for RAG Chat-with-Notes Backend (Windows)

echo 🚀 Starting RAG Chat-with-Notes Backend...
echo ==================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo ⚠️  No .env file found. Copying from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env file with your API keys before running!
    pause
    exit /b 1
)

REM Start the server
echo 🌟 Starting FastAPI server on http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/api/docs
echo ==================================
uvicorn main:app --reload --port 8000 --host 0.0.0.0