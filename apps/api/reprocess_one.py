"""Reprocess one conversation bypassing confidence threshold."""
import uuid
from src.workers.analysis import (
    _get_conversation_segments_sync,
    _store_analysis_sync,
    _update_conversation_summary_sync,
)
from src.ai.analyzer import analyze_conversation as analyze_conversation_ai
from src.ai.analyzer import MIN_CONFIDENCE_THRESHOLD

conv_id = 'd4eff261-d437-4f47-940d-571212c59131'

print(f'Reprocessing conversation {conv_id}')
print(f'Current MIN_CONFIDENCE_THRESHOLD: {MIN_CONFIDENCE_THRESHOLD}')

# Get segments
segments = _get_conversation_segments_sync(conv_id)
print(f'Found {len(segments)} segment(s)')

if not segments:
    print('No segments - aborting')
    exit(1)

# Analyze with custom function that bypasses threshold
from src.ai.analyzer import format_transcript
from src.ai.nvidia_client import nvidia_client
import json

transcript_text = format_transcript(segments)

messages = [
    {"role": "system", "content": analyze_conversation.__doc__ or ""},
    {"role": "user", "content": f"Analyze this retail conversation:\n\n{transcript_text}"},
]

# Import the system prompt
from src.ai.analyzer import SYSTEM_PROMPT

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": f"Analyze this retail conversation:\n\n{transcript_text}"},
]

print('Calling LLM...')
response_text = nvidia_client.chat_completion(
    messages=messages,
    temperature=0.1,
    max_tokens=2048,
    response_format={"type": "json_object"},
)

# Parse
try:
    analysis = json.loads(response_text)
    print('✅ Parsed analysis')
    print(f'  Confidence: {analysis.get("confidence")}')
    print(f'  Outcome: {analysis.get("outcome")}')
    print(f'  Scores: {analysis.get("scores")}')
except Exception as e:
    print(f'❌ Parse error: {e}')
    print(f'Response: {response_text[:500]}')
    exit(1)

# Store regardless of confidence
print('Storing analysis...')
_store_analysis_sync(conv_id, analysis)

summary = analysis.get("summary", "")
if summary:
    _update_conversation_summary_sync(conv_id, summary)

print('✅ Done!')
