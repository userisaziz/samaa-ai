"""Salesperson scoring worker — scores performance across 5 dimensions."""
import logging
import uuid
from datetime import datetime, timezone

from src.ai.scorer import compute_average_scores, score_salesperson_performance
from src.config import settings
from src.models.conversation import Conversation, ConversationAnalysis
from src.models.metrics import DailyMetrics
from src.models.recording import Recording, RecordingStatus
from src.models.transcript import TranscriptSegment
from src.workers.celery_app import celery_app
from src.workers.preprocessing import (
    _get_recording_sync,
    _update_recording_status_sync,
)

logger = logging.getLogger(__name__)


def _get_conversations_with_segments_sync(recording_id: str) -> list[dict]:
    """Load conversations with their transcript segments."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        conversations = (
            session.query(Conversation)
            .filter(Conversation.recording_id == uuid.UUID(recording_id))
            .order_by(Conversation.start_time)
            .all()
        )

        result = []
        for conv in conversations:
            segments = (
                session.query(TranscriptSegment)
                .filter(
                    TranscriptSegment.recording_id == uuid.UUID(recording_id),
                    TranscriptSegment.start_time >= conv.start_time - 1.0,
                    TranscriptSegment.end_time <= conv.end_time + 1.0,
                )
                .order_by(TranscriptSegment.start_time)
                .all()
            )
            result.append({
                "conversation_id": str(conv.id),
                "segments": [
                    {
                        "start": seg.start_time,
                        "end": seg.end_time,
                        "text": seg.text,
                        "speaker": seg.speaker_label,
                    }
                    for seg in segments
                ],
            })
    engine.dispose()
    return result


def _store_scores_sync(conversation_id: str, scores: dict):
    """Store scoring results in conversation_analysis.scores."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        analysis = session.query(ConversationAnalysis).filter(
            ConversationAnalysis.conversation_id == uuid.UUID(conversation_id)
        ).first()

        if analysis:
            analysis.scores = scores
        else:
            # Create analysis record with just scores
            ca = ConversationAnalysis(
                conversation_id=uuid.UUID(conversation_id),
                scores=scores,
            )
            session.add(ca)

        session.commit()
    engine.dispose()


def _complete_recording_sync(recording_id: str):
    """Mark recording as COMPLETED with processed_at timestamp."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        recording = session.query(Recording).filter(
            Recording.id == uuid.UUID(recording_id)
        ).first()
        if recording:
            recording.status = RecordingStatus.COMPLETED
            recording.processed_at = datetime.now(timezone.utc)
            recording.error_message = None
        session.commit()
    engine.dispose()


def _update_daily_metrics_sync(recording_id: str):
    """Update daily metrics for the salesperson and store after scoring."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        # Get recording info
        recording = session.query(Recording).filter(
            Recording.id == uuid.UUID(recording_id)
        ).first()
        if not recording:
            engine.dispose()
            return

        salesperson_id = recording.salesperson_id
        today = datetime.now(timezone.utc).date()

        # Get store_id from salesperson
        from src.models.salesperson import Salesperson
        salesperson = session.query(Salesperson).filter(
            Salesperson.id == salesperson_id
        ).first()
        if not salesperson:
            engine.dispose()
            return

        store_id = salesperson.store_id

        # Compute metrics for salesperson today
        _upsert_daily_metrics(session, salesperson_id, "SALESPERSON", today)
        _upsert_daily_metrics(session, store_id, "STORE", today)

        session.commit()
        logger.info(f"[{recording_id}] Updated daily metrics")
    engine.dispose()


def _upsert_daily_metrics(session, entity_id, entity_type: str, date_val):
    """Insert or update daily metrics for an entity."""
    from sqlalchemy import func

    # Get all conversations for this entity today
    if entity_type == "SALESPERSON":
        from src.models.recording import Recording
        recording_ids = [
            r.id for r in session.query(Recording.id).filter(
                Recording.salesperson_id == entity_id
            ).all()
        ]
    else:
        from src.models.salesperson import Salesperson
        from src.models.recording import Recording
        sp_ids = [
            s.id for s in session.query(Salesperson.id).filter(
                Salesperson.store_id == entity_id
            ).all()
        ]
        recording_ids = [
            r.id for r in session.query(Recording.id).filter(
                Recording.salesperson_id.in_(sp_ids)
            ).all()
        ]

    if not recording_ids:
        return

    # Count conversations and compute avg score
    conv_count = session.query(Conversation).filter(
        Conversation.recording_id.in_(recording_ids)
    ).count()

    # Get average overall score from analyses
    avg_result = session.query(func.avg(ConversationAnalysis.confidence)).join(
        Conversation
    ).filter(
        Conversation.recording_id.in_(recording_ids)
    ).scalar()

    # Count sales
    sale_count = session.query(ConversationAnalysis).join(
        Conversation
    ).filter(
        Conversation.recording_id.in_(recording_ids),
        ConversationAnalysis.outcome == "SALE_MADE",
    ).count()

    conversion_rate = (sale_count / conv_count * 100) if conv_count > 0 else 0

    # Upsert
    existing = session.query(DailyMetrics).filter(
        DailyMetrics.entity_id == entity_id,
        DailyMetrics.entity_type == entity_type,
        DailyMetrics.date == date_val,
    ).first()

    if existing:
        existing.conversation_count = conv_count
        existing.avg_score = float(avg_result) if avg_result else None
        existing.conversion_rate = round(conversion_rate, 1)
    else:
        dm = DailyMetrics(
            entity_id=entity_id,
            entity_type=entity_type,
            date=date_val,
            conversation_count=conv_count,
            avg_score=float(avg_result) if avg_result else None,
            conversion_rate=round(conversion_rate, 1),
        )
        session.add(dm)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, name="score_salesperson")
def score_salesperson(self, recording_id: str) -> str:
    """Score salesperson performance across 5 dimensions for each conversation.

    After scoring:
    - Stores scores in conversation_analysis.scores
    - Marks recording as COMPLETED
    - Updates daily metrics

    Returns:
        recording_id (final stage in pipeline)
    """
    logger.info(f"[{recording_id}] Starting salesperson scoring")
    _update_recording_status_sync(recording_id, RecordingStatus.SCORING)

    try:
        recording = _get_recording_sync(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        # Load conversations with segments
        conversations = _get_conversations_with_segments_sync(recording_id)
        if not conversations:
            logger.warning(f"[{recording_id}] No conversations to score")
            _complete_recording_sync(recording_id)
            return recording_id

        logger.info(f"[{recording_id}] Scoring {len(conversations)} conversations")

        all_scores = []
        scored_count = 0

        for conv in conversations:
            conv_id = conv["conversation_id"]
            segments = conv["segments"]

            if not segments:
                continue

            scores = score_salesperson_performance(segments)
            if scores is None:
                logger.warning(f"[{recording_id}] Scoring failed for conversation {conv_id}")
                continue

            _store_scores_sync(conv_id, scores)
            all_scores.append(scores)
            scored_count += 1

            logger.info(
                f"[{recording_id}] Conversation {conv_id} scores: "
                f"greeting={scores.get('greeting_score')}, "
                f"discovery={scores.get('discovery_score')}, "
                f"product={scores.get('product_knowledge_score')}, "
                f"objection={scores.get('objection_handling_score')}, "
                f"closing={scores.get('closing_score')}"
            )

        # Compute averages
        if all_scores:
            averages = compute_average_scores(all_scores)
            logger.info(f"[{recording_id}] Average scores: {averages}")

        # Mark recording as completed
        _complete_recording_sync(recording_id)

        # Update daily metrics
        _update_daily_metrics_sync(recording_id)

        logger.info(
            f"[{recording_id}] Scoring complete: {scored_count}/{len(conversations)} scored"
        )
        return recording_id

    except Exception as exc:
        logger.error(f"[{recording_id}] Scoring failed: {exc}")
        _update_recording_status_sync(recording_id, RecordingStatus.FAILED, str(exc))
        raise self.retry(exc=exc)
