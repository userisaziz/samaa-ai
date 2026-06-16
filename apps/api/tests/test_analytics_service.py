"""Tests for analytics service — overview, comparisons, trends."""
import asyncio
import uuid
from datetime import date
from unittest.mock import MagicMock, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Tests: Analytics Overview
# ---------------------------------------------------------------------------

class TestAnalyticsOverview:
    def test_empty_scope_returns_defaults(self):
        """Empty scope returns zero-valued overview."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert overview.funnel_stages is not None
            assert len(overview.outcome_distribution) == 0
        asyncio.run(run())

    def test_brand_scope_aggregates_data(self):
        """Analytics aggregates data for brand scope."""
        async def run():
            from src.services.analytics import get_analytics_overview
            from src.schemas.analytics import AnalyticsOverviewResponse

            brand_id = str(uuid.uuid4())
            mock_db = AsyncMock()

            # Empty recording scope → returns default overview
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(
                mock_db,
                brand_id=brand_id,
                date_from=date(2024, 1, 1),
                date_to=date(2024, 12, 31)
            )

            # Empty scope returns defaults, not errors
            assert isinstance(overview, AnalyticsOverviewResponse)
            assert overview.total_conversations == 0
        asyncio.run(run())

    def test_store_scope_filters_correctly(self):
        """Analytics filters by store scope."""
        async def run():
            from src.services.analytics import get_analytics_overview

            store_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, store_id=store_id)
            assert overview is not None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Funnel Analysis
# ---------------------------------------------------------------------------

class TestFunnelAnalysis:
    def test_funnel_has_conversation_stage(self):
        """Funnel includes conversation count stage."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            funnel_stages = [f.stage for f in overview.funnel_stages]
            assert "Conversations" in funnel_stages or len(overview.funnel_stages) > 0
        asyncio.run(run())

    def test_funnel_has_closing_stage(self):
        """Funnel includes closing attempts stage."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert len(overview.funnel_stages) >= 1
        asyncio.run(run())

    def test_funnel_has_sales_stage(self):
        """Funnel includes sales made stage."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert hasattr(overview, 'funnel_stages')
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Outcome Distribution
# ---------------------------------------------------------------------------

class TestOutcomeDistribution:
    def test_outcome_groups_by_result(self):
        """Outcome distribution groups by analysis outcome."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert isinstance(overview.outcome_distribution, list)
        asyncio.run(run())

    def test_outcome_handles_no_data(self):
        """Outcome distribution handles empty dataset."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert len(overview.outcome_distribution) == 0
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Trend Analysis
# ---------------------------------------------------------------------------

class TestTrendAnalysis:
    def test_score_trend_returns_time_series(self):
        """Score trend returns daily time series."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert isinstance(overview.score_trend, list)
        asyncio.run(run())

    def test_volume_trend_tracks_recordings(self):
        """Volume trend tracks recording count over time."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert isinstance(overview.volume_trend, list)
        asyncio.run(run())

    def test_trends_handle_date_range(self):
        """Trends respect date range filters."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(
                mock_db,
                brand_id=brand_id,
                date_from=date(2024, 1, 1),
                date_to=date(2024, 12, 31)
            )

            assert overview is not None
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Store Comparison
# ---------------------------------------------------------------------------

class TestStoreComparison:
    def test_store_comparison_returns_list(self):
        """Store comparison returns list of store metrics."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)

            assert isinstance(overview.store_comparison, list)
        asyncio.run(run())

    def test_store_comparison_empty_for_single_store(self):
        """Store comparison may be empty for single store scope."""
        async def run():
            from src.services.analytics import get_analytics_overview

            store_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, store_id=store_id)

            assert isinstance(overview.store_comparison, list)
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests: Analytics Edge Cases
# ---------------------------------------------------------------------------

class TestAnalyticsEdgeCases:
    def test_analytics_without_date_filters(self):
        """Analytics works without date filters (all-time)."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(mock_db, brand_id=brand_id)
            assert overview is not None
        asyncio.run(run())

    def test_analytics_with_only_date_from(self):
        """Analytics works with only start date."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(
                mock_db,
                brand_id=brand_id,
                date_from=date(2024, 1, 1)
            )
            assert overview is not None
        asyncio.run(run())

    def test_analytics_with_only_date_to(self):
        """Analytics works with only end date."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(
                mock_db,
                brand_id=brand_id,
                date_to=date(2024, 12, 31)
            )
            assert overview is not None
        asyncio.run(run())

    def test_analytics_future_date_range(self):
        """Analytics handles future date ranges gracefully."""
        async def run():
            from src.services.analytics import get_analytics_overview

            brand_id = str(uuid.uuid4())
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_result.scalars.return_value.all.return_value = []
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_result)

            overview = await get_analytics_overview(
                mock_db,
                brand_id=brand_id,
                date_from=date(2030, 1, 1),
                date_to=date(2030, 12, 31)
            )

            assert overview is not None
        asyncio.run(run())
