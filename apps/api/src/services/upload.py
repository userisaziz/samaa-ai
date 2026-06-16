"""Upload service with pre-signed URL support for direct-to-storage uploads."""
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.recording import Recording, RecordingStatus
from src.storage.local import get_storage
from src.config import settings

logger = logging.getLogger(__name__)


async def generate_presigned_upload_url(
    db: AsyncSession,
    filename: str,
    content_type: str,
    salesperson_id: str,
    recorded_at: str | None = None,
) -> dict:
    """Generate a pre-signed URL for direct browser-to-R2 upload.
    
    Returns:
        dict with:
        - upload_url: Pre-signed PUT URL for direct upload
        - recording_id: UUID of the recording record
        - file_key: Storage key in R2
        - file_url: URL/path for the uploaded file (returned after upload)
    """
    from datetime import datetime
    from sqlalchemy import select
    from src.models.salesperson import Salesperson
    from src.models.store import Store
    
    # Generate unique recording ID
    recording_id = uuid.uuid4()
    file_ext = Path(filename).suffix
    
    # Resolve brand/store hierarchy for a clear, scannable file path
    today = datetime.now().strftime("%Y%m%d")
    sp_uuid = uuid.UUID(salesperson_id)
    sp_short = str(sp_uuid)[:8]
    
    brand_short = "unknown"
    store_short = "unknown"
    
    sp_stmt = select(Salesperson).where(Salesperson.id == sp_uuid)
    sp_result = await db.execute(sp_stmt)
    salesperson = sp_result.scalar_one_or_none()
    
    if salesperson:
        store_short = str(salesperson.store_id)[:8]
        store_stmt = select(Store).where(Store.id == salesperson.store_id)
        store_result = await db.execute(store_stmt)
        store = store_result.scalar_one_or_none()
        if store:
            brand_short = str(store.brand_id)[:8]
    
    # Human-readable path: recordings/{brand_prefix}-{store_prefix}-{sp_prefix}/{date}-{short_id}.ext
    short_id = str(recording_id)[:8]
    file_key = f"recordings/{brand_short}-{store_short}-{sp_short}/{today}-{short_id}{file_ext}"
    
    # Create recording record in PENDING_UPLOAD state
    recording = Recording(
        id=recording_id,
        salesperson_id=sp_uuid,
        file_url=file_key,
        file_size=None,
        duration_seconds=None,
        format=content_type,
        status=RecordingStatus.PENDING_UPLOAD,
        recorded_at=datetime.fromisoformat(recorded_at) if recorded_at else None,
    )
    db.add(recording)
    await db.flush()
    await db.refresh(recording)
    
    # Generate pre-signed upload URL
    storage = get_storage()
    upload_url = await storage.generate_presigned_upload_url(
        key=file_key,
        content_type=content_type,
        expires_in=3600,
    )
    
    logger.info(
        "Generated presigned upload URL for recording %s (salesperson: %s) key=%s",
        recording_id,
        salesperson_id,
        file_key,
    )
    
    return {
        "upload_url": upload_url,
        "recording_id": str(recording_id),
        "file_key": file_key,
    }


async def confirm_upload(
    db: AsyncSession,
    recording_id: str,
    file_size: int | None = None,
) -> Recording:
    """Confirm that a file has been uploaded to R2 and mark it as UPLOADED.

    In ``pipeline_mode=full`` (dev/local) the processing pipeline is
    auto-enqueued. In ``pipeline_mode=cloud-only`` (GCP Cloud Run) the
    recording stops at UPLOADED — the pipeline is started later from a
    local machine that shares the same database.
    """
    from sqlalchemy import select

    # Get the recording using proper ORM query
    stmt = select(Recording).where(Recording.id == uuid.UUID(recording_id))
    result = await db.execute(stmt)
    recording = result.scalar_one_or_none()

    if not recording:
        raise ValueError(f"Recording {recording_id} not found")

    if recording.status != RecordingStatus.PENDING_UPLOAD:
        raise ValueError(
            f"Recording is in {recording.status.value} state, expected PENDING_UPLOAD"
        )

    # Update recording status and metadata
    recording.status = RecordingStatus.UPLOADED
    if file_size:
        recording.file_size = file_size

    await db.flush()
    await db.refresh(recording)

    # Only auto-enqueue pipeline when running in full mode (dev/local).
    # cloud-only mode: pipeline is triggered manually from local machine.
    if settings.pipeline_mode == "full":
        from src.workers.pipeline import enqueue_first_stage
        try:
            enqueue_first_stage(str(recording.id))
            logger.info(
                "Confirmed upload and started pipeline for recording %s",
                recording_id,
            )
        except Exception as e:
            logger.error(
                "Failed to enqueue pipeline for recording %s: %s",
                recording_id,
                e,
            )
            # Don't raise — the upload was successful, pipeline can be retried manually
    else:
        logger.info(
            "Confirmed upload for recording %s (pipeline_mode=%s, no auto-enqueue)",
            recording_id,
            settings.pipeline_mode,
        )

    return recording
