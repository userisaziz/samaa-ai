"""Reprocess analysis for a specific conversation to populate scores."""
import asyncio
import uuid
from src.database import async_session_factory
from sqlalchemy import select
from src.models.conversation import Conversation, ConversationAnalysis
from src.workers.analysis import (
    _get_conversation_segments_sync,
    _store_analysis_sync,
    _update_conversation_summary_sync,
)
from src.ai.analyzer import analyze_conversation as analyze_conversation_ai

async def reprocess():
    conv_id = 'd4eff261-d437-4f47-940d-571212c59131'
    
    print(f'Reprocessing analysis for conversation {conv_id}')
    
    # Get transcript segments
    segments = _get_conversation_segments_sync(conv_id)
    print(f'Found {len(segments)} transcript segment(s)')
    
    if not segments:
        print('No segments found - cannot reprocess')
        return
    
    # Analyze conversation
    print('Running AI analysis...')
    analysis = analyze_conversation_ai(segments)
    
    if not analysis:
        print('Analysis failed')
        return
    
    print(f'Analysis completed:')
    print(f'  Confidence: {analysis.get("confidence")}')
    print(f'  Outcome: {analysis.get("outcome")}')
    print(f'  Scores: {analysis.get("scores")}')
    
    # Store analysis
    print('Storing analysis...')
    _store_analysis_sync(conv_id, analysis)
    
    # Update summary
    summary = analysis.get("summary", "")
    if summary:
        _update_conversation_summary_sync(conv_id, summary)
    
    print('✅ Analysis reprocessed successfully')
    
    # Verify
    async with async_session_factory() as db:
        result = await db.execute(
            select(ConversationAnalysis).where(ConversationAnalysis.conversation_id == uuid.UUID(conv_id))
        )
        updated = result.scalar_one_or_none()
        if updated:
            print(f'\nVerification:')
            print(f'  Scores: {updated.scores}')
            print(f'  Outcome: {updated.outcome}')

asyncio.run(reprocess())
