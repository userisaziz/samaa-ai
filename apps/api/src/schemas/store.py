from pydantic import BaseModel


class StoreCreate(BaseModel):
    name: str
    brand_id: str
    location: str | None = None
    working_hours: dict | None = None


class StoreUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    working_hours: dict | None = None


class StoreResponse(BaseModel):
    id: str
    brand_id: str
    name: str
    location: str | None = None
    working_hours: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class StoreMetricsResponse(BaseModel):
    store_id: str
    name: str
    total_salespeople: int
    total_recordings: int
    total_conversations: int
    avg_performance_score: float | None = None
    conversion_rate: float | None = None
    top_objection: str | None = None
