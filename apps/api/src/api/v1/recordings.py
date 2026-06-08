import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_salesperson_up
from src.database import get_db
from src.models.user import User
from src.schemas.recording import (
    ConversationSummaryResponse,
    RecordingResponse,
    RecordingStatusResponse,
    TranscriptSegmentResponse,
)
from src.services.recording import (
    create_recording,
    get_conversations,
    get_recording,
    get_transcript,
)
from src.storage.local import get_storage
from src.workers.pipeline import start_processing_pipeline

ALLOWED_FORMATS = {"wav", "mp3", "m4a"}
ALLOWED_MIME_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/mp3"}

router = APIRouter(prefix="/recordings", tags=["Recordings"])


@router.post("/upload", response_model=RecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    file: UploadFile = File(...),
    salesperson_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Allowed: {', '.join(ALLOWED_FORMATS)}",
        )

    # Read file
    file_data = await file.read()
    file_size = len(file_data)

    # Store file
    storage = get_storage()
    file_key = f"recordings/{uuid.uuid4()}/{file.filename}"
    file_url = await storage.upload(file_data, file_key)

    # Create recording record
    recording = await create_recording(
        db=db,
        salesperson_id=salesperson_id,
        file_url=file_url,
        file_size=file_size,
        duration_seconds=None,  # Will be determined during preprocessing
        format=ext.upper(),
    )

    # Enqueue Celery processing pipeline
    try:
        start_processing_pipeline(str(recording.id))
    except Exception as e:
        # If Redis/Celery is unavailable, recording stays in UPLOADED status
        # Can be re-triggered later via re-process endpoint
        import logging
        logging.getLogger(__name__).warning(f"Could not enqueue pipeline: {e}")

    return recording


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording_detail(
    recording_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    recording = await get_recording(db, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording


@router.get("/{recording_id}/status", response_model=RecordingStatusResponse)
async def get_recording_status(
    recording_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    recording = await get_recording(db, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return RecordingStatusResponse(
        id=str(recording.id),
        status=recording.status.value,
        error_message=recording.error_message,
    )


@router.get("/{recording_id}/transcript", response_model=list[TranscriptSegmentResponse])
async def get_recording_transcript(
    recording_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    return await get_transcript(db, recording_id)


@router.get("/{recording_id}/conversations", response_model=list[ConversationSummaryResponse])
async def get_recording_conversations(
    recording_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    return await get_conversations(db, recording_id)
