"""Conversation segmentation worker — placeholder for Sprint 2."""
import logging
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def segment_conversations(self, recording_id: str) -> str:
    """Segment recording into discrete conversations."""
    logger.info(f"Segmenting recording {recording_id}")
    # TODO Sprint 2: Apply segmentation rules
    return recording_id
