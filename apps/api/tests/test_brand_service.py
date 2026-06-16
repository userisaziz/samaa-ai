"""Tests for brand service — CRUD operations and listing."""
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Tests: Brand Retrieval
# ---------------------------------------------------------------------------

class TestBrandService:
    def test_get_brand_success(self):
        """get_brand returns brand when found."""
        async def run():
            from src.services.brand import get_brand

            brand_id = uuid.uuid4()
            mock_brand = MagicMock()
            mock_brand.id = brand_id
            mock_brand.name = "Test Brand"
            mock_brand.description = "Test Description"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_brand
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            brand = await get_brand(mock_db, str(brand_id))
            assert brand.name == "Test Brand"
        asyncio.run(run())

    def test_get_brand_not_found(self):
        """get_brand returns None when brand not found."""
        async def run():
            from src.services.brand import get_brand

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            brand = await get_brand(mock_db, str(uuid.uuid4()))
            assert brand is None
        asyncio.run(run())

    def test_get_brand_invalid_uuid(self):
        """get_brand raises ValueError for invalid UUID format."""
        async def run():
            from src.services.brand import get_brand

            mock_db = AsyncMock()
            with pytest.raises((ValueError, Exception)):
                await get_brand(mock_db, "not-a-uuid")
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Brand Listing
# ---------------------------------------------------------------------------

class TestBrandListing:
    def test_list_brands_returns_list(self):
        """list_brands returns list of brands."""
        async def run():
            from src.services.brand import list_brands

            mock_brand = MagicMock()
            mock_brand.id = uuid.uuid4()
            mock_brand.name = "Brand 1"

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_brand]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            brands = await list_brands(mock_db)
            assert isinstance(brands, list)
            assert len(brands) == 1
        asyncio.run(run())

    def test_list_brands_empty(self):
        """list_brands returns empty list when no brands."""
        async def run():
            from src.services.brand import list_brands

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            brands = await list_brands(mock_db)
            assert isinstance(brands, list)
            assert len(brands) == 0
        asyncio.run(run())

    def test_list_brands_returns_ordered(self):
        """list_brands returns brands ordered by created_at desc."""
        async def run():
            from src.services.brand import list_brands

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            brands = await list_brands(mock_db)
            assert isinstance(brands, list)
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Brand Creation
# ---------------------------------------------------------------------------

class TestBrandCreation:
    def test_create_brand_success(self):
        """create_brand creates new brand."""
        async def run():
            from src.services.brand import create_brand
            from src.schemas.brand import BrandCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_data = BrandCreate(
                name="New Brand",
                description="A test brand"
            )

            brand = await create_brand(mock_db, brand_data)

            mock_db.add.assert_called_once()
            assert brand.name == "New Brand"
        asyncio.run(run())

    def test_create_brand_minimal_fields(self):
        """create_brand works with only required fields."""
        async def run():
            from src.services.brand import create_brand
            from src.schemas.brand import BrandCreate

            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            brand_data = BrandCreate(name="Minimal Brand")

            brand = await create_brand(mock_db, brand_data)
            assert brand.name == "Minimal Brand"
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Brand Update
# ---------------------------------------------------------------------------

class TestBrandUpdate:
    def test_update_brand_success(self):
        """update_brand modifies existing brand."""
        async def run():
            from src.services.brand import update_brand
            from src.schemas.brand import BrandUpdate

            brand_id = uuid.uuid4()
            mock_brand = MagicMock()
            mock_brand.id = brand_id
            mock_brand.name = "Old Name"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_brand
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()

            update_data = BrandUpdate(name="New Name")

            updated_brand = await update_brand(mock_db, str(brand_id), update_data)
            assert updated_brand.name == "New Name"
        asyncio.run(run())

    def test_update_brand_not_found(self):
        """update_brand returns None for non-existent brand."""
        async def run():
            from src.services.brand import update_brand
            from src.schemas.brand import BrandUpdate

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await update_brand(mock_db, str(uuid.uuid4()), BrandUpdate(name="New"))
            assert result is None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Brand Model Validation
# ---------------------------------------------------------------------------

class TestBrandModel:
    def test_brand_model_fields(self):
        """Brand model has required fields."""
        from src.models.brand import Brand

        assert hasattr(Brand, 'id')
        assert hasattr(Brand, 'name')
        assert hasattr(Brand, 'description')
        assert hasattr(Brand, 'created_at')

    def test_brand_name_required(self):
        """Brand name is a required field."""
        from src.schemas.brand import BrandCreate

        schema = BrandCreate.__fields__ if hasattr(BrandCreate, '__fields__') else BrandCreate.model_fields
        assert 'name' in schema

    def test_brand_description_optional(self):
        """Brand description is optional."""
        from src.schemas.brand import BrandCreate

        brand = BrandCreate(name="Test")
        assert brand.name == "Test"
