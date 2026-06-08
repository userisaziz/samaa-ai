import uuid
from datetime import date

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class DailyMetrics(Base):
    __tablename__ = "metrics_daily"
    __table_args__ = (
        UniqueConstraint("entity_id", "entity_type", "date", name="uq_daily_metrics"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    conversation_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class WeeklyMetrics(Base):
    __tablename__ = "metrics_weekly"
    __table_args__ = (
        UniqueConstraint("entity_id", "entity_type", "week_start", name="uq_weekly_metrics"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    conversation_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_objection: Mapped[str | None] = mapped_column(String(500), nullable=True)
