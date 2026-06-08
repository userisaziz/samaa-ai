import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation
from src.models.recording import Recording, RecordingStatus
from src.models.transcript import TranscriptSegment
from src.schemas.recording import RecordingResponse


async def get_recording(db: AsyncSession, recording_id: str) -> Recording | None:
    result = await db.execute(
        select(Recording).where(Recording.id == uuid.UUID(recording_id))
    )
    return result.scalar_one_or_none()


async def create_recording(
    db: AsyncSession,
    salesperson_id: str,
    file_url: str,
    file_size: int,
    duration_seconds: int | None,
    format: str,
) -> Recording:
    recording = Recording(
        salesperson_id=uuid.UUID(salesperson_id),
        file_url=file_url,
        file_size=file_size,
        duration_seconds=duration_seconds,
        format=format,
        status=RecordingStatus.UPLOADED,
    )
    db.add(recording)
    await db.flush()
    await db.refresh(recording)
    return recording


async def update_recording_status(
    db: AsyncSession, recording_id: str, status: RecordingStatus, error_message: str | None = None
) -> Recording | None:
    recording = await get_recording(db, recording_id)
    if not recording:
        return None
    recording.status = status
    if error_message:
        recording.error_message = error_message
    await db.flush()
    await db.refresh(recording)
    return recording


async def get_transcript(db: AsyncSession, recording_id: str) -> list[TranscriptSegment]:
    result = await db.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.recording_id == uuid.UUID(recording_id))
        .order_by(TranscriptSegment.start_time)
    )
    return list(result.scalars().all())


async def get_conversations(db: AsyncSession, recording_id: str) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.recording_id == uuid.UUID(recording_id))
        .order_by(Conversation.start_time)
    )
    return list(result.scalars().all())
