"""Conversation analysis worker — analyzes conversations using Llama 3.3 70B."""
import logging
import uuid

from src.ai.analyzer import analyze_conversation as analyze_conversation_ai
from src.ai.analyzer import MIN_CONFIDENCE_THRESHOLD
from src.config import settings
from src.models.conversation import Conversation, ConversationAnalysis
from src.models.recording import RecordingStatus
from src.models.transcript import TranscriptSegment
from src.workers.celery_app import celery_app
from src.workers.preprocessing import (
    _get_recording_sync,
    _update_recording_status_sync,
)

logger = logging.getLogger(__name__)


def _get_conversations_sync(recording_id: str) -> list[dict]:
    """Load conversations from DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        rows = (
            session.query(Conversation)
            .filter(Conversation.recording_id == uuid.UUID(recording_id))
            .order_by(Conversation.start_time)
            .all()
        )
        conversations = [
            {
                "id": str(row.id),
                "start_time": row.start_time,
                "end_time": row.end_time,
            }
            for row in rows
        ]
    engine.dispose()
    return conversations


def _get_conversation_segments_sync(conversation_id: str) -> list[dict]:
    """Load transcript segments for a conversation's time range."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # First get the conversation's recording_id and time range
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        conv = session.query(Conversation).filter(
            Conversation.id == uuid.UUID(conversation_id)
        ).first()
        if not conv:
            engine.dispose()
            return []

        recording_id = conv.recording_id
        start_time = conv.start_time
        end_time = conv.end_time

        # Get transcript segments within this time range
        rows = (
            session.query(TranscriptSegment)
            .filter(
                TranscriptSegment.recording_id == recording_id,
                TranscriptSegment.start_time >= start_time,  # no lower buffer to avoid overlap
                TranscriptSegment.end_time <= end_time + 1.0,
            )
            .order_by(TranscriptSegment.start_time)
            .all()
        )
        segments = [
            {
                "start": row.start_time,
                "end": row.end_time,
                "text": row.text,
                "speaker": row.speaker_label,
            }
            for row in rows
        ]
    engine.dispose()
    return segments


def _store_analysis_sync(conversation_id: str, analysis: dict):
    """Store analysis result in the database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        # Check if analysis already exists
        existing = session.query(ConversationAnalysis).filter(
            ConversationAnalysis.conversation_id == uuid.UUID(conversation_id)
        ).first()

        if existing:
            # Update existing
            existing.intent = analysis.get("intent")
            existing.products = analysis.get("products", [])
            existing.budget = analysis.get("budget")
            existing.objections = analysis.get("objections", [])
            existing.competitors = analysis.get("competitors", [])
            existing.closing_attempt = analysis.get("closing_attempt", False)
            existing.outcome = analysis.get("outcome")
            existing.confidence = analysis.get("confidence")
            existing.summary = analysis.get("summary")
            existing.coaching_notes = analysis.get("coaching_notes")
        else:
            # Create new
            ca = ConversationAnalysis(
                conversation_id=uuid.UUID(conversation_id),
                intent=analysis.get("intent"),
                products=analysis.get("products", []),
                budget=analysis.get("budget"),
                objections=analysis.get("objections", []),
                competitors=analysis.get("competitors", []),
                closing_attempt=analysis.get("closing_attempt", False),
                outcome=analysis.get("outcome"),
                confidence=analysis.get("confidence"),
                summary=analysis.get("summary"),
                coaching_notes=analysis.get("coaching_notes"),
            )
            session.add(ca)

        session.commit()
        logger.info(f"[{conversation_id}] Stored conversation analysis")
    engine.dispose()


def _update_conversation_summary_sync(conversation_id: str, summary: str):
    """Update the conversation's summary field."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        session.query(Conversation).filter(
            Conversation.id == uuid.UUID(conversation_id)
        ).update({"summary": summary})
        session.commit()
    engine.dispose()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, name="analyze_conversations")
def analyze_conversations(self, recording_id: str) -> str:
    """Analyze all conversations in a recording using Llama 3.3 70B.

    For each conversation:
    1. Load transcript segments within the conversation's time range
    2. Send to LLM for analysis (intent, products, objections, outcome, etc.)
    3. Store analysis in conversation_analysis table
    4. Update conversation summary

    Returns:
        recording_id for the next pipeline stage
    """
    logger.info(f"[{recording_id}] Starting conversation analysis")
    _update_recording_status_sync(recording_id, RecordingStatus.ANALYZING)

    try:
        recording = _get_recording_sync(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        # Load all conversations
        conversations = _get_conversations_sync(recording_id)
        if not conversations:
            logger.warning(f"[{recording_id}] No conversations found — skipping analysis")
            return recording_id

        logger.info(f"[{recording_id}] Analyzing {len(conversations)} conversations")

        analyzed_count = 0
        failed_count = 0

        for conv in conversations:
            conv_id = conv["id"]
            logger.info(
                f"[{recording_id}] Analyzing conversation {conv_id} "
                f"({conv['start_time']:.1f}s - {conv['end_time']:.1f}s)"
            )

            # Get transcript segments for this conversation
            segments = _get_conversation_segments_sync(conv_id)
            if not segments:
                logger.warning(f"[{recording_id}] No segments for conversation {conv_id}")
                failed_count += 1
                continue

            # Analyze conversation
            analysis = analyze_conversation_ai(segments)
            if analysis is None:
                logger.warning(f"[{recording_id}] Analysis failed for conversation {conv_id}")
                failed_count += 1
                continue

            # Check confidence threshold before storing
            if analysis.get("confidence", 0) < MIN_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"[{recording_id}] Analysis confidence {analysis.get('confidence')}% "
                    f"below threshold {MIN_CONFIDENCE_THRESHOLD}% — skipping"
                )
                failed_count += 1
                continue

            # Store analysis
            _store_analysis_sync(conv_id, analysis)

            # Update conversation summary
            summary = analysis.get("summary", "")
            if summary:
                _update_conversation_summary_sync(conv_id, summary)

            analyzed_count += 1
            logger.info(
                f"[{recording_id}] Conversation {conv_id}: "
                f"outcome={analysis.get('outcome')}, "
                f"confidence={analysis.get('confidence')}"
            )

        logger.info(
            f"[{recording_id}] Analysis complete: "
            f"{analyzed_count} analyzed, {failed_count} failed out of {len(conversations)}"
        )

        return recording_id

    except Exception as exc:
        logger.error(f"[{recording_id}] Analysis failed: {exc}")
        if self.request.retries >= self.max_retries:

            _update_recording_status_sync(recording_id, RecordingStatus.FAILED, str(exc))
        raise self.retry(exc=exc)
