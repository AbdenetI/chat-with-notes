# 🚀 How to Run Your RAG Application

## Quick Start
```bash
cd "C:\Users\User\Desktop\SWE Projects\chat-with-notes"
.\rag_env\Scripts\Activate.ps1
python -m streamlit run gemini_app.py --server.port 8518
```

## What You Have Built
✅ Complete RAG (Retrieval-Augmented Generation) application
✅ Google Gemini 2.5 Flash integration
✅ Multi-format document processing (PDF, DOCX, TXT)
✅ Clean, user-friendly interface
✅ Single source citations (as requested)
✅ Professional-grade implementation

## Your Applications
- **gemini_app.py** - Main app with Gemini AI (recommended)
- **fixed_app.py** - OpenAI version (backup)
- **demo_app.py** - Demo version (no API key needed)

## Key Features
- Upload documents and ask questions
- Real AI responses from Google Gemini
- Source citations with relevance scores
- Clean text formatting
- Conversation history
- Usage statistics

## API Key Location
Your Gemini API key is stored in `.env` file.

## Backup Instructions
1. Copy entire `chat-with-notes` folder
2. Or use git: `git push origin main` (if connected to GitHub)

## Sharing/Deployment
- Local use: Run as shown above
- Cloud deployment: See DEPLOYMENT.md
- Share code: Upload to GitHub (excluding .env file)

## Troubleshooting
- If port 8518 is busy, change to 8519, 8520, etc.
- Ensure virtual environment is activated
- Check Gemini API key in .env file

---
Created: December 11, 2025
Status: Production Ready ✅