import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.brand import Brand
from src.schemas.brand import BrandCreate, BrandUpdate


async def list_brands(db: AsyncSession) -> list[Brand]:
    result = await db.execute(select(Brand).order_by(Brand.created_at.desc()))
    return list(result.scalars().all())


async def get_brand(db: AsyncSession, brand_id: str) -> Brand | None:
    result = await db.execute(select(Brand).where(Brand.id == uuid.UUID(brand_id)))
    return result.scalar_one_or_none()


async def create_brand(db: AsyncSession, data: BrandCreate) -> Brand:
    brand = Brand(name=data.name, description=data.description)
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return brand


async def update_brand(db: AsyncSession, brand_id: str, data: BrandUpdate) -> Brand | None:
    brand = await get_brand(db, brand_id)
    if not brand:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    await db.flush()
    await db.refresh(brand)
    return brand
