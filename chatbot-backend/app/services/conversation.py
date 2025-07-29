import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.db.models import Conversation, Message, MessageRole
from app.db.connection import get_async_engine

logger = logging.getLogger(__name__)

def get_async_session() -> AsyncSession:
    """Get async database session."""
    engine = get_async_engine()
    return AsyncSession(engine)

def create_conversation_id() -> str:
    """Generate a new conversation ID."""
    conv_id = str(uuid.uuid4())
    logger.info(f"Generated conversation ID: {conv_id}")
    return conv_id

async def create_conversation(title: Optional[str] = None) -> str:
    """Create a new conversation and return its ID."""
    conv_id = create_conversation_id()
    
    async with get_async_session() as session:
        conversation = Conversation(
            id=conv_id,
            title=title
        )
        session.add(conversation)
        await session.commit()
        
    logger.info(f"Created conversation: {conv_id}")
    return conv_id

async def add_message(conversation_id: str, role: MessageRole, content: str) -> None:
    """Add a message to a conversation."""
    async with get_async_session() as session:
        # Update conversation's updated_at timestamp
        await session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        
        # Add the message
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        session.add(message)
        await session.commit()
        
    logger.info(f"Added {role.value} message to conversation {conversation_id}")

async def get_conversation_history(
    conversation_id: str, 
    limit: Optional[int] = 50
    ) -> List[Dict]:
    """Get conversation messages in chronological order."""
    async with get_async_session() as session:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        
        if limit:
            query = query.limit(limit)
            
        result = await session.execute(query)
        messages = result.scalars().all()
        
        return [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]

async def conversation_exists(conversation_id: str) -> bool:
    """Check if a conversation exists."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none() is not None