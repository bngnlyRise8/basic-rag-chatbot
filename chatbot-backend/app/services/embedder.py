import tempfile
import os
import logging
import hashlib
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector

logger = logging.getLogger(__name__)

def generate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

async def check_document_exists(file_hash: str, vectorstore: PGVector) -> bool:
    try:
        # Search for documents with this file hash in metadata
        results = await vectorstore.asimilarity_search("", k=1, filter={"file_hash": file_hash})
        return len(results) > 0
    except Exception as e:
        logger.error(f"Error checking for duplicate document: {str(e)}")
        return False

async def process_and_store_pdf_file(file_bytes: bytes, filename: str, vectorstore: PGVector) -> int:
    tmp_path = None
    
    try:
        # Generate file hash for duplicate detection
        file_hash = generate_file_hash(file_bytes)
        logger.info(f"Generated file hash: {file_hash[:12]}...")
        
        # Write PDF bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
            logger.info(f"Created temporary file: {tmp_path}")

        # Load and split the PDF
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        if not documents:
            logger.warning(f"No documents extracted from PDF: {filename}")
            return 0
            
        logger.info(f"Extracted {len(documents)} pages from PDF: {filename}")

        # Add filename and file hash to metadata
        for doc in documents:
            doc.metadata['source_filename'] = filename
            doc.metadata['file_hash'] = file_hash

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
        )
        splits = text_splitter.split_documents(documents)
        
        if not splits:
            logger.warning(f"No text chunks created from PDF: {filename}")
            return 0
            
        logger.info(f"Created {len(splits)} chunks from PDF: {filename}")

        # Store the chunks in the vectorstore
        try:
            await vectorstore.aadd_documents(splits)
            logger.info(f"Successfully stored {len(splits)} chunks in vectorstore")
        except Exception as e:
            logger.error(f"Failed to store chunks in vectorstore: {str(e)}")
            raise Exception(f"Database storage failed: {str(e)}")
        
        return len(splits)
    
    except Exception as e:
        logger.error(f"Error processing PDF {filename}: {str(e)}")
        raise
    
    finally:
        # Clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Cleaned up temporary file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmp_path}: {str(e)}")
