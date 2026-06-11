"""Voiceprint enrollment and matching service (Phase C scaffold).

Provides an abstraction layer for speaker identification via voiceprint
enrollment. Supports pluggable engines (Picovoice Eagle, Resemblyzer, etc.).

Current status: SCAFFOLD ONLY — the Picovoice Eagle integration requires
the `pveagle` package and an access key from the Picovoice Console.
The service methods raise NotImplementedError until the SDK is installed
and configured.

Architecture:
    1. Enrollment: A salesperson records 30-60s of speech → engine creates
       a voiceprint profile → stored in speaker_voiceprints table.
    2. Matching: Before diarization, audio is compared against enrolled
       voiceprints → matched segments get labeled immediately → unmatched
       voices become "Customer".
    3. Hybrid resolution: voiceprint match + LLM role classification +
       recording metadata → confidence-weighted fusion.
"""
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transcript import SpeakerVoiceprint

logger = logging.getLogger(__name__)


class VoiceprintEngine(str, Enum):
    """Supported voiceprint engines."""
    PICOVOICE_EAGLE = "picovoice_eagle"
    RESEMBLYZER = "resemblyzer"


class EnrollmentStatus(str, Enum):
    """Voiceprint enrollment status."""
    PENDING = "pending"
    ENROLLED = "enrolled"
    FAILED = "failed"


@dataclass
class VoiceprintMatch:
    """Result of matching audio against enrolled voiceprints."""
    salesperson_id: uuid.UUID
    speaker_label: str
    confidence: float
    engine: str


class VoiceprintEngineProtocol(Protocol):
    """Interface for pluggable voiceprint engines."""

    def enroll(self, audio_frames: list[bytes], sample_rate: int) -> bytes:
        """Create a voiceprint profile from audio frames.

        Args:
            audio_frames: List of PCM audio frames (16-bit, mono).
            sample_rate: Audio sample rate in Hz.

        Returns:
            Serialized voiceprint profile bytes.
        """
        ...

    def match(
        self, audio_frames: list[bytes], sample_rate: int, profiles: list[bytes]
    ) -> list[tuple[int, float]]:
        """Match audio against a list of voiceprint profiles.

        Args:
            audio_frames: List of PCM audio frames.
            sample_rate: Audio sample rate in Hz.
            profiles: List of serialized voiceprint profiles.

        Returns:
            List of (profile_index, confidence) tuples, sorted by confidence desc.
        """
        ...


# --- Database Operations ---

async def create_voiceprint_record(
    db: AsyncSession,
    salesperson_id: str,
    recording_id: str | None = None,
    engine: str = VoiceprintEngine.PICOVOICE_EAGLE.value,
) -> SpeakerVoiceprint:
    """Create a new voiceprint enrollment record.

    Args:
        db: Database session.
        salesperson_id: ID of the salesperson to enroll.
        recording_id: Optional source recording ID.
        engine: Voiceprint engine identifier.

    Returns:
        New SpeakerVoiceprint record (not yet committed).
    """
    voiceprint = SpeakerVoiceprint(
        salesperson_id=uuid.UUID(salesperson_id),
        recording_id=uuid.UUID(recording_id) if recording_id else None,
        engine=engine,
        status=EnrollmentStatus.PENDING.value,
    )
    db.add(voiceprint)
    await db.commit()
    await db.refresh(voiceprint)
    logger.info(f"Created voiceprint record {voiceprint.id} for salesperson {salesperson_id}")
    return voiceprint


async def get_enrolled_voiceprints(
    db: AsyncSession,
    salesperson_id: str,
    engine: str = VoiceprintEngine.PICOVOICE_EAGLE.value,
) -> list[SpeakerVoiceprint]:
    """Get all enrolled voiceprints for a salesperson.

    Args:
        db: Database session.
        salesperson_id: ID of the salesperson.
        engine: Voiceprint engine to filter by.

    Returns:
        List of enrolled SpeakerVoiceprint records.
    """
    result = await db.execute(
        select(SpeakerVoiceprint)
        .where(
            SpeakerVoiceprint.salesperson_id == uuid.UUID(salesperson_id),
            SpeakerVoiceprint.engine == engine,
            SpeakerVoiceprint.status == EnrollmentStatus.ENROLLED.value,
        )
        .order_by(SpeakerVoiceprint.enrolled_at.desc())
    )
    return list(result.scalars().all())


async def get_store_voiceprints(
    db: AsyncSession,
    store_id: str,
    engine: str = VoiceprintEngine.PICOVOICE_EAGLE.value,
) -> list[SpeakerVoiceprint]:
    """Get all enrolled voiceprints for all salespeople in a store.

    Used for pre-diarization matching — check if any audio segments
    match known salespeople at the store.

    Args:
        db: Database session.
        store_id: ID of the store.
        engine: Voiceprint engine to filter by.

    Returns:
        List of enrolled SpeakerVoiceprint records for the store.
    """
    from src.models.salesperson import Salesperson

    sp_ids = select(Salesperson.id).where(
        Salesperson.store_id == uuid.UUID(store_id)
    )
    result = await db.execute(
        select(SpeakerVoiceprint)
        .where(
            SpeakerVoiceprint.salesperson_id.in_(sp_ids),
            SpeakerVoiceprint.engine == engine,
            SpeakerVoiceprint.status == EnrollmentStatus.ENROLLED.value,
        )
    )
    return list(result.scalars().all())


async def complete_enrollment(
    db: AsyncSession,
    voiceprint_id: str,
    voiceprint_bytes: bytes,
    sample_duration_seconds: float,
    sample_count: int,
) -> SpeakerVoiceprint:
    """Mark a voiceprint enrollment as complete.

    Args:
        db: Database session.
        voiceprint_id: ID of the voiceprint record.
        voiceprint_bytes: Serialized voiceprint profile.
        sample_duration_seconds: Total enrollment audio duration.
        sample_count: Number of audio samples used.

    Returns:
        Updated SpeakerVoiceprint record.

    Raises:
        ValueError: If voiceprint record not found.
    """
    from datetime import datetime

    result = await db.execute(
        select(SpeakerVoiceprint)
        .where(SpeakerVoiceprint.id == uuid.UUID(voiceprint_id))
    )
    voiceprint = result.scalar_one_or_none()
    if not voiceprint:
        raise ValueError(f"Voiceprint record {voiceprint_id} not found")

    voiceprint.voiceprint_bytes = voiceprint_bytes
    voiceprint.status = EnrollmentStatus.ENROLLED.value
    voiceprint.sample_duration_seconds = sample_duration_seconds
    voiceprint.sample_count = sample_count
    voiceprint.enrolled_at = datetime.utcnow()

    await db.commit()
    await db.refresh(voiceprint)
    logger.info(f"Completed enrollment for voiceprint {voiceprint_id}")
    return voiceprint


# --- Engine Integration (Scaffold) ---

def get_engine(engine_type: str = VoiceprintEngine.PICOVOICE_EAGLE.value) -> VoiceprintEngineProtocol:
    """Factory for voiceprint engine instances.

    Args:
        engine_type: Engine identifier string.

    Returns:
        Voiceprint engine implementing VoiceprintEngineProtocol.

    Raises:
        NotImplementedError: If engine SDK is not installed.
    """
    if engine_type == VoiceprintEngine.PICOVOICE_EAGLE.value:
        raise NotImplementedError(
            "Picovoice Eagle requires the 'pveagle' package and an access key. "
            "Install with: pip install pveagle && set PICOVOICE_ACCESS_KEY env var. "
            "See: https://picovoice.ai/docs/eagle/python/"
        )
    elif engine_type == VoiceprintEngine.RESEMBLYZER.value:
        raise NotImplementedError(
            "Resemblyzer requires the 'resemblyzer' package. "
            "Install with: pip install resemblyzer. "
            "See: https://github.com/resemble-ai/Resemblyzer"
        )
    else:
        raise ValueError(f"Unknown voiceprint engine: {engine_type}")
