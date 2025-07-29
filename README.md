# AI Document Chatbot

Upload PDFs and chat with their content using AI.

## Setup

### 1. Database
```bash
docker run --name pgvector-db \
  -e POSTGRES_DB=rag_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

### 2. Backend
```bash
cd chatbot-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database settings

# Run migrations (automatically enables pgvector extension)
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 3. Ollama
```bash
# Install Ollama and pull model
ollama pull deepseek-r1
# Ollama runs on localhost:11434
```

### 4. Frontend
```bash
cd chatbot-frontend
npm install
npm run dev
```

## Usage

1. Open http://localhost:5173
2. Upload PDF documents
3. Click "Continue to Chat"
4. Ask questions about your documents

## URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs