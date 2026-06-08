"""Semantic search service using pgvector similarity search."""
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.ai.nvidia_client import nvidia_client
from src.models.conversation import Conversation, ConversationAnalysis
from src.models.recording import Recording
from src.models.salesperson import Salesperson
from src.models.transcript import TranscriptSegment


async def semantic_search(
    db: AsyncSession,
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    store_id: str | None = None,
    salesperson_id: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Perform semantic search across transcript segments using pgvector.

    Returns conversation cards with relevant transcript snippets.
    """
    # Generate query embedding
    query_embedding = nvidia_client.embeddings([query])[0]

    # Build base query: find segments similar to query, grouped by conversation
    # Join with conversations, recordings, and optionally analyses
    seg_query = (
        select(
            TranscriptSegment,
            TranscriptSegment.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Conversation, Conversation.recording_id == TranscriptSegment.recording_id)
        .join(Recording, Recording.id == TranscriptSegment.recording_id)
        .where(
            and_(
                TranscriptSegment.embedding.isnot(None),
                Conversation.start_time <= TranscriptSegment.start_time,
                Conversation.end_time >= TranscriptSegment.end_time,
            )
        )
    )

    # Apply filters
    if date_from:
        seg_query = seg_query.where(Recording.uploaded_at >= date_from)
    if date_to:
        seg_query = seg_query.where(Recording.uploaded_at <= date_to)
    if salesperson_id:
        seg_query = seg_query.where(Recording.salesperson_id == uuid.UUID(salesperson_id))
    if store_id:
        seg_query = seg_query.where(
            Recording.salesperson_id.in_(
                select(Salesperson.id).where(Salesperson.store_id == uuid.UUID(store_id))
            )
        )
    if outcome:
        seg_query = seg_query.where(
            Conversation.id.in_(
                select(ConversationAnalysis.conversation_id).where(
                    ConversationAnalysis.outcome == outcome
                )
            )
        )

    seg_query = seg_query.order_by("distance").limit(limit * 3)  # Over-fetch to deduplicate

    result = await db.execute(seg_query)
    rows = result.all()

    # Group by conversation, keeping best matching segment per conversation
    conversations_map: dict[str, dict] = {}
    for seg, distance in rows:
        conv_id = str(seg.recording_id)  # Group by recording for now
        # Find the conversation this segment belongs to
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.recording_id == seg.recording_id,
                Conversation.start_time <= seg.start_time,
                Conversation.end_time >= seg.end_time,
            )
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            continue

        cid = str(conv.id)
        if cid not in conversations_map:
            # Load analysis for this conversation
            analysis_result = await db.execute(
                select(ConversationAnalysis).where(
                    ConversationAnalysis.conversation_id == conv.id
                )
            )
            analysis = analysis_result.scalar_one_or_none()

            # Load recording
            rec_result = await db.execute(
                select(Recording).where(Recording.id == conv.recording_id)
            )
            recording = rec_result.scalar_one_or_none()

            conversations_map[cid] = {
                "conversation": conv,
                "analysis": analysis,
                "recording": recording,
                "relevant_segments": [],
                "similarity_score": round(1 - float(distance), 4),
            }

        conversations_map[cid]["relevant_segments"].append(seg)

        if len(conversations_map) >= limit:
            break

    return list(conversations_map.values())


async def generate_and_store_embeddings(
    db: AsyncSession,
    recording_id: str,
    batch_size: int = 32,
) -> int:
    """Generate embeddings for all transcript segments of a recording.

    Returns the number of segments embedded.
    """
    # Load segments without embeddings
    result = await db.execute(
        select(TranscriptSegment).where(
            TranscriptSegment.recording_id == uuid.UUID(recording_id),
            TranscriptSegment.embedding.is_(None),
        )
    )
    segments = list(result.scalars().all())

    if not segments:
        return 0

    embedded_count = 0
    # Process in batches
    for i in range(0, len(segments), batch_size):
        batch = segments[i : i + batch_size]
        texts = [seg.text for seg in batch]

        try:
            embeddings = nvidia_client.embeddings(texts)
            for seg, embedding in zip(batch, embeddings):
                seg.embedding = embedding
                embedded_count += 1
            await db.flush()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Embedding generation failed for batch: {e}")
            continue

    return embedded_count
