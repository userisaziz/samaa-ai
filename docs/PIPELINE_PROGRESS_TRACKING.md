# Pipeline Progress Tracking System

## Overview

The pipeline progress tracking system provides real-time status updates to the UI during pipeline execution. It ensures the dashboard never hangs and always shows exactly what stage is processing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Pipeline Stage (pipeline.py)                               │
│  ┌──────────────────────────────────────────────┐           │
│  │ log_stage_start()                             │           │
│  │   ↓                                           │           │
│  │ Execute stage function                        │           │
│  │   ↓                                           │           │
│  │ log_stage_complete() or log_stage_error()    │           │
│  └──────────────────────────────────────────────┘           │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────┐           │
│  │ pipeline_progress.py                          │           │
│  │ update_pipeline_progress()                    │           │
│  │   ↓                                           │           │
│  │ _update_recording_status_sync()               │           │
│  └──────────────────────────────────────────────┘           │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────┐           │
│  │ Database (Recording table)                    │           │
│  │ - status                                      │           │
│  │ - error_message                               │           │
│  │ - pipeline_state (JSONB)                      │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Frontend Dashboard                                          │
│  - Polls /recordings/{id}/status                             │
│  - Shows real-time progress                                  │
│  - Displays error messages                                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Functions

### `update_pipeline_progress()`

Core function that updates the database with current pipeline status.

```python
update_pipeline_progress(
    recording_id="uuid-string",
    stage_name="stt",
    status="processing",  # or "completed", "failed"
    message="Transcribing audio...",
    current_index=1,
    total_stages=9,
)
```

**Parameters:**
- `recording_id`: Recording UUID
- `stage_name`: Stage identifier (e.g., "preprocess", "stt", "diarization")
- `status`: Status string ("processing", "completed", "failed")
- `message`: Human-readable status message
- `current_index`: Current stage index (0-based) for progress calculation
- `total_stages`: Total number of stages

### `log_stage_start()`

Logs that a stage is starting and updates UI progress.

```python
log_stage_start(
    recording_id="uuid",
    stage_name="stt",
    total_stages=9,
    current_index=1,
)
```

**Output:** `🔄 [uuid] Updating Status: stt -> processing (Starting stage 2/9: stt)`

### `log_stage_complete()`

Logs successful stage completion.

```python
log_stage_complete(
    recording_id="uuid",
    stage_name="stt",
    total_stages=9,
    current_index=1,
)
```

**Output:** `🔄 [uuid] Updating Status: stt -> completed (Completed stage 2/9: stt)`

### `log_stage_error()`

Logs stage failure with error details.

```python
log_stage_error(
    recording_id="uuid",
    stage_name="stt",
    error_msg="gRPC timeout after 300s",
    total_stages=9,
    current_index=1,
)
```

**Output:** `🔄 [uuid] Updating Status: stt -> failed (Failed at stage 2/9: stt — gRPC timeout after 300s)`

### `log_pipeline_complete()`

Logs entire pipeline completion.

```python
log_pipeline_complete(
    recording_id="uuid",
    total_stages=9,
)
```

**Output:** `✅ [uuid] Pipeline completed all 9 stages successfully`

### `log_pipeline_halted()`

Logs pipeline halt after retry exhaustion.

```python
log_pipeline_halted(
    recording_id="uuid",
    stage_name="stt",
    error_msg="gRPC timeout",
    retry_count=3,
    max_retries=3,
)
```

**Output:** `🛑 [uuid] Pipeline halted at stage 'stt' after 3 retries (max: 3). Manual intervention required.`

## Integration in Pipeline

The progress tracking is automatically integrated into `pipeline.py`:

```python
def run_stage(recording_id, pipeline_version, stage_index, force_rerun=False):
    # 1. Log stage start
    log_stage_start(recording_id, stage_name, len(STAGES), stage_index)
    
    try:
        # 2. Execute stage
        func(recording_id)
        
        # 3. Log completion
        log_stage_complete(recording_id, stage_name, len(STAGES), stage_index)
        
    except Exception as e:
        # 4. Log error
        log_stage_error(recording_id, stage_name, str(e), len(STAGES), stage_index)
        raise
```

## Database Updates

Each progress update writes to the Recording model:

```python
Recording {
    id: UUID
    status: RecordingStatus.TRANSCRIBING  # Current stage
    error_message: "Starting stage 2/9: stt"  # Progress message
    pipeline_state: {  # JSONB
        "current_stage": "stt",
        "completed_stages": ["preprocess"],
        "stage_timestamps": {
            "preprocess": "2026-06-15T10:30:00Z"
        },
        "retry_count": {"stt": 0}
    }
}
```

## Frontend Consumption

The frontend polls the status endpoint:

```typescript
// Poll every 2 seconds
const { data } = useQuery({
  queryKey: ['recording-status', recordingId],
  queryFn: () => fetch(`/api/v1/recordings/${recordingId}/status`),
  refetchInterval: 2000,
})

// Display in UI
<ProgressBadge 
  status={data.status} 
  message={data.error_message}
/>
```

## Benefits

✅ **No UI hanging** — Database updates happen synchronously at each stage boundary  
✅ **Real-time progress** — Shows "Stage 3/9: diarization" instead of just "Processing"  
✅ **Error visibility** — Detailed error messages stored in `error_message` field  
✅ **Retry tracking** — Retry counts visible in pipeline_state JSONB  
✅ **Idempotent** — Safe to call multiple times; no side effects  
✅ **Failure-safe** — Try/except around DB updates prevents cascade failures  

## Pipeline Stages

The 9 pipeline stages tracked:

1. **preprocess** — Audio format conversion, normalization, VAD filtering
2. **stt** — Speech-to-text transcription (Deepgram/NVIDIA Riva)
3. **diarization** — Speaker segmentation (pyannote.audio)
4. **turns** — Conversation turn construction
5. **roles** — Speaker role classification (salesperson/customer)
6. **segmentation** — Conversation segmentation by silence gaps
7. **extract-audio** — Per-conversation audio clip extraction
8. **analyze** — AI coaching analysis (LLM-based)
9. **scoring** — Salesperson performance scoring

## Troubleshooting

### UI Still Shows "Processing"

Check logs for progress updates:
```bash
grep "🔄" .logs/celery.log
```

### Database Not Updating

Verify `_update_recording_status_sync` is working:
```python
from src.workers.preprocessing import _update_recording_status_sync
from src.models.recording import RecordingStatus

_update_recording_status_sync("recording-uuid", RecordingStatus.TRANSCRIBING, "Test message")
```

### Missing Stage Logs

Ensure `log_stage_start()` is called **before** stage execution, not after.
