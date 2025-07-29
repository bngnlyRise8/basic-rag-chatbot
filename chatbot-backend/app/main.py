from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.documents import documents_router
from app.routes.prompt import prompt_router
from app.db.connection import get_pool_status
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="AI Chatbot Backend",
    description="FastAPI backend for uploading PDFs and storing embeddings",
    version="0.1.0"
)

# Add CORS middleware
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Include routes
app.include_router(documents_router, prefix="/api")
app.include_router(prompt_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Chatbot Backend...")
    
    try:
        from app.db.vectorstore import get_vectorstore
        await get_vectorstore()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.warning("App started but database is not accessible")

@app.get("/health")
async def health_check():
    """Health check endpoint with connection pool status."""
    pool_status = await get_pool_status()
    return {
        "status": "healthy",
        "pool": pool_status
    }
