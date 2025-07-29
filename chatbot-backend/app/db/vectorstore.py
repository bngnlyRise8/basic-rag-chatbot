from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from app.db.connection import get_async_engine
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def get_embeddings() -> HuggingFaceEmbeddings:
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )
        logger.info("Initialized embeddings model: BAAI/bge-small-en-v1.5")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize embeddings model: {str(e)}")
        raise Exception(f"Embeddings initialization failed: {str(e)}")

async def get_vectorstore() -> PGVector:
    """Get vectorstore with connection from pool."""
    engine = get_async_engine()
    embeddings = get_embeddings()

    try:
        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name="documents", 
            connection=engine,
            use_jsonb=True,
            async_mode=True,
            pre_delete_collection=False,
            create_extension=False
        )
        logger.info("Created vectorstore instance with pooled connection")
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to create vectorstore: {str(e)}")
        raise Exception(f"Vectorstore creation failed: {str(e)}")
