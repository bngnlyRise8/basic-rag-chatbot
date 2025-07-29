from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from functools import lru_cache
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@lru_cache()
def get_async_engine() -> AsyncEngine:
    """Create async engine with connection pooling."""
    # Build database URL from environment variables
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "rag_db")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "postgres")
    
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    
    engine = create_async_engine(
        database_url,
        pool_size=5,           # Number of connections to maintain
        max_overflow=5,        # Extra connections under high load  
        pool_timeout=30,        # Timeout waiting for connection
        pool_recycle=3600,      # Recycle connections after 1 hour
        echo=False              # Set True for SQL logging
    )
    
    logger.info(f"Created async engine with pool_size=5, max_overflow=5")
    return engine

async def get_pool_status() -> dict:
    """Get connection pool statistics."""
    engine = get_async_engine()
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(), 
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow()
    }