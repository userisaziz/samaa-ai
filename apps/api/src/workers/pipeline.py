"""Pipeline chain orchestration for audio processing."""
from celery import chain

from src.workers.preprocessing import preprocess_audio
from src.workers.transcription import transcribe_audio
from src.workers.diarization import diarize_audio
from src.workers.segmentation import segment_conversations
from src.workers.analysis import analyze_conversations
from src.workers.scoring import score_salesperson


def start_processing_pipeline(recording_id: str):
    """Start the full audio processing pipeline for a recording."""
    processing_chain = chain(
        preprocess_audio.s(recording_id),
        transcribe_audio.s(),
        diarize_audio.s(),
        segment_conversations.s(),
        analyze_conversations.s(),
        score_salesperson.s(),
    )
    return processing_chain.apply_async()
