import uuid
from datetime import datetime

from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    description: str | None = None


class BrandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class BrandResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
