from pydantic import BaseModel


class RecordingResponse(BaseModel):
    id: str
    salesperson_id: str
    file_url: str
    file_size: int | None = None
    duration_seconds: int | None = None
    format: str
    status: str
    error_message: str | None = None
    uploaded_at: str
    processed_at: str | None = None

    model_config = {"from_attributes": True}


class RecordingStatusResponse(BaseModel):
    id: str
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}


class TranscriptSegmentResponse(BaseModel):
    id: str
    recording_id: str
    speaker_label: str
    start_time: float
    end_time: float
    text: str

    model_config = {"from_attributes": True}


class ConversationSummaryResponse(BaseModel):
    id: str
    recording_id: str
    start_time: float
    end_time: float
    segment_count: int
    summary: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
