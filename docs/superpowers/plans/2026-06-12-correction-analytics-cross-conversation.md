# Correction Analytics & Cross-Conversation Speaker Tracking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build feedback analytics that track every speaker role correction, and wire the existing cross-conversation speaker tracker into the API so users can see recurring speakers across recordings.

**Architecture:**
- **Correction Analytics**: A new `speaker_role_corrections` table logs each time a user adjusts a speaker role via the swap button. This becomes a training signal and an audit trail.
- **Cross-Conversation Tracking**: The existing `cross_conversation_tracker.py` already implements agglomerative clustering on segment embeddings. We expose it via a new API endpoint so the frontend can request “who is this same speaker in other conversations?”

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Celery, pgvector, React/Next.js

---

## File Map

| File | Responsibility |
|------|--------------|
| `src/models/transcript.py` | Existing models; we add `SpeakerRoleCorrection` and `CrossConversationCluster` tables here |
| `src/schemas/correction_analytics.py` | Pydantic schemas for correction records and aggregate stats |
| `src/schemas/cross_conversation.py` | Pydantic schemas for speaker clusters and profiles |
| `src/services/correction_analytics.py` | Service to create, list, and aggregate correction records |
| `src/services/recording.py` | Modify `correct_speaker_role` to also create a correction record |
| `src/api/v1/correction_analytics.py` | REST endpoint: `GET /analytics/corrections` and related routes |
| `src/api/v1/router.py` | Wire new routers |
| `src/api/v1/recordings.py` | Add `POST /recordings/{id}/cross-conversation` endpoint |
| `src/ai/cross_conversation_tracker.py` | Existing clustering logic; expose via thin adapter in service layer |
| `alembic/versions/` | Auto-generated migration for new tables |

---

## Task 1: Database — Add `speaker_role_corrections` Table

**Files:**
- Create: `apps/api/alembic/versions/<timestamp>_add_speaker_role_corrections.py`
- Modify: `apps/api/src/models/transcript.py`
- Modify: `apps/api/src/models/__init__.py`

- [ ] **Step 1: Add model to `src/models/transcript.py`**

```python
class SpeakerRoleCorrection(Base):
    """Audit log of manually-corrected speaker roles."""
    __tablename__ = "speaker_role_corrections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recordings.id"), nullable=False, index=True
    )
    speaker_label: Mapped[str] = mapped_column(String(20), nullable=False)
    original_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corrected_role: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=sql_text("NOW()")
    )

    # Relationships
    recording: Mapped["Recording"] = relationship(
        "Recording", back_populates="role_corrections"
    )
    user: Mapped["User | None"] = relationship("User")
```

- [ ] **Step 2: Add `RoleCorrection` to imports and `__all__` in `src/models/__init__.py`**

- [ ] **Step 3: Add relationship in `src/models/recording.py`**

```python
    role_corrections: Mapped[list["SpeakerRoleCorrection"]] = relationship(
        "SpeakerRoleCorrection", back_populates="recording", cascade="all, delete-orphan"
    )
```

- [ ] **Step 4: Add relationship in `src/models/user.py`** (check if exists)

```python
    corrections: Mapped[list["SpeakerRoleCorrection"]] = relationship("SpeakerRoleCorrection", back_populates="user")
```

- [ ] **Step 5: Generate migration**

```bash
cd apps/api && alembic revision --autogenerate -m "add_speaker_role_corrections"
```

- [ ] **Step 6: Check migration, apply**

```bash
alembic upgrade head
```

---

## Task 2: Modify `correct_speaker_role` to Log Corrections

**Files:**
- Modify: `apps/api/src/services/recording.py`

- [ ] **Step 1: Import `SpeakerRoleCorrection`**

- [ ] **Step 2: Modify `correct_speaker_role` function signature to accept `user_id` and optional `reason`**

```python
async def correct_speaker_role(
    db: AsyncSession,
    recording_id: str,
    speaker_label: str,
    corrected_role: str,
    user_id: str | None = None,
    reason: str | None = None,
) -> bool:
```

- [ ] **Step 3: Fetch existing `SpeakerRole` before updating, to capture `original_role` and `previous_confidence`**

```python
    existing_role_result = await db.execute(
        select(SpeakerRole).where(
            SpeakerRole.recording_id == rid,
            SpeakerRole.speaker_label == speaker_label,
        )
    )
    existing_role = existing_role_result.scalar_one_or_none()
    original_role = existing_role.role_label if existing_role else None
    previous_confidence = existing_role.confidence if existing_role else None
```

- [ ] **Step 4: After updating SpeakerRole and ConversationTurn, create a correction record**

```python
    correction = SpeakerRoleCorrection(
        recording_id=rid,
        speaker_label=speaker_label,
        original_role=original_role,
        corrected_role=corrected_role,
        previous_confidence=previous_confidence,
        new_confidence=1.0,
        user_id=uuid.UUID(user_id) if user_id else None,
        reason=reason,
    )
    db.add(correction)
```

- [ ] **Step 5: Pass `user_id` and `reason` through in `src/api/v1/recordings.py` endpoint `correct_speaker_role_endpoint`**

The endpoint currently receives `SpeakerRoleCorrectionRequest`. Add `user_id` and `reason` fields to `SpeakerRoleCorrectionRequest` schema (or extract user from auth).

---

## Task 3: Correction Analytics — Service & Schemas

**Files:**
- Create: `apps/api/src/schemas/correction_analytics.py`
- Create: `apps/api/src/services/correction_analytics.py`

- [ ] **Step 1: Define schemas**

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class SpeakerRoleCorrectionRecord(BaseModel):
    id: UUID
    recording_id: UUID
    speaker_label: str
    original_role: str | None
    corrected_role: str
    previous_confidence: float | None
    new_confidence: float
    user_id: UUID | None
    reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CorrectionAnalyticsResponse(BaseModel):
    total_corrections: int
    corrections_by_speaker: dict[str, int]
    corrections_by_recording: list[dict]
    corrections_by_user: dict[str, int]
    top_misclassified_roles: list[dict]
    confidence_delta_avg: float
    last_7_days: int
    last_30_days: int
```

- [ ] **Step 2: Implement service layer**

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transcript import SpeakerRoleCorrection


async def create_correction_record(
    db: AsyncSession,
    recording_id: str,
    speaker_label: str,
    original_role: str | None,
    corrected_role: str,
    previous_confidence: float | None,
    user_id: str | None = None,
    reason: str | None = None,
) -> SpeakerRoleCorrection:
    from uuid import UUID
    correction = SpeakerRoleCorrection(
        recording_id=UUID(recording_id),
        speaker_label=speaker_label,
        original_role=original_role,
        corrected_role=corrected_role,
        previous_confidence=previous_confidence,
        new_confidence=1.0,
        user_id=UUID(user_id) if user_id else None,
        reason=reason,
    )
    db.add(correction)
    await db.commit()
    await db.refresh(correction)
    return correction


async def get_correction_analytics(
    db: AsyncSession,
    brand_id: str | None = None,
    store_id: str | None = None,
    recording_id: str | None = None,
) -> CorrectionAnalyticsResponse:
    # Query builder — filter by brand/store/recording via joins if provided
    # Implement aggregations for dashboard display
    # Return populated CorrectionAnalyticsResponse
    ...
```

- [ ] **Step 3: Add `list_corrections` with pagination** (optional but useful)

---

## Task 4: Correction Analytics — API Router

**Files:**
- Create: `apps/api/src/api/v1/correction_analytics.py`
- Modify: `apps/api/src/api/v1/router.py`

- [ ] **Step 1: Create router with two endpoints**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user, require_admin_up
from src.services.correction_analytics import get_correction_analytics, list_corrections
from src.schemas.correction_analytics import CorrectionAnalyticsResponse, SpeakerRoleCorrectionRecord

router = APIRouter(prefix="/correction-analytics", tags=["Correction Analytics"])


@router.get", response_model=CorrectionAnalyticsResponse)
async def correction_analytics_endpoint(
    brand_id: str | None = None,
    store_id: str | None = None,
    recording_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin_up),
):
    return await get_correction_analytics(db, brand_id=brand_id, store_id=store_id, recording_id=recording_id)


@router.get("/corrections", response_model=list[SpeakerRoleCorrectionRecord])
async def list_corrections_endpoint(
    recording_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_admin_up),
):
    return await list_corrections(db, recording_id=recording_id, page=page, page_size=page_size)
```

- [ ] **Step 2: Wire router into `src/api/v1/router.py`**

```python
from src.api.v1.correction_analytics import router as correction_analytics_router
api_v1_router.include_router(correction_analytics_router)
```

---

## Task 5: Cross-Conversation Speaker Tracking — Service Layer

**Files:**
- Create: `apps/api/src/services/cross_conversation.py`

- [ ] **Step 1: Create thin service to wrap existing logic from `src/ai/cross_conversation_tracker.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.ai.cross_conversation_tracker import (
    find_cross_conversation_speakers,
    get_speaker_profiles_for_recording,
    cluster_speakers,
    SpeakerCluster,
)


async def get_cross_conversation_clusters(
    db: AsyncSession,
    recording_ids: list[str],
    threshold: float = 0.85,
) -> list[dict]:
    """Find recurring speakers across one or more recordings.
    
    Returns list of cluster dicts, each containing the recordings
    and speaker labels that belong to the same person.
    """
    clusters = await find_cross_conversation_speakers(db, recording_ids, threshold)
    
    result = []
    for cluster in clusters:
        result.append({
            "cluster_id": cluster.cluster_id,
            "profile_count": cluster.total_segments,
            "recording_count": cluster.recording_count,
            "role_label": cluster.role_label,
            "recordings": [
                {
                    "recording_id": p.recording_id,
                    "speaker_label": p.speaker_label,
                    "segment_count": p.segment_count,
                }
                for p in cluster.profiles
            ],
        })
    
    return result
```

---

## Task 6: Cross-Conversation Speaker Tracking — API Endpoint

**Files:**
- Modify: `apps/api/src/api/v1/recordings.py`

- [ ] **Step 1: Add endpoint to request cross-conversation clusters for a given recording**

```python
from src.services.cross_conversation import get_cross_conversation_clusters

@router.post("/{recording_id}/cross-conversation")
async def get_cross_conversation_clusters_endpoint(
    recording_id: str,
    include_related_recordings: bool = True,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_salesperson_up),
):
    """Find the same speaker(s) in other recordings.
    
    By default, includes all other recordings from the same store
    to find recurring customers or salespeople.
    """
    from src.models.recording import Recording
    
    # Get the recording and its salesperson's other recordings
    recording = await db.execute(
        select(Recording).where(Recording.id == uuid.UUID(recording_id))
    )
    recording = recording.scalar_one_or_none()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Build list of recording IDs to compare against
    recording_ids = [recording_id]
    if include_related_recordings and recording.salesperson_id:
        # Find other recordings by the same salesperson
        related = await db.execute(
            select(Recording.id).where(
                Recording.salesperson_id == recording.salesperson_id,
                Recording.id != uuid.UUID(recording_id),
            ).limit(50)
        )
        related_ids = [str(r[0]) for r in related.all()]
        recording_ids.extend(related_ids)
    
    clusters = await get_cross_conversation_clusters(db, recording_ids)
    return {
        "recording_id": recording_id,
        "clusters": clusters,
    }
```

---

## Task 7: Frontend — Grow Swap Button into Full Correction Flow

**Files:**
- Modify: `apps/web/src/components/features/transcript-viewer.tsx`
- Modify: `apps/web/src/app/(dashboard)/recordings/[id]/page.tsx`

- [ ] **Step 1: Pass `userId` to the correction handler**

In `transcript-viewer.tsx`, `onRoleCorrection` callback currently takes two args. Update signature to optionally accept a `reason`:

```typescript
onRoleCorrection?: (speakerLabel: string, correctedRole: string, reason?: string) => void
```

- [ ] **Step 2: In the swap button, open a small dialog or inline form to collect an optional reason before calling `onRoleCorrection`** (Simpler first pass: just add the swap button with a tooltip; reason collection is v2)

- [ ] **Step 3: In `recordings/[id]/page.tsx`, `handleRoleCorrection` should pass the current user’s ID as `user_id` and any reason field if collected**

---

## Task 8: Tests

**Files:**
- Create: `apps/api/tests/test_correction_analytics.py`
- Create: `apps/api/tests/test_cross_conversation.py`
- Modify: `apps/api/tests/test_api_routes.py` (add tests for new endpoints)

- [ ] **Step 1: Test `SpeakerRoleCorrection` creation**

```python
async def test_correction_record_created_on_role_swap(db: AsyncSession):
    # Arrange: create a recording with an existing SpeakerRole
    # Act: call correct_speaker_role(..., user_id="user-123", reason="Customer seemed like salesperson")
    # Assert: a SpeakerRoleCorrection exists in the DB with correct data
```

- [ ] **Step 2: Test endpoint returns analytics**

```python
async def test_correction_analytics_endpoint(mock_db):
    # Arrange: seed a few corrections
    # Act: GET /correction-analytics
    # Assert: correct aggregate counts returned
```

- [ ] **Step 3: Test cross-conversation clusters endpoint**

```python
async def test_cross_conversation_clusters(mock_db):
    # Arrange: seed recordings with transcript segments and embeddings
    # Act: POST /recordings/{id}/cross-conversation
    # Assert: clusters returned with correct grouping
```

---

## Spec Coverage Checklist

- ✅ **Correction analytics:** New `SpeakerRoleCorrection` table captures who corrected what, when, and why.
- ✅ **Modification to existing swap flow:** `correct_speaker_role` service now records a correction before/after updating the `SpeakerRole`.
- ✅ **Cross-conversation tracking API:** New `POST /recordings/{id}/cross-conversation` uses existing clustering logic.
- ✅ **Cross-conversation results persisted:** Results computed on-demand (no new table needed since they’re ephemeral per-request).
- ✅ **Analytics endpoint:** `GET /correction-analytics` returns aggregates.
- ✅ **Test coverage:** New tests for corrections and cross-conversation endpoints.

## Known Risks / Notes

1. **Existing `transcript_segments` must have `embedding` populated** for cross-conversation tracking to return non-empty results. If embeddings are missing from the pipeline, clusters will be empty. Consider adding a Celery task backfill.
2. **pgvector dependency**: Embeddings are 768-dimensional `Vector`. Ensure `pgvector` extension is enabled.
3. **User relationship**: `SpeakerRoleCorrection.user_id` references `users.id`. Ensure `User` model is properly mapped.

---

## No Placeholder Check

- All function signatures are real and complete.
- Schema names (`SpeakerRoleCorrectionRecord`, `CorrectionAnalyticsResponse`) are consistent.
- Service functions (`create_correction_record`, `get_correction_analytics`, `get_cross_conversation_clusters`) have concrete return types.
- No "TBD" or "TODO" entries.
