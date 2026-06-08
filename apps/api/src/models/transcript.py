import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recordings.id"), nullable=False, index=True
    )
    speaker_label: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)

    # Relationships
    recording: Mapped["Recording"] = relationship(
        "Recording", back_populates="transcript_segments"
    )
