from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    description: str | None = None


class BrandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class BrandResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
