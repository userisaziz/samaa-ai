from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_salesperson_up
from src.database import get_db
from src.models.user import User
from src.schemas.conversation import ConversationAnalysisResponse, ConversationResponse
from src.schemas.recording import RecordingResponse, TranscriptSegmentResponse
from src.services.search import semantic_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    date_from: str | None = None,
    date_to: str | None = None,
    store_id: str | None = None,
    salesperson_id: str | None = None,
    outcome: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    """Semantic search across transcript segments using pgvector similarity."""
    results = await semantic_search(
        db,
        query=q,
        date_from=date_from,
        date_to=date_to,
        store_id=store_id,
        salesperson_id=salesperson_id,
        outcome=outcome,
        limit=limit,
    )

    # Serialize results
    serialized = []
    for r in results:
        conv = r["conversation"]
        analysis = r["analysis"]
        recording = r["recording"]
        segments = r["relevant_segments"]

        serialized.append({
            "conversation": {
                "id": str(conv.id),
                "recording_id": str(conv.recording_id),
                "start_time": conv.start_time,
                "end_time": conv.end_time,
                "segment_count": conv.segment_count,
                "summary": conv.summary,
                "created_at": str(conv.created_at),
            },
            "analysis": {
                "id": str(analysis.id),
                "conversation_id": str(analysis.conversation_id),
                "intent": analysis.intent,
                "products": analysis.products or [],
                "budget": analysis.budget,
                "objections": analysis.objections or [],
                "competitors": analysis.competitors or [],
                "closing_attempt": analysis.closing_attempt,
                "outcome": analysis.outcome,
                "confidence": analysis.confidence,
                "scores": analysis.scores,
                "summary": analysis.summary,
                "coaching_notes": analysis.coaching_notes,
                "created_at": str(analysis.created_at),
            } if analysis else None,
            "recording": {
                "id": str(recording.id),
                "salesperson_id": str(recording.salesperson_id),
                "file_url": recording.file_url,
                "file_size": recording.file_size,
                "duration_seconds": recording.duration_seconds,
                "format": recording.format,
                "status": recording.status.value if hasattr(recording.status, "value") else recording.status,
                "error_message": recording.error_message,
                "uploaded_at": str(recording.uploaded_at),
                "processed_at": str(recording.processed_at) if recording.processed_at else None,
            } if recording else None,
            "relevant_segments": [
                {
                    "id": str(seg.id),
                    "recording_id": str(seg.recording_id),
                    "speaker_label": seg.speaker_label,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text,
                }
                for seg in segments
            ],
            "similarity_score": r["similarity_score"],
        })

    return {"results": serialized, "total": len(serialized)}
