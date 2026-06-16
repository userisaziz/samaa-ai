"""Tests for conversation analysis and scoring parsing logic."""
import pytest

from src.ai.analyzer import (
    _parse_analysis_response,
    _validate_analysis,
)
from src.ai.utils import format_transcript as _format_transcript
from src.ai.scorer import (
    _normalize_scores,
    _parse_scores_response,
    compute_average_scores,
)


# ---------------------------------------------------------------------------
# Tests: Analyzer
# ---------------------------------------------------------------------------

class TestFormatTranscript:
    def test_basic_format(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello there.", "speaker": "Speaker_A"},
            {"start": 65.5, "end": 70.0, "text": "Hi, how are you?", "speaker": "Speaker_B"},
        ]
        result = _format_transcript(segments)
        assert "[00:00] Speaker_A: Hello there." in result
        assert "[01:05] Speaker_B: Hi, how are you?" in result

    def test_empty_segments(self):
        assert _format_transcript([]) == ""


class TestParseAnalysisResponse:
    def test_valid_json(self):
        response = '{"intent": "buy phone", "outcome": "SALE_MADE", "confidence": 90}'
        result = _parse_analysis_response(response)
        assert result is not None
        assert result["intent"] == "buy phone"

    def test_json_in_code_block(self):
        response = '```json\n{"intent": "buy phone", "outcome": "LOST", "confidence": 80}\n```'
        result = _parse_analysis_response(response)
        assert result is not None
        assert result["outcome"] == "LOST"

    def test_json_embedded_in_text(self):
        response = 'Here is the analysis:\n{"intent": "return", "outcome": "FOLLOW_UP_NEEDED", "confidence": 70}\nDone.'
        result = _parse_analysis_response(response)
        assert result is not None
        assert result["intent"] == "return"

    def test_invalid_json(self):
        response = "This is not JSON at all"
        result = _parse_analysis_response(response)
        assert result is None


class TestValidateAnalysis:
    def test_valid_analysis(self):
        analysis = {
            "intent": "Buy a laptop",
            "products": ["MacBook Pro"],
            "budget": "$1000-$2000",
            "objections": ["Too expensive"],
            "competitors": ["Dell"],
            "closing_attempt": True,
            "outcome": "LOST",
            "confidence": 92,
            "summary": "Customer wanted a laptop but found it too expensive.",
            "coaching_notes": "Could have offered financing options.",
        }
        assert _validate_analysis(analysis) is True
        assert analysis["outcome"] == "LOST"

    def test_invalid_outcome(self):
        analysis = {"outcome": "UNKNOWN", "confidence": 90}
        assert _validate_analysis(analysis) is False

    def test_missing_outcome(self):
        analysis = {"confidence": 90}
        assert _validate_analysis(analysis) is False

    def test_clamps_confidence(self):
        analysis = {"outcome": "SALE_MADE", "confidence": 150}
        _validate_analysis(analysis)
        assert analysis["confidence"] == 100

    def test_defaults_for_missing_fields(self):
        analysis = {"outcome": "SALE_MADE", "confidence": 90}
        _validate_analysis(analysis)
        assert analysis["products"] == []
        assert analysis["objections"] == []
        assert analysis["closing_attempt"] is False

    def test_string_to_list_conversion(self):
        analysis = {"outcome": "SALE_MADE", "confidence": 90, "products": "iPhone"}
        _validate_analysis(analysis)
        assert analysis["products"] == ["iPhone"]


# ---------------------------------------------------------------------------
# Tests: Scorer
# ---------------------------------------------------------------------------

class TestParseScoresResponse:
    def test_valid_scores(self):
        response = '{"greeting_score": 85, "discovery_score": 70, "product_knowledge_score": 90, "objection_handling_score": 60, "closing_score": 75}'
        result = _parse_scores_response(response)
        assert result is not None
        assert result["greeting_score"] == 85
        assert result["closing_score"] == 75

    def test_clamps_scores(self):
        response = '{"greeting_score": 150, "discovery_score": -10, "product_knowledge_score": 50, "objection_handling_score": 80, "closing_score": 90}'
        result = _parse_scores_response(response)
        assert result["greeting_score"] == 100
        assert result["discovery_score"] == 0

    def test_invalid_json(self):
        result = _parse_scores_response("not json")
        assert result is None


class TestNormalizeScores:
    def test_all_present(self):
        data = {
            "greeting_score": 80,
            "discovery_score": 70,
            "product_knowledge_score": 90,
            "objection_handling_score": 60,
            "closing_score": 75,
        }
        result = _normalize_scores(data)
        assert result["greeting_score"] == 80
        assert result["closing_score"] == 75

    def test_missing_fields(self):
        data = {"greeting_score": 80}
        result = _normalize_scores(data)
        assert result["greeting_score"] == 80
        assert result["discovery_score"] is None


class TestComputeAverageScores:
    def test_basic_average(self):
        records = [
            {"greeting_score": 80, "discovery_score": 60, "product_knowledge_score": 90, "objection_handling_score": 70, "closing_score": 50},
            {"greeting_score": 90, "discovery_score": 80, "product_knowledge_score": 85, "objection_handling_score": 75, "closing_score": 60},
        ]
        result = compute_average_scores(records)
        assert result["avg_greeting_score"] == 85.0
        assert result["avg_discovery_score"] == 70.0

    def test_empty_records(self):
        result = compute_average_scores([])
        assert result["avg_greeting_score"] is None

    def test_handles_none_values(self):
        records = [
            {"greeting_score": 80, "discovery_score": None, "product_knowledge_score": 90, "objection_handling_score": 70, "closing_score": 50},
            {"greeting_score": 90, "discovery_score": 60, "product_knowledge_score": 85, "objection_handling_score": 75, "closing_score": 60},
        ]
        result = compute_average_scores(records)
        assert result["avg_greeting_score"] == 85.0
        assert result["avg_discovery_score"] == 60.0  # Only one non-None value
