from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_salesperson_up, require_store_manager_up, require_operator_up
from src.database import get_db
from src.models.user import User
from src.schemas.salesperson import (
    SalespersonCreate,
    SalespersonPerformanceResponse,
    SalespersonResponse,
)
from src.services.salesperson import (
    create_salesperson,
    get_salesperson,
    get_salesperson_performance,
    list_salespeople,
)

router = APIRouter(prefix="/salespeople", tags=["Salespeople"])


@router.get("", response_model=list[SalespersonResponse])
async def get_salespeople(
    store_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_operator_up),
):
    return await list_salespeople(db, store_id=store_id)


@router.post("", response_model=SalespersonResponse, status_code=status.HTTP_201_CREATED)
async def create_new_salesperson(
    data: SalespersonCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_store_manager_up),
):
    return await create_salesperson(db, data)


@router.get("/{salesperson_id}", response_model=SalespersonResponse)
async def get_salesperson_detail(
    salesperson_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_operator_up),
):
    salesperson = await get_salesperson(db, salesperson_id)
    if not salesperson:
        raise HTTPException(status_code=404, detail="Salesperson not found")
    return salesperson


@router.get("/{salesperson_id}/performance", response_model=SalespersonPerformanceResponse)
async def get_salesperson_performance_endpoint(
    salesperson_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    performance = await get_salesperson_performance(db, salesperson_id)
    if not performance:
        raise HTTPException(status_code=404, detail="Salesperson not found")
    return performance
