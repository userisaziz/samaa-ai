from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_brand_admin_up, require_store_manager_up
from src.database import get_db
from src.models.user import User
from src.schemas.store import StoreCreate, StoreMetricsResponse, StoreResponse
from src.services.store import create_store, get_store, get_store_metrics, list_stores

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model=list[StoreResponse])
async def get_stores(
    brand_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_store_manager_up),
):
    return await list_stores(db, brand_id=brand_id)


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_new_store(
    data: StoreCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_brand_admin_up),
):
    return await create_store(db, data)


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store_detail(
    store_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_store_manager_up),
):
    store = await get_store(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.get("/{store_id}/metrics", response_model=StoreMetricsResponse)
async def get_store_metrics_endpoint(
    store_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_store_manager_up),
):
    metrics = await get_store_metrics(db, store_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Store not found")
    return metrics
