"""CSV export service for recordings, conversations, and metrics."""
import csv
import io
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation, ConversationAnalysis
from src.models.recording import Recording
from src.models.salesperson import Salesperson


async def export_recordings_csv(
    db: AsyncSession,
    salesperson_id: str | None = None,
    status: str | None = None,
) -> str:
    """Export recordings as CSV."""
    query = select(Recording)
    if salesperson_id:
        query = query.where(Recording.salesperson_id == uuid.UUID(salesperson_id))
    if status:
        from src.models.recording import RecordingStatus
        query = query.where(Recording.status == RecordingStatus(status))

    query = query.order_by(Recording.uploaded_at.desc())
    result = await db.execute(query)
    recordings = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Salesperson ID", "Format", "Duration (s)", "File Size (bytes)",
        "Status", "Uploaded At", "Processed At", "Error Message",
    ])
    for r in recordings:
        writer.writerow([
            str(r.id), str(r.salesperson_id), r.format,
            r.duration_seconds or "", r.file_size or "",
            r.status.value if hasattr(r.status, "value") else r.status,
            str(r.uploaded_at), str(r.processed_at) if r.processed_at else "",
            r.error_message or "",
        ])
    return output.getvalue()


async def export_conversations_csv(
    db: AsyncSession,
    recording_id: str | None = None,
    salesperson_id: str | None = None,
) -> str:
    """Export conversation analyses as CSV."""
    query = (
        select(Conversation, ConversationAnalysis, Recording)
        .outerjoin(ConversationAnalysis, ConversationAnalysis.conversation_id == Conversation.id)
        .join(Recording, Recording.id == Conversation.recording_id)
    )
    if recording_id:
        query = query.where(Conversation.recording_id == uuid.UUID(recording_id))
    if salesperson_id:
        query = query.where(Recording.salesperson_id == uuid.UUID(salesperson_id))

    query = query.order_by(Conversation.start_time)
    result = await db.execute(query)
    rows = list(result.all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Conversation ID", "Recording ID", "Start Time", "End Time",
        "Segments", "Intent", "Customer Expectation", "Products", "Budget",
        "Objections", "Competitors", "Closing Attempt", "Outcome", "Loss Reason",
        "Confidence",
        "Greeting Score", "Discovery Score", "Product Knowledge Score",
        "Objection Handling Score", "Closing Score", "Summary", "Coaching Notes",
    ])
    for conv, analysis, _rec in rows:
        scores = analysis.scores or {} if analysis else {}

        # Format objections: handle both legacy strings and new structured objects
        objections_str = ""
        if analysis and analysis.objections:
            parts = []
            for obj in analysis.objections:
                if isinstance(obj, dict):
                    parts.append(f"[{obj.get('category', 'Other')}] {obj.get('issue', '')} -> {obj.get('response', '')}")
                else:
                    parts.append(str(obj))
            objections_str = "; ".join(parts)

        writer.writerow([
            str(conv.id), str(conv.recording_id),
            conv.start_time, conv.end_time, conv.segment_count,
            analysis.intent or "" if analysis else "",
            analysis.customer_expectation or "" if analysis else "",
            ", ".join(analysis.products or []) if analysis else "",
            analysis.budget or "" if analysis else "",
            objections_str,
            ", ".join(analysis.competitors or []) if analysis else "",
            analysis.closing_attempt if analysis else "",
            analysis.outcome or "" if analysis else "",
            analysis.loss_reason or "" if analysis else "",
            analysis.confidence or "" if analysis else "",
            scores.get("greeting_score", ""),
            scores.get("discovery_score", ""),
            scores.get("product_knowledge_score", ""),
            scores.get("objection_handling_score", ""),
            scores.get("closing_score", ""),
            analysis.summary or "" if analysis else "",
            analysis.coaching_notes or "" if analysis else "",
        ])
    return output.getvalue()
