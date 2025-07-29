from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from langchain_postgres import PGVector
from app.services.embedder import process_and_store_pdf_file, generate_file_hash, check_document_exists
from app.db.vectorstore import get_vectorstore
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class UploadResponse(BaseModel):
    filename: str
    upload_time: datetime
    chunk_count: int
    status: str = "success"
    message: str = ""

documents_router = APIRouter()

@documents_router.post("/document", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF document and store its embeddings in the vector database."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    contents = await file.read()
    
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    
    # Get vectorstore with connection from pool
    vectorstore = await get_vectorstore()
    
    # Check for duplicates
    file_hash = generate_file_hash(contents)
    if await check_document_exists(file_hash, vectorstore):
        raise HTTPException(
            status_code=409, 
            detail=f"Document '{file.filename}' has already been uploaded"
        )

    try:
        # Process the PDF and get the chunk count
        chunk_count = await process_and_store_pdf_file(contents, file.filename, vectorstore)
        
        if chunk_count == 0:
            logger.warning(f"No content extracted from PDF: {file.filename}")
            return UploadResponse(
                filename=file.filename,
                upload_time=datetime.now(timezone.utc),
                chunk_count=0,
                status="warning",
                message="PDF processed but no text content was extracted"
            )

        return UploadResponse(
            filename=file.filename,
            upload_time=datetime.now(timezone.utc),
            chunk_count=chunk_count,
            status="success",
            message=f"Successfully processed {chunk_count} chunks"
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process PDF: {str(e)}"
        )

class DocumentInfo(BaseModel):
    filename: str
    file_hash: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

@documents_router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents with their metadata."""
    try:
        from app.db.connection import get_async_engine
        
        engine = get_async_engine()
        
        async with engine.begin() as conn:
            # Get unique file hashes first
            hash_query = text("""
                SELECT DISTINCT cmetadata->>'file_hash' as file_hash
                FROM langchain_pg_embedding 
                WHERE cmetadata->>'file_hash' IS NOT NULL
            """)
            
            result = await conn.execute(hash_query)
            file_hashes = [row[0] for row in result.fetchall()]
        
        documents = []
        vectorstore = await get_vectorstore()
        
        # For each unique file hash, get one document to extract metadata
        for file_hash in file_hashes:
            try:
                # Get one document for metadata
                sample_docs = await vectorstore.asimilarity_search("", k=1, filter={"file_hash": file_hash})
                if sample_docs:
                    filename = sample_docs[0].metadata.get("source_filename", "Unknown")
                    
                    documents.append(DocumentInfo(
                        filename=filename,
                        file_hash=file_hash
                    ))
            except Exception as e:
                logger.warning(f"Error processing file hash {file_hash}: {str(e)}")
                continue
        
        # Sort by filename for consistent ordering
        documents.sort(key=lambda x: x.filename)
        
        return DocumentListResponse(
            documents=documents
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

class DeleteResponse(BaseModel):
    filename: str
    deleted_chunks: int
    status: str = "success"
    message: str = ""

@documents_router.delete("/document/{file_hash}", response_model=DeleteResponse)
async def delete_document(file_hash: str):
    """Delete a document and all its chunks by file hash."""
    try:
        vectorstore = await get_vectorstore()
        
        # Use while loop to delete all chunks with this file_hash in batches
        total_deleted = 0
        filename = "Unknown"
        
        # Get first batch of chunks with this file_hash
        batch_docs = await vectorstore.asimilarity_search("", k=1000, filter={"file_hash": file_hash})
        print(batch_docs)
        
        if not batch_docs:
            raise HTTPException(
                status_code=404,
                detail=f"Document with hash '{file_hash}' not found"
            )
        
        filename = batch_docs[0].metadata.get("source_filename", "Unknown")
        
        # Keep deleting batches until no more chunks remain
        while batch_docs:
            doc_ids = [doc.id for doc in batch_docs]
            
            # Delete this batch
            await vectorstore.adelete(ids=doc_ids)
            batch_deleted = len(doc_ids)
            total_deleted += batch_deleted
            
            logger.info(f"Deleted batch of {batch_deleted} chunks (total so far: {total_deleted})")
            
            # Get next batch for the next iteration
            batch_docs = await vectorstore.asimilarity_search("", k=1000, filter={"file_hash": file_hash})
        
        
        logger.info(f"Deleted {total_deleted} chunks for document: {filename} (hash: {file_hash})")
        
        return DeleteResponse(
            filename=filename,
            deleted_chunks=total_deleted,
            status="success",
            message=f"Successfully deleted {total_deleted} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document with hash {file_hash}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
