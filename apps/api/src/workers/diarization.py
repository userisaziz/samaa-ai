"""Speaker diarization worker — placeholder for Sprint 2."""
import logging
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def diarize_audio(self, recording_id: str) -> str:
    """Diarize speakers using NVIDIA NeMo."""
    logger.info(f"Diarizing recording {recording_id}")
    # TODO Sprint 2: Call NVIDIA NIM NeMo Diarization API
    return recording_id
