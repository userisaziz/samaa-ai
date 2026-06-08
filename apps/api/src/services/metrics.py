"""Metrics aggregation service — computes daily/weekly metrics for entities."""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation, ConversationAnalysis
from src.models.metrics import DailyMetrics, WeeklyMetrics
from src.models.recording import Recording


async def get_entity_daily_metrics(
    db: AsyncSession,
    entity_id: str,
    entity_type: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DailyMetrics]:
    """Get daily metrics for an entity within a date range."""
    query = select(DailyMetrics).where(
        DailyMetrics.entity_id == uuid.UUID(entity_id),
        DailyMetrics.entity_type == entity_type,
    )
    if start_date:
        query = query.where(DailyMetrics.date >= start_date)
    if end_date:
        query = query.where(DailyMetrics.date <= end_date)

    query = query.order_by(DailyMetrics.date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_entity_weekly_metrics(
    db: AsyncSession,
    entity_id: str,
    entity_type: str,
    weeks: int = 12,
) -> list[WeeklyMetrics]:
    """Get weekly metrics for an entity for the last N weeks."""
    start_date = date.today() - timedelta(weeks=weeks)
    query = select(WeeklyMetrics).where(
        WeeklyMetrics.entity_id == uuid.UUID(entity_id),
        WeeklyMetrics.entity_type == entity_type,
        WeeklyMetrics.week_start >= start_date,
    ).order_by(WeeklyMetrics.week_start.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_store_metrics_summary(
    db: AsyncSession,
    store_id: str,
) -> dict:
    """Get aggregated metrics summary for a store."""
    from src.models.salesperson import Salesperson

    # Get salespeople in this store
    sp_result = await db.execute(
        select(Salesperson.id).where(Salesperson.store_id == uuid.UUID(store_id))
    )
    sp_ids = [row[0] for row in sp_result.all()]

    if not sp_ids:
        return {
            "total_salespeople": 0,
            "total_recordings": 0,
            "total_conversations": 0,
            "avg_performance_score": None,
            "conversion_rate": None,
            "top_objection": None,
        }

    # Count recordings
    rec_result = await db.execute(
        select(func.count(Recording.id)).where(Recording.salesperson_id.in_(sp_ids))
    )
    total_recordings = rec_result.scalar() or 0

    # Count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.recording_id.in_(
                select(Recording.id).where(Recording.salesperson_id.in_(sp_ids))
            )
        )
    )
    total_conversations = conv_result.scalar() or 0

    # Average confidence score
    avg_result = await db.execute(
        select(func.avg(ConversationAnalysis.confidence)).join(Conversation).where(
            Conversation.recording_id.in_(
                select(Recording.id).where(Recording.salesperson_id.in_(sp_ids))
            )
        )
    )
    avg_score = avg_result.scalar()

    # Conversion rate
    sale_count_result = await db.execute(
        select(func.count(ConversationAnalysis.id)).join(Conversation).where(
            Conversation.recording_id.in_(
                select(Recording.id).where(Recording.salesperson_id.in_(sp_ids))
            ),
            ConversationAnalysis.outcome == "SALE_MADE",
        )
    )
    sale_count = sale_count_result.scalar() or 0
    conversion_rate = (sale_count / total_conversations * 100) if total_conversations > 0 else None

    return {
        "total_salespeople": len(sp_ids),
        "total_recordings": total_recordings,
        "total_conversations": total_conversations,
        "avg_performance_score": round(float(avg_score), 1) if avg_score else None,
        "conversion_rate": round(conversion_rate, 1) if conversion_rate is not None else None,
        "top_objection": None,  # TODO: compute from aggregated objections
    }


async def get_salesperson_performance_summary(
    db: AsyncSession,
    salesperson_id: str,
) -> dict:
    """Get performance summary for a salesperson."""
    # Get recordings
    rec_result = await db.execute(
        select(Recording.id).where(Recording.salesperson_id == uuid.UUID(salesperson_id))
    )
    rec_ids = [row[0] for row in rec_result.all()]

    if not rec_ids:
        return {
            "total_conversations": 0,
            "avg_scores": {},
            "conversion_rate": None,
        }

    # Count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.recording_id.in_(rec_ids)
        )
    )
    total_conversations = conv_result.scalar() or 0

    # Get average scores per dimension
    # Scores are stored as JSONB in conversation_analysis.scores
    analyses_result = await db.execute(
        select(ConversationAnalysis.scores).join(Conversation).where(
            Conversation.recording_id.in_(rec_ids),
            ConversationAnalysis.scores.isnot(None),
        )
    )
    score_records = [row[0] for row in analyses_result.all() if row[0]]

    avg_scores = {}
    if score_records:
        dimensions = [
            "greeting_score",
            "discovery_score",
            "product_knowledge_score",
            "objection_handling_score",
            "closing_score",
        ]
        for dim in dimensions:
            values = [s.get(dim) for s in score_records if s.get(dim) is not None]
            if values:
                avg_scores[dim] = round(sum(values) / len(values), 1)
            else:
                avg_scores[dim] = None

    # Conversion rate
    sale_count_result = await db.execute(
        select(func.count(ConversationAnalysis.id)).join(Conversation).where(
            Conversation.recording_id.in_(rec_ids),
            ConversationAnalysis.outcome == "SALE_MADE",
        )
    )
    sale_count = sale_count_result.scalar() or 0
    conversion_rate = (sale_count / total_conversations * 100) if total_conversations > 0 else None

    return {
        "total_conversations": total_conversations,
        "avg_scores": avg_scores,
        "conversion_rate": round(conversion_rate, 1) if conversion_rate is not None else None,
    }
