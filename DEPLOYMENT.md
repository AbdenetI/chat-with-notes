# 🚀 Deployment Guide - Chat with Notes RAG Application

This guide covers various deployment options for your RAG application, from local development to production hosting.

## 📋 Table of Contents

- [Local Development](#local-development)
- [Streamlit Cloud (Free)](#streamlit-cloud-free)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Environment Variables](#environment-variables)
- [Production Considerations](#production-considerations)

## 🏠 Local Development

### Quick Start (Already Done)
```bash
# 1. Clone and setup
git clone <your-repo>
cd chat-with-notes
python setup.py  # Runs automated setup

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Run locally
source rag_env/bin/activate  # Linux/Mac
# OR
rag_env\Scripts\activate     # Windows

streamlit run streamlit_app.py
```

## ☁️ Streamlit Cloud (Free)

**Best for:** Demos, personal use, sharing with small teams

### Prerequisites
- GitHub repository with your code
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Step-by-Step Deployment

1. **Prepare Your Repository**
   ```bash
   # Ensure all files are committed and pushed
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Streamlit Cloud App**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set main file: `streamlit_app.py`
   - Choose branch: `main`

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to "App settings" → "Secrets"
   - Add your environment variables:
   ```toml
   OPENAI_API_KEY = "your-actual-api-key"
   CHAT_MODEL = "gpt-3.5-turbo"
   EMBEDDING_MODEL = "text-embedding-3-small"
   ```

4. **Deploy**
   - Click "Deploy"
   - Your app will be available at `https://your-app-name.streamlit.app`

### Streamlit Cloud Limitations
- **CPU/Memory**: Limited resources for large documents
- **Storage**: No persistent storage (files are temporary)
- **Sessions**: Apps sleep after inactivity

## 🐳 Docker Deployment

**Best for:** Consistent environments, enterprise deployment, cloud hosting

### Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads vector_db

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Create docker-compose.yml
```yaml
version: '3.8'

services:
  chat-with-notes:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHAT_MODEL=${CHAT_MODEL:-gpt-3.5-turbo}
      - EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-3-small}
    volumes:
      - ./uploads:/app/uploads
      - ./vector_db:/app/vector_db
    restart: unless-stopped

  # Optional: Add a reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - chat-with-notes
```

### Deploy with Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Scale if needed
docker-compose up -d --scale chat-with-notes=3
```

## 🌐 Cloud Platforms

### Heroku
```bash
# 1. Install Heroku CLI
# 2. Login and create app
heroku login
heroku create your-app-name

# 3. Configure buildpacks
heroku buildpacks:add heroku/python

# 4. Set environment variables
heroku config:set OPENAI_API_KEY="your-key"
heroku config:set CHAT_MODEL="gpt-3.5-turbo"

# 5. Create Procfile
echo "web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# 6. Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway new
railway up

# 3. Set environment variables in Railway dashboard
```

### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/chat-with-notes', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/chat-with-notes']
- name: 'gcr.io/cloud-builders/gcloud'
  args:
  - 'run'
  - 'deploy'
  - 'chat-with-notes'
  - '--image'
  - 'gcr.io/$PROJECT_ID/chat-with-notes'
  - '--platform'
  - 'managed'
  - '--region'
  - 'us-central1'
  - '--allow-unauthenticated'
```

### AWS ECS/Fargate
```json
{
  "family": "chat-with-notes",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "chat-with-notes",
      "image": "your-ecr-repo/chat-with-notes:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chat-with-notes",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 🔐 Environment Variables

### Required Variables
```bash
# Core API Key
OPENAI_API_KEY=sk-...                    # Required

# Model Configuration
CHAT_MODEL=gpt-3.5-turbo                # Optional
EMBEDDING_MODEL=text-embedding-3-small  # Optional
MAX_TOKENS=2000                         # Optional
TEMPERATURE=0.1                         # Optional

# Document Processing
CHUNK_SIZE=1000                         # Optional
CHUNK_OVERLAP=200                       # Optional
MAX_FILE_SIZE=52428800                  # Optional (50MB)

# Vector Database
VECTOR_DB_NAME=notes_collection         # Optional
SIMILARITY_THRESHOLD=0.7                # Optional
MAX_RETRIEVED_DOCS=4                    # Optional
```

### Platform-Specific Setup

**Streamlit Cloud:**
```toml
# In Streamlit secrets
OPENAI_API_KEY = "sk-..."
```

**Heroku:**
```bash
heroku config:set OPENAI_API_KEY="sk-..."
```

**Docker:**
```bash
# In .env file
OPENAI_API_KEY=sk-...
```

## 🏭 Production Considerations

### Performance Optimization

1. **Caching Strategy**
   ```python
   # Add to streamlit_app.py
   @st.cache_resource
   def load_app():
       return ChatWithNotesApp()
   ```

2. **Memory Management**
   ```python
   # Limit concurrent uploads
   MAX_CONCURRENT_UPLOADS = 3
   
   # Clear old conversations
   if len(st.session_state.messages) > 50:
       st.session_state.messages = st.session_state.messages[-30:]
   ```

3. **Database Optimization**
   ```python
   # Use persistent ChromaDB
   CHROMA_PERSIST_DIRECTORY = "./chroma_data"
   ```

### Security Enhancements

1. **API Key Rotation**
   ```python
   # Implement key rotation logic
   def rotate_api_key():
       # Logic to update API key
       pass
   ```

2. **Rate Limiting**
   ```python
   # Add rate limiting
   from streamlit_limiter import limiter
   
   @limiter.limit("10 per minute")
   def ask_question():
       pass
   ```

3. **Input Validation**
   ```python
   # Enhanced file validation
   def validate_upload(file):
       # Virus scanning
       # Size limits
       # Content validation
       pass
   ```

### Monitoring and Logging

1. **Application Monitoring**
   ```python
   # Add logging
   import logging
   logging.basicConfig(level=logging.INFO)
   
   # Add metrics
   import prometheus_client
   ```

2. **Error Tracking**
   ```python
   # Add Sentry for error tracking
   import sentry_sdk
   sentry_sdk.init("your-dsn")
   ```

### Scaling Considerations

1. **Horizontal Scaling**
   - Use Redis for session storage
   - Implement load balancing
   - Separate ChromaDB instance

2. **Vertical Scaling**
   - Increase memory for larger documents
   - Use GPUs for faster embeddings
   - Optimize chunk sizes

### Cost Optimization

1. **OpenAI API Costs**
   ```python
   # Monitor token usage
   def track_usage(response):
       cost = response.get('token_usage', {}).get('total_cost', 0)
       # Log to database
   ```

2. **Infrastructure Costs**
   - Use spot instances
   - Implement auto-scaling
   - Cache frequently accessed data

## 🔍 Health Checks

### Application Health Check
```python
# health_check.py
def health_check():
    """Check if all components are working."""
    try:
        # Test database connection
        vector_store = VectorStore()
        
        # Test OpenAI API
        from openai import OpenAI
        client = OpenAI()
        
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python health_check.py || exit 1
```

## 📊 Performance Benchmarks

### Expected Performance
- **Document Processing**: ~1-2 seconds per MB
- **Query Response**: ~2-5 seconds per query
- **Memory Usage**: ~200-500MB baseline
- **Storage**: ~10-20MB per 100 document chunks

### Optimization Targets
- **Response Time**: <3 seconds for queries
- **Upload Time**: <10 seconds for 10MB files
- **Memory Efficiency**: <1GB for typical usage
- **Cost**: <$0.01 per query (with gpt-3.5-turbo)

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Code is tested and working locally
- [ ] All sensitive data is in environment variables
- [ ] Requirements.txt is up to date
- [ ] Documentation is complete
- [ ] Error handling is implemented

### Deployment
- [ ] Choose deployment platform
- [ ] Set up environment variables
- [ ] Configure monitoring/logging
- [ ] Test deployed application
- [ ] Set up backup strategy

### Post-Deployment
- [ ] Monitor application performance
- [ ] Track costs and usage
- [ ] Set up alerts for errors
- [ ] Plan for updates and maintenance
- [ ] Document operational procedures

---

**🎉 Your RAG application is ready for the world!**

Choose the deployment option that best fits your needs:
- **Streamlit Cloud**: For quick demos and personal use
- **Docker**: For consistent, portable deployments
- **Cloud Platforms**: For production applications with scaling needs

Good luck with your deployment! 🚀