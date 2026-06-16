"""Pipeline progress tracking — Real-time status updates for UI.

Provides centralized logging and status update functions that ensure
the dashboard shows exactly what's happening during pipeline execution.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def update_pipeline_progress(
    recording_id: str,
    stage_name: str,
    status: str,
    message: str = "",
    current_index: int = None,
    total_stages: int = None,
) -> None:
    """
    Updates the database with the current pipeline status.
    This ensures the UI doesn't hang and shows exactly what's happening.
    
    Args:
        recording_id: The recording UUID or string ID
        stage_name: The current stage name (e.g., "preprocess", "stt")
        status: Status label (processing, completed, failed)
        message: Human-readable status message
        current_index: Current stage index (0-based) for progress calculation
        total_stages: Total number of stages for progress calculation
    """
    # Build progress message
    if current_index is not None and total_stages is not None:
        progress_msg = f"Processing stage {current_index + 1}/{total_stages}: {stage_name}"
        if message:
            progress_msg = f"{progress_msg} — {message}"
    else:
        progress_msg = message if message else f"Stage {stage_name}: {status}"
    
    logger.info(
        f"🔄 [{recording_id}] Updating Status: {stage_name} -> {status} ({progress_msg})"
    )
    
    try:
        # Import here to avoid circular dependencies
        from src.workers.preprocessing import _update_recording_status_sync
        from src.models.recording import RecordingStatus
        
        # Map status string to RecordingStatus enum
        status_enum = RecordingStatus(status.upper()) if status.upper() in [e.value for e in RecordingStatus] else RecordingStatus.TRANSCRIBING
        
        # Update recording status in DB
        _update_recording_status_sync(recording_id, status_enum, progress_msg)
        
    except Exception as e:
        logger.error(f"Failed to update progress for {recording_id}: {e}", exc_info=True)


def log_stage_start(
    recording_id: str,
    stage_name: str,
    total_stages: int,
    current_index: int,
) -> None:
    """Log that a stage is starting and update UI progress."""
    msg = f"Starting stage {current_index + 1}/{total_stages}: {stage_name}"
    update_pipeline_progress(
        recording_id,
        stage_name,
        "processing",
        msg,
        current_index,
        total_stages,
    )


def log_stage_complete(
    recording_id: str,
    stage_name: str,
    total_stages: int = None,
    current_index: int = None,
) -> None:
    """Log that a stage completed successfully and update UI progress."""
    if current_index is not None and total_stages is not None:
        msg = f"Completed stage {current_index + 1}/{total_stages}: {stage_name}"
    else:
        msg = "Stage finished successfully"
    
    update_pipeline_progress(
        recording_id,
        stage_name,
        "completed",
        msg,
        current_index,
        total_stages,
    )


def log_stage_error(
    recording_id: str,
    stage_name: str,
    error_msg: str,
    total_stages: int = None,
    current_index: int = None,
) -> None:
    """Log that a stage failed and update UI with error details."""
    if current_index is not None and total_stages is not None:
        msg = f"Failed at stage {current_index + 1}/{total_stages}: {stage_name} — {error_msg}"
    else:
        msg = f"Stage failed: {error_msg}"
    
    update_pipeline_progress(
        recording_id,
        stage_name,
        "failed",
        msg,
        current_index,
        total_stages,
    )


def log_pipeline_complete(
    recording_id: str,
    total_stages: int,
) -> None:
    """Log that the entire pipeline completed successfully."""
    msg = f"Pipeline completed all {total_stages} stages successfully"
    logger.info(f"✅ [{recording_id}] {msg}")
    
    try:
        from src.workers.preprocessing import _update_recording_status_sync
        from src.models.recording import RecordingStatus
        
        _update_recording_status_sync(
            recording_id,
            RecordingStatus.COMPLETED,
            msg,
        )
    except Exception as e:
        logger.error(f"Failed to update final completion status for {recording_id}: {e}", exc_info=True)


def log_pipeline_halted(
    recording_id: str,
    stage_name: str,
    error_msg: str,
    retry_count: int,
    max_retries: int,
) -> None:
    """Log that the pipeline halted due to repeated failures."""
    msg = (
        f"Pipeline halted at stage '{stage_name}' after {retry_count} retries "
        f"(max: {max_retries}). Manual intervention required."
    )
    logger.error(f"🛑 [{recording_id}] {msg}")
    
    try:
        from src.workers.preprocessing import _update_recording_status_sync
        from src.models.recording import RecordingStatus
        
        _update_recording_status_sync(
            recording_id,
            RecordingStatus.FAILED,
            msg,
        )
    except Exception as e:
        logger.error(f"Failed to update halted status for {recording_id}: {e}", exc_info=True)
