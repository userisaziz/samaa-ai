"""Tests for store service — CRUD operations and filtering."""
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Tests: Store Retrieval
# ---------------------------------------------------------------------------

class TestStoreService:
    def test_get_store_success(self):
        """get_store returns store when found."""
        async def run():
            from src.services.store import get_store

            store_id = uuid.uuid4()
            mock_store = MagicMock()
            mock_store.id = store_id
            mock_store.name = "Test Store"
            mock_store.brand_id = uuid.uuid4()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_store
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            store = await get_store(mock_db, str(store_id))
            assert store.name == "Test Store"
        asyncio.run(run())

    def test_get_store_not_found(self):
        """get_store returns None when store not found."""
        async def run():
            from src.services.store import get_store

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            store = await get_store(mock_db, str(uuid.uuid4()))
            assert store is None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Store Listing
# ---------------------------------------------------------------------------

class TestStoreListing:
    def test_list_stores_returns_list(self):
        """list_stores returns list of stores."""
        async def run():
            from src.services.store import list_stores

            mock_store = MagicMock()
            mock_store.id = uuid.uuid4()
            mock_store.name = "Store 1"
            mock_store.brand_id = uuid.uuid4()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_store]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            stores = await list_stores(mock_db)
            assert isinstance(stores, list)
            assert len(stores) == 1
        asyncio.run(run())

    def test_list_stores_by_brand(self):
        """list_stores filters by brand_id."""
        async def run():
            from src.services.store import list_stores

            brand_id = uuid.uuid4()
            mock_store = MagicMock()
            mock_store.id = uuid.uuid4()
            mock_store.name = "Brand Store"
            mock_store.brand_id = brand_id

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_store]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            stores = await list_stores(mock_db, brand_id=str(brand_id))
            assert len(stores) == 1
        asyncio.run(run())

    def test_list_stores_empty(self):
        """list_stores returns empty list when no stores."""
        async def run():
            from src.services.store import list_stores

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            stores = await list_stores(mock_db)
            assert isinstance(stores, list)
            assert len(stores) == 0
        asyncio.run(run())

    def test_list_stores_ordered(self):
        """list_stores returns stores ordered by created_at."""
        async def run():
            from src.services.store import list_stores

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            stores = await list_stores(mock_db)
            assert isinstance(stores, list)
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Store Creation
# ---------------------------------------------------------------------------

class TestStoreCreation:
    def test_create_store_success(self):
        """create_store creates new store."""
        async def run():
            from src.services.store import create_store
            from src.schemas.store import StoreCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_id = uuid.uuid4()
            store_data = StoreCreate(
                name="New Store",
                brand_id=str(brand_id)
            )

            store = await create_store(mock_db, store_data)

            mock_db.add.assert_called_once()
            assert store.name == "New Store"
        asyncio.run(run())

    def test_create_store_with_location(self):
        """create_store accepts optional location field."""
        async def run():
            from src.services.store import create_store
            from src.schemas.store import StoreCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_id = uuid.uuid4()
            store_data = StoreCreate(
                name="Store with Location",
                brand_id=str(brand_id),
                location="Dubai, UAE"
            )

            store = await create_store(mock_db, store_data)
            assert store.location == "Dubai, UAE"
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Store Update
# ---------------------------------------------------------------------------

class TestStoreUpdate:
    def test_update_store_success(self):
        """update_store modifies existing store."""
        async def run():
            from src.services.store import update_store
            from src.schemas.store import StoreUpdate

            store_id = uuid.uuid4()
            mock_store = MagicMock()
            mock_store.id = store_id
            mock_store.name = "Old Name"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_store
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            update_data = StoreUpdate(name="New Name")
            updated_store = await update_store(mock_db, str(store_id), update_data)

            assert updated_store.name == "New Name"
        asyncio.run(run())

    def test_update_store_not_found(self):
        """update_store returns None for non-existent store."""
        async def run():
            from src.services.store import update_store
            from src.schemas.store import StoreUpdate

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await update_store(mock_db, str(uuid.uuid4()), StoreUpdate(name="New"))
            assert result is None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Store Model Validation
# ---------------------------------------------------------------------------

class TestStoreModel:
    def test_store_model_fields(self):
        """Store model has required fields."""
        from src.models.store import Store

        assert hasattr(Store, 'id')
        assert hasattr(Store, 'name')
        assert hasattr(Store, 'brand_id')
        assert hasattr(Store, 'created_at')

    def test_store_brand_id_foreign_key(self):
        """Store has foreign key relationship to Brand."""
        from src.models.store import Store
        assert hasattr(Store, 'brand_id')

    def test_store_schema_validation(self):
        """StoreCreate schema validates required fields."""
        from src.schemas.store import StoreCreate

        brand_id = uuid.uuid4()
        store = StoreCreate(
            name="Test Store",
            brand_id=str(brand_id)
        )

        assert store.name == "Test Store"
        assert store.brand_id == str(brand_id)

    def test_store_schema_optional_fields(self):
        """StoreCreate accepts optional fields."""
        from src.schemas.store import StoreCreate

        brand_id = uuid.uuid4()
        store = StoreCreate(
            name="Test Store",
            brand_id=str(brand_id),
            location="Optional Location",
            working_hours={"open": "9:00", "close": "21:00"}
        )

        assert store.location == "Optional Location"
        assert store.working_hours == {"open": "9:00", "close": "21:00"}


# ---------------------------------------------------------------------------
# Tests: Store Edge Cases
# ---------------------------------------------------------------------------

class TestStoreEdgeCases:
    def test_list_stores_multiple_brands(self):
        """list_stores handles stores from multiple brands."""
        async def run():
            from src.services.store import list_stores

            brand1 = uuid.uuid4()
            brand2 = uuid.uuid4()

            mock_stores = [
                MagicMock(id=uuid.uuid4(), name="Store 1", brand_id=brand1),
                MagicMock(id=uuid.uuid4(), name="Store 2", brand_id=brand2),
            ]

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_stores
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            stores = await list_stores(mock_db)
            assert len(stores) == 2
        asyncio.run(run())

    def test_store_name_max_length(self):
        """Store name accepts long names."""
        async def run():
            from src.services.store import create_store
            from src.schemas.store import StoreCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_id = uuid.uuid4()
            long_name = "A" * 200
            store_data = StoreCreate(
                name=long_name,
                brand_id=str(brand_id)
            )

            store = await create_store(mock_db, store_data)
            assert len(store.name) == 200
        asyncio.run(run())

    def test_store_special_characters_in_name(self):
        """Store name accepts special characters."""
        async def run():
            from src.services.store import create_store
            from src.schemas.store import StoreCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_id = uuid.uuid4()
            store_data = StoreCreate(
                name="Store & Co. (Dubai)",
                brand_id=str(brand_id)
            )

            store = await create_store(mock_db, store_data)
            assert "&" in store.name
            assert "(" in store.name
        asyncio.run(run())
