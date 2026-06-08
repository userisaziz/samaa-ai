import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, ConversationAnalysis


async def get_conversation(db: AsyncSession, conversation_id: str) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.analysis))
        .where(Conversation.id == uuid.UUID(conversation_id))
    )
    return result.scalar_one_or_none()


async def get_analysis(db: AsyncSession, conversation_id: str) -> ConversationAnalysis | None:
    result = await db.execute(
        select(ConversationAnalysis).where(
            ConversationAnalysis.conversation_id == uuid.UUID(conversation_id)
        )
    )
    return result.scalar_one_or_none()
