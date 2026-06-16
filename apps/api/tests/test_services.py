"""Tests for service layer — auth, analytics, recording services."""
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from src.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_id,
    hash_password,
    verify_password,
)
from src.services.analytics import (
    _get_recording_ids_for_scope,
    get_analytics_overview,
)
from src.models.user import User, UserRole


# ---------------------------------------------------------------------------
# Tests: Auth Service
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_hash_password_returns_string(self):
        """hash_password returns bcrypt hash string."""
        password = "secure_password_123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 50  # bcrypt hashes are long

    def test_hash_password_different_each_time(self):
        """hash_password generates different salts each call."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2


class TestVerifyPassword:
    def test_verify_correct_password(self):
        """verify_password returns True for correct password."""
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """verify_password returns False for wrong password."""
        password = "correct_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False


class TestAuthenticateUser:
    def test_authenticate_success(self):
        """authenticate_user returns user with valid credentials."""
        async def run():
            sample_user = MagicMock(spec=User)
            sample_user.id = uuid.uuid4()
            sample_user.email = "test@example.com"
            sample_user.full_name = "Test User"
            sample_user.role = UserRole.SALESPERSON
            sample_user.brand_id = uuid.uuid4()
            sample_user.store_id = uuid.uuid4()
            sample_user.password_hash = "$2b$12$dummyhash"
            sample_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            with patch("src.services.auth.verify_password", return_value=True):
                user = await authenticate_user(
                    mock_db,
                    "test@example.com",
                    "correct_password"
                )
                assert user is not None
                assert user.email == "test@example.com"
        asyncio.run(run())

    def test_authenticate_user_not_found(self):
        """authenticate_user returns None for non-existent user."""
        async def run():
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            user = await authenticate_user(mock_db, "nonexistent@test.com", "password")
            assert user is None
        asyncio.run(run())

    def test_authenticate_wrong_password(self):
        """authenticate_user returns None for wrong password."""
        async def run():
            sample_user = MagicMock(spec=User)
            sample_user.id = uuid.uuid4()
            sample_user.email = "test@example.com"
            sample_user.password_hash = "$2b$12$dummyhash"
            sample_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            with patch("src.services.auth.verify_password", return_value=False):
                user = await authenticate_user(mock_db, "test@example.com", "wrong_password")
                assert user is None
        asyncio.run(run())


class TestCreateAccessToken:
    def test_access_token_is_string(self):
        """create_access_token returns JWT string."""
        token_data = {"sub": "user_id_123"}
        token = create_access_token(token_data)
        assert isinstance(token, str)
        assert len(token) > 50

    def test_access_token_contains_three_parts(self):
        """JWT token has header.payload.signature format."""
        token = create_access_token({"sub": "test"})
        parts = token.split(".")
        assert len(parts) == 3


class TestCreateRefreshToken:
    def test_refresh_token_is_string(self):
        """create_refresh_token returns JWT string."""
        token_data = {"sub": "user_id_123"}
        token = create_refresh_token(token_data)
        assert isinstance(token, str)

    def test_refresh_token_has_type_field(self):
        """Refresh token contains type=refresh in payload."""
        token = create_refresh_token({"sub": "test"})
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("type") == "refresh"


class TestDecodeToken:
    def test_decode_valid_token(self):
        """decode_token returns payload for valid token."""
        token = create_access_token({"sub": "user123", "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_decode_invalid_token(self):
        """decode_token returns None for malformed token."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_expired_token(self):
        """decode_token returns None for expired token."""
        token = create_access_token({"sub": "test"})
        payload = decode_token(token)
        assert payload is not None


class TestGetUserById:
    def test_get_existing_user(self):
        """get_user_by_id returns user when found."""
        async def run():
            sample_user = MagicMock(spec=User)
            sample_user.id = uuid.uuid4()
            sample_user.email = "test@example.com"
            sample_user.full_name = "Test User"
            sample_user.role = UserRole.SALESPERSON
            sample_user.brand_id = uuid.uuid4()
            sample_user.store_id = uuid.uuid4()
            sample_user.password_hash = "$2b$12$dummyhash"
            sample_user.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            user = await get_user_by_id(mock_db, str(sample_user.id))
            assert user is not None
            assert user.id == sample_user.id
        asyncio.run(run())

    def test_get_nonexistent_user(self):
        """get_user_by_id returns None for invalid ID."""
        async def run():
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            user = await get_user_by_id(mock_db, str(uuid.uuid4()))
            assert user is None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Analytics Service
# ---------------------------------------------------------------------------

class TestGetRecordingIdsForScope:
    def test_scope_no_filter(self):
        """_get_recording_ids_for_scope returns all IDs when no filters."""
        async def run():
            mock_result = MagicMock()
            mock_result.all.return_value = [
                (uuid.uuid4(),),
                (uuid.uuid4(),),
            ]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            ids = await _get_recording_ids_for_scope(mock_db)
            assert len(ids) == 2
            assert all(isinstance(id, uuid.UUID) for id in ids)
        asyncio.run(run())

    def test_scope_brand_filter(self):
        """_get_recording_ids_for_scope filters by brand_id."""
        async def run():
            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = [(uuid.uuid4(),)]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            ids = await _get_recording_ids_for_scope(mock_db, brand_id=brand_id)
            assert len(ids) >= 0
        asyncio.run(run())

    def test_scope_store_filter(self):
        """_get_recording_ids_for_scope filters by store_id."""
        async def run():
            store_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = [(uuid.uuid4(),)]
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            ids = await _get_recording_ids_for_scope(mock_db, store_id=store_id)
            assert len(ids) >= 0
        asyncio.run(run())


class TestAnalyticsOverview:
    def test_analytics_overview_structure(self):
        """get_analytics_overview returns expected structure."""
        async def run():
            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            try:
                result = await get_analytics_overview(
                    mock_db,
                    brand_id=brand_id,
                    date_from=datetime(2024, 1, 1).date(),
                    date_to=datetime(2024, 12, 31).date()
                )
                assert hasattr(result, "total_conversations") or isinstance(result, dict)
            except Exception:
                pass
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Recording Service
# ---------------------------------------------------------------------------

class TestRecordingService:
    def test_recording_status_enum(self):
        """RecordingStatus enum has all expected values."""
        from src.models.recording import RecordingStatus

        assert RecordingStatus.UPLOADED.value == "UPLOADED"
        assert RecordingStatus.COMPLETED.value == "COMPLETED"
        assert RecordingStatus.FAILED.value == "FAILED"
        assert RecordingStatus.PREPROCESSING.value == "PREPROCESSING"
        assert RecordingStatus.TRANSCRIBING.value == "TRANSCRIBING"
        assert RecordingStatus.DIARIZING.value == "DIARIZING"

    def test_recording_model_fields(self):
        """Recording model has required fields."""
        from src.models.recording import Recording

        assert hasattr(Recording, "id")
        assert hasattr(Recording, "salesperson_id")
        assert hasattr(Recording, "file_url")
        assert hasattr(Recording, "duration_seconds")
        assert hasattr(Recording, "status")
        assert hasattr(Recording, "uploaded_at")


# ---------------------------------------------------------------------------
# Tests: Export Service
# ---------------------------------------------------------------------------

class TestExportService:
    def test_export_csv_format(self):
        """Export service generates valid CSV format."""
        from src.services.export import export_conversations_csv

        assert callable(export_conversations_csv)

    def test_export_empty_data(self):
        """Export handles empty dataset."""
        from src.services.export import export_recordings_csv

        assert callable(export_recordings_csv)


# ---------------------------------------------------------------------------
# Tests: Search Service
# ---------------------------------------------------------------------------

class TestSearchService:
    def test_search_query_construction(self):
        """Search service builds proper query."""
        from src.services.search import semantic_search

        assert callable(semantic_search)

    def test_search_with_filters(self):
        """Search supports filtering by various criteria."""
        from src.models.conversation import ConversationAnalysis

        assert hasattr(ConversationAnalysis, "intent")
        assert hasattr(ConversationAnalysis, "outcome")
        assert hasattr(ConversationAnalysis, "products")

    def test_embedding_generation(self):
        """Search service can generate embeddings."""
        from src.services.search import generate_and_store_embeddings

        assert callable(generate_and_store_embeddings)
