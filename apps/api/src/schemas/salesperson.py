import uuid
from datetime import datetime

from pydantic import BaseModel


class SalespersonCreate(BaseModel):
    store_id: str
    name: str
    email: str | None = None
    role: str | None = None
    shift: str | None = None
    device_number: str | None = None


class SalespersonUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    shift: str | None = None
    device_number: str | None = None


class SalespersonResponse(BaseModel):
    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    email: str | None = None
    role: str | None = None
    shift: str | None = None
    device_number: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalespersonPerformanceResponse(BaseModel):
    salesperson_id: str
    name: str
    total_conversations: int
    avg_greeting_score: float | None = None
    avg_discovery_score: float | None = None
    avg_product_knowledge_score: float | None = None
    avg_objection_handling_score: float | None = None
    avg_closing_score: float | None = None
    avg_overall_score: float | None = None
    conversion_rate: float | None = None
