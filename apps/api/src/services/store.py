import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation, ConversationAnalysis
from src.models.recording import Recording
from src.models.salesperson import Salesperson
from src.models.store import Store
from src.schemas.store import StoreCreate, StoreMetricsResponse, StoreUpdate


async def list_stores(db: AsyncSession, brand_id: str | None = None) -> list[Store]:
    query = select(Store)
    if brand_id:
        query = query.where(Store.brand_id == uuid.UUID(brand_id))
    result = await db.execute(query.order_by(Store.created_at.desc()))
    return list(result.scalars().all())


async def get_store(db: AsyncSession, store_id: str) -> Store | None:
    result = await db.execute(select(Store).where(Store.id == uuid.UUID(store_id)))
    return result.scalar_one_or_none()


async def create_store(db: AsyncSession, data: StoreCreate) -> Store:
    store = Store(
        name=data.name,
        brand_id=uuid.UUID(data.brand_id),
        location=data.location,
        working_hours=data.working_hours,
    )
    db.add(store)
    await db.flush()
    await db.refresh(store)
    return store


async def update_store(db: AsyncSession, store_id: str, data: StoreUpdate) -> Store | None:
    store = await get_store(db, store_id)
    if not store:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store, key, value)
    await db.flush()
    await db.refresh(store)
    return store


async def get_store_metrics(db: AsyncSession, store_id: str) -> StoreMetricsResponse | None:
    store = await get_store(db, store_id)
    if not store:
        return None

    sid = uuid.UUID(store_id)

    # Count salespeople
    sp_count = await db.execute(
        select(func.count()).select_from(Salesperson).where(Salesperson.store_id == sid)
    )
    total_salespeople = sp_count.scalar() or 0

    # Count recordings
    rec_count = await db.execute(
        select(func.count()).select_from(Recording).where(Recording.salesperson_id.in_(
            select(Salesperson.id).where(Salesperson.store_id == sid)
        ))
    )
    total_recordings = rec_count.scalar() or 0

    # Count conversations
    conv_count = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.recording_id.in_(
            select(Recording.id).where(Recording.salesperson_id.in_(
                select(Salesperson.id).where(Salesperson.store_id == sid)
            ))
        ))
    )
    total_conversations = conv_count.scalar() or 0

    return StoreMetricsResponse(
        store_id=store_id,
        name=store.name,
        total_salespeople=total_salespeople,
        total_recordings=total_recordings,
        total_conversations=total_conversations,
    )
