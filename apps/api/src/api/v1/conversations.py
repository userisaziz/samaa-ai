from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_salesperson_up
from src.database import get_db
from src.models.user import User
from src.schemas.conversation import ConversationAnalysisResponse, ConversationResponse
from src.services.conversation import get_analysis, get_conversation

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}/analysis", response_model=ConversationAnalysisResponse)
async def get_conversation_analysis(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    analysis = await get_analysis(db, conversation_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
