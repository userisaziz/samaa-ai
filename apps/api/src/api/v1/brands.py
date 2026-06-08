from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_brand_admin_up, require_super_admin
from src.database import get_db
from src.models.user import User
from src.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from src.services.brand import create_brand, get_brand, list_brands, update_brand

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("", response_model=list[BrandResponse])
async def get_brands(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_super_admin),
):
    return await list_brands(db)


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_new_brand(
    data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_brand_admin_up),
):
    return await create_brand(db, data)


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand_detail(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_brand_admin_up),
):
    brand = await get_brand(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand_detail(
    brand_id: str,
    data: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_super_admin),
):
    brand = await update_brand(db, brand_id, data)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand
