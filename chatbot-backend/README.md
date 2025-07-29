# Getting Started

## Requirements
A list of required packages can be found in ```requirements.txt```

### 1. Create and activate virtual environment
```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

### 2. Install packages
```bash
pip install -r requirements.txt
```

## Running the DB store
```bash
docker run --name pgvector-db \
  -e POSTGRES_DB=rag_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

## Running the LLM model

### 1. Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Start Ollama server (keep this running)
```bash
ollama serve
```

### 3. Pull a model (in a new terminal)
```bash
ollama pull deepseek-r1
# OR
ollama pull llama2
```

## Configuration

### Environment Variables
Create a `.env` file in the root directory (copy from `.env.example`):
```bash
cp .env.example .env
```

Default values:
```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=rag_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=deepseek-r1
OLLAMA_TEMPERATURE=0.7
```

## Starting the Application (Correct Order)

1. **Start PostgreSQL** (if not already running)
   ```bash
   docker start pgvector-db
   ```

2. **Create `.env` file** (if not exists)
   ```bash
   cp .env.example .env
   # Edit .env if needed for custom configuration
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start Ollama server** (in separate terminal)
   ```bash
   ollama serve
   ```

5. **Start FastAPI application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Upload a PDF document** (REQUIRED before chatting)
   ```bash
   curl -X POST "http://localhost:8000/api/upload" \
     -F "file=@your-document.pdf"
   ```

7. **Start chatting**
   ```bash
   curl -X POST "http://localhost:8000/api/prompt" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is this document about?"}'
   ```

## Important Notes

- You MUST upload at least one document before asking questions
- Ollama server must be running for LLM responses to work
- Check API documentation at http://localhost:8000/docs