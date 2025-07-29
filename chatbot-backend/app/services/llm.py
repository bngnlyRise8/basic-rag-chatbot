import logging
import os
from typing import List, Dict, Any
from functools import lru_cache
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from langchain_postgres import PGVector
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

async def search_documents(query: str, vectorstore: PGVector, k: int = 3) -> List[Dict[str, Any]]:
    try:
        results = await vectorstore.asimilarity_search(query, k=k)
        
        search_results = []
        for doc in results:
            search_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source_filename": doc.metadata.get("source_filename", "Unknown")
            })
        
        logger.info(f"Found {len(search_results)} results for query: {query[:50]}...")
        return search_results
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise Exception(f"Search failed: {str(e)}")

@lru_cache()
def get_chat_model() -> ChatOllama:
    try:
        # Get configuration from environment variables
        host = os.getenv("OLLAMA_HOST", "localhost")
        port = os.getenv("OLLAMA_PORT", "11434")
        model = os.getenv("OLLAMA_MODEL", "deepseek-r1")
        temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        base_url = f"http://{host}:{port}"
        
        chat_model = ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url
        )
        logger.info(f"Initialized Ollama chat model: {model} at {base_url} (temperature={temperature})")
        return chat_model
    except Exception as e:
        logger.error(f"Failed to initialize Ollama chat model: {str(e)}")
        raise Exception(f"Ollama chat model initialization failed: {str(e)}")