"""Audio preprocessing worker — placeholder for Sprint 2."""
import logging

from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def preprocess_audio(self, recording_id: str) -> str:
    """Preprocess raw audio: convert to mono, normalize, resample to 16kHz."""
    logger.info(f"Preprocessing recording {recording_id}")
    # TODO Sprint 2: Implement actual preprocessing
    # - Convert to mono
    # - Normalize volume
    # - Resample to 16kHz
    # - Detect silence gaps > 30s
    # - Update recording status to TRANSCRIBING
    return recording_id
