import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: uuid.UUID
    recording_id: uuid.UUID
    start_time: float
    end_time: float
    segment_count: int
    summary: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationAnalysisResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    intent: str | None = None
    customer_expectation: str | None = None
    products: list[str] | None = None
    budget: str | None = None
    objections: list[Any] | None = None
    competitors: list[str] | None = None
    closing_attempt: bool = False
    outcome: str | None = None
    loss_reason: str | None = None
    confidence: int | None = None
    scores: dict | None = None
    summary: str | None = None
    coaching_notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
