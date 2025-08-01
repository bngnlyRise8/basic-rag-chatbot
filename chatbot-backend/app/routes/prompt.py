from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from app.services.llm import search_documents, get_chat_model
from app.services.conversation import (
    create_conversation, add_message, get_conversation_history, 
    conversation_exists
)
from app.db.vectorstore import get_vectorstore
from app.db.models import MessageRole
import logging
import os

logger = logging.getLogger(__name__)

class PromptRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class PromptResponse(BaseModel):
    question: str
    answer: str
    conversation_id: str

prompt_router = APIRouter()

@prompt_router.post("/prompt", response_model=PromptResponse)
async def ask_question(
    request: PromptRequest,
    chat_model: ChatOllama = Depends(get_chat_model)
):
    """Ask a question and get an AI-generated answer based on uploaded documents."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Get or create conversation
        if request.conversation_id:
            if not await conversation_exists(request.conversation_id):
                raise HTTPException(status_code=404, detail="Conversation not found")
            conv_id = request.conversation_id
        else:
            conv_id = await create_conversation()
        
        # Get vectorstore with connection from pool
        vectorstore = await get_vectorstore()
        
        # Search for relevant documents with similarity threshold
        # Get up to 10 documents but only keep those above similarity threshold
        similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
        logger.info(f"Using similarity threshold: {similarity_threshold}")
        
        document_chunks = await search_documents(
            request.question, 
            vectorstore, 
            k=10, 
            similarity_threshold=similarity_threshold
        )
        
        # Get conversation history for context
        history = await get_conversation_history(conv_id, limit=10)
        
        # Build context from documents and messages
        if document_chunks:
            context = "\n\n".join([
                f"Source: {chunk['source_filename']} (Relevance: {chunk['similarity_score']:.2f})\nContent: {chunk['content']}"
                for chunk in document_chunks
            ])
            current_message = f"""Context from documents: {context}\n\nCurrent question: {request.question}"""
        else:
            # No documents met the similarity threshold
            current_message = f"""No relevant documents were found in the knowledge base for this question. Please answer based on the conversation history if applicable, or indicate that you don't have relevant information.\n\nCurrent question: {request.question}"""
        
        # Build messages with conversation history
        messages = [
            SystemMessage(content="""You are a helpful AI assistant. Answer the user's question based on the provided context from documents and the conversation history. 
            If the context doesn't contain relevant information, say so. Keep your answer concise and accurate.""")
            ]
        
        # Add conversation history
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "llm":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current question with document context
        messages.append(HumanMessage(content=current_message))
        
        # Generate answer using LLM
        response = await chat_model.ainvoke(messages)
        answer = response.content.strip()
        
        # Save messages to conversation
        await add_message(conv_id, MessageRole.USER, request.question)
        await add_message(conv_id, MessageRole.LLM, answer)
        
        logger.info(f"Generated answer for conversation {conv_id}")
        
        return PromptResponse(
            question=request.question,
            answer=answer,
            conversation_id=conv_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question '{request.question}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )