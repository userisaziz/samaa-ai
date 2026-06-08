from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: str
    recording_id: str
    start_time: float
    end_time: float
    segment_count: int
    summary: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class ConversationAnalysisResponse(BaseModel):
    id: str
    conversation_id: str
    intent: str | None = None
    products: list[str] | None = None
    budget: str | None = None
    objections: list[str] | None = None
    competitors: list[str] | None = None
    closing_attempt: bool = False
    outcome: str | None = None
    confidence: int | None = None
    scores: dict | None = None
    summary: str | None = None
    coaching_notes: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
