#!/usr/bin/env python3
"""Find all UPLOADED recordings and process them through the local pipeline.

Connects to the production Neon DB (shared with the cloud API), finds
recordings in UPLOADED status, and dispatches them to the local Celery
worker for AI pipeline processing.

Prerequisites:
  1. Local Redis running:  brew services start redis
  2. Local Celery worker:  ./start_local_pipeline.sh
  3. .env.local-pipeline configured with production DATABASE_URL + R2 keys

Usage:
  cd apps/api
  uv run python process_uploaded.py

Options (env vars):
  DRY_RUN=1          — List recordings without triggering pipeline
  RECORDING_ID=<id>  — Process a single recording by ID
  POLL_INTERVAL=5    — Seconds between status checks (default: 5)
  MAX_TIMEOUT=1800   — Max seconds to wait per recording (default: 30 min)
"""
import os
import sys
import time
from datetime import datetime

# Ensure PYTHONPATH includes the apps/api directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("APP_ENV", "development")

DRY_RUN = os.getenv("DRY_RUN", "").strip() in ("1", "true", "yes")
TARGET_RECORDING_ID = os.getenv("RECORDING_ID", "").strip()
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
MAX_TIMEOUT = int(os.getenv("MAX_TIMEOUT", "1800"))


def get_sync_session():
    """Create a sync SQLAlchemy session connected to the production Neon DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.config import settings

    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return Session(engine)


def find_uploaded_recordings(session, target_id=None):
    """Query recordings with status=UPLOADED from the database."""
    from sqlalchemy import select
    from src.models.recording import Recording, RecordingStatus

    stmt = select(Recording).where(Recording.status == RecordingStatus.UPLOADED)
    if target_id:
        import uuid
        stmt = stmt.where(Recording.id == uuid.UUID(target_id))
    stmt = stmt.order_by(Recording.created_at.asc())

    result = session.execute(stmt)
    return list(result.scalars().all())


def monitor_recording(session, recording_id, timeout=MAX_TIMEOUT, poll_interval=POLL_INTERVAL):
    """Poll recording status until terminal state or timeout."""
    from sqlalchemy import select
    from src.models.recording import Recording, RecordingStatus

    STATUS_LABELS = {
        "UPLOADED": "UPLOADED",
        "PREPROCESSING": "PREPROCESSING",
        "TRANSCRIBING": "TRANSCRIBING",
        "DIARIZING": "DIARIZING",
        "RECONCILING": "RECONCILING",
        "SEGMENTING": "SEGMENTING",
        "STITCHING": "STITCHING",
        "ANALYZING": "ANALYZING",
        "SCORING": "SCORING",
        "COMPLETED": "COMPLETED",
        "FAILED": "FAILED",
    }
    TERMINAL = {"COMPLETED", "FAILED"}

    start = time.time()
    last_status = None

    while time.time() - start < timeout:
        session.expire_all()
        stmt = select(Recording).where(Recording.id == recording_id)
        rec = session.execute(stmt).scalar_one_or_none()
        if not rec:
            print(f"  WARNING: recording {recording_id} vanished")
            time.sleep(poll_interval)
            continue

        current = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
        if current != last_status:
            elapsed = time.time() - start
            label = STATUS_LABELS.get(current.upper(), current)
            print(f"  [{elapsed:6.1f}s] {label}")
            if current.upper() in TERMINAL:
                if current.upper() == "FAILED":
                    print(f"           Error: {rec.error_message or 'unknown'}")
                return current.upper()
            last_status = current

        time.sleep(poll_interval)

    print(f"  TIMEOUT after {timeout}s (last status: {last_status})")
    return "TIMEOUT"


def main():
    print("=" * 60)
    print("  CXSAMAA Local Pipeline Runner")
    print("  Finds UPLOADED recordings and processes them locally")
    print("=" * 60)
    print()

    session = get_sync_session()

    try:
        recordings = find_uploaded_recordings(session, TARGET_RECORDING_ID or None)
    except Exception as e:
        print(f"ERROR: Failed to query recordings: {e}")
        sys.exit(1)

    if not recordings:
        print("No UPLOADED recordings found. Nothing to do.")
        return

    print(f"Found {len(recordings)} UPLOADED recording(s):")
    for i, rec in enumerate(recordings, 1):
        dur = rec.duration_seconds or 0
        print(f"  {i}. {rec.id}  (duration: {dur}s, created: {rec.created_at})")
    print()

    if DRY_RUN:
        print("DRY RUN — no pipeline triggered.")
        return

    # Import pipeline dispatcher (requires local Celery + Redis)
    try:
        from src.workers.pipeline import enqueue_first_stage
        from src.config import settings
    except Exception as e:
        print(f"ERROR: Cannot import pipeline modules: {e}")
        print("  Make sure local Redis is running and .env.local-pipeline is configured.")
        sys.exit(1)

    results = {"completed": [], "failed": [], "timeout": []}

    for i, rec in enumerate(recordings, 1):
        rec_id = str(rec.id)
        print(f"[{i}/{len(recordings)}] Processing {rec_id[:12]}...")

        try:
            enqueue_first_stage(rec_id, settings.pipeline_version)
            print(f"  Pipeline enqueued.")
        except Exception as e:
            print(f"  FAILED to enqueue: {e}")
            results["failed"].append((rec_id, str(e)))
            continue

        # Wait a moment for pipeline to start, then monitor
        time.sleep(3)
        final = monitor_recording(session, rec.id)

        if final == "COMPLETED":
            results["completed"].append(rec_id)
        elif final == "FAILED":
            results["failed"].append((rec_id, "pipeline failed"))
        else:
            results["timeout"].append(rec_id)

        print()

    # Summary
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Total:      {len(recordings)}")
    print(f"  Completed:  {len(results['completed'])}")
    print(f"  Failed:     {len(results['failed'])}")
    print(f"  Timeout:    {len(results['timeout'])}")

    if results["failed"]:
        print(f"\n  Failed:")
        for rec_id, err in results["failed"]:
            print(f"    - {rec_id[:12]}... : {err}")

    if results["timeout"]:
        print(f"\n  Timed out:")
        for rec_id in results["timeout"]:
            print(f"    - {rec_id[:12]}...")

    print("=" * 60)


if __name__ == "__main__":
    main()
