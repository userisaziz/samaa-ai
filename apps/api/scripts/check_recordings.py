#!/usr/bin/env python3
"""Check recording statuses and pipeline health.

Usage:
  PYTHONPATH=/Users/almabetter/xsamaa-ai-pipeline/apps/api uv run python scripts/check_recordings.py
"""
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from src.config import settings
from src.models.recording import Recording, RecordingStatus

def main():
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Total count
        total = session.query(Recording).count()
        print(f"📊 Total recordings: {total}\n")
        
        if total == 0:
            print("⚠️  No recordings found in database")
            return
        
        # Status breakdown
        print("📈 Status breakdown:")
        print("=" * 60)
        statuses = session.query(Recording.status, func.count(Recording.id)).group_by(Recording.status).all()
        for status, count in sorted(statuses, key=lambda x: x[0]):
            emoji = {
                "UPLOADED": "📤",
                "PREPROCESSING": "🔧",
                "TRANSCRIBING": "📝",
                "DIARIZING": "🎯",
                "RECONCILING": "🔄",
                "SEGMENTING": "✂️",
                "STITCHING": "🎬",
                "ANALYZING": "🧠",
                "SCORING": "📊",
                "COMPLETED": "✅",
                "FAILED": "❌",
            }.get(status, "❓")
            print(f"  {emoji} {status:20s} → {count}")
        
        print("=" * 60)
        
        # Failed recordings
        failed = session.query(Recording).filter(Recording.status == RecordingStatus.FAILED).all()
        if failed:
            print(f"\n❌ Failed recordings ({len(failed)}):")
            for rec in failed[:10]:  # Show first 10
                print(f"  • {str(rec.id)[:8]}... - {rec.error_message or 'No error message'}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more")
        
        # Stuck recordings (processing status)
        processing_statuses = [
            RecordingStatus.PREPROCESSING,
            RecordingStatus.TRANSCRIBING,
            RecordingStatus.DIARIZING,
            RecordingStatus.RECONCILING,
            RecordingStatus.SEGMENTING,
            RecordingStatus.STITCHING,
            RecordingStatus.ANALYZING,
            RecordingStatus.SCORING,
        ]
        stuck = session.query(Recording).filter(Recording.status.in_(processing_statuses)).all()
        if stuck:
            print(f"\n⏳ Processing recordings ({len(stuck)}):")
            for rec in stuck[:10]:
                print(f"  • {str(rec.id)[:8]}... - {rec.status}")
            if len(stuck) > 10:
                print(f"  ... and {len(stuck) - 10} more")
        
        # Completed recordings
        completed = session.query(Recording).filter(Recording.status == RecordingStatus.COMPLETED).count()
        print(f"\n✅ Completion rate: {completed}/{total} ({completed/total*100:.1f}%)")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
