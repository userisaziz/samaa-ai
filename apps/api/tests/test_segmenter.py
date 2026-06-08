"""Tests for conversation segmentation logic (AI-05)."""
import pytest

from src.ai.segmenter import (
    GREETING_PATTERNS,
    FAREWELL_PATTERNS,
    DIRECT_QUESTION_PATTERNS,
    MEDIUM_GAP_THRESHOLD,
    _find_boundaries,
    _filter_conversations,
    _text_matches_patterns,
    _is_customer_speaker,
    segment_conversations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_segments(*texts_with_times: tuple[float, float, str, str]) -> list[dict]:
    """Create transcript segments: (start, end, text, speaker)."""
    return [
        {"start": s, "end": e, "text": t, "speaker": sp}
        for s, e, t, sp in texts_with_times
    ]


# ---------------------------------------------------------------------------
# Tests: Basic segmentation
# ---------------------------------------------------------------------------

class TestSegmentConversations:
    def test_empty_input(self):
        assert segment_conversations([]) == []

    def test_single_conversation_no_gaps(self):
        """Segments with no large gaps form a single conversation."""
        segments = _make_segments(
            (0.0, 5.0, "Hello, how can I help you?", "Speaker_A"),
            (5.5, 10.0, "I'm looking for a phone.", "Speaker_B"),
            (10.5, 15.0, "Let me show you our selection.", "Speaker_A"),
        )
        result = segment_conversations(segments)
        assert len(result) == 1
        assert result[0]["segment_count"] == 3
        assert result[0]["start_time"] == 0.0
        assert result[0]["end_time"] == 15.0

    def test_silence_gap_creates_boundary(self):
        """A gap > 30 seconds splits into two conversations."""
        segments = _make_segments(
            (0.0, 5.0, "Hello, welcome!", "Speaker_A"),
            (5.5, 10.0, "Thanks, I need a laptop.", "Speaker_B"),
            (50.0, 55.0, "Next customer please!", "Speaker_A"),
            (55.5, 60.0, "I want to return this.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2
        assert result[0]["end_time"] == 10.0
        assert result[1]["start_time"] == 50.0

    def test_greeting_creates_boundary(self):
        """A greeting phrase starts a new conversation even without a large gap."""
        segments = _make_segments(
            (0.0, 5.0, "That's everything, thank you.", "Speaker_A"),
            (5.5, 12.0, "Let me process that for you.", "Speaker_A"),
            (13.0, 18.0, "Good morning! Welcome to our store.", "Speaker_B"),
            (18.5, 25.0, "I'm looking for a new laptop.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_farewell_creates_boundary(self):
        """A farewell phrase ends a conversation."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check that for you.", "Speaker_A"),
            (5.5, 10.0, "Great, I'll take it.", "Speaker_B"),
            (10.5, 15.0, "Goodbye, have a nice day!", "Speaker_A"),
            (20.0, 25.0, "Welcome! How can I help you today?", "Speaker_A"),
            (25.5, 35.0, "I need to find a replacement part.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_short_conversations_filtered(self):
        """Conversations shorter than 10s or with < 2 segments are filtered out."""
        segments = _make_segments(
            (0.0, 3.0, "Hi.", "Speaker_A"),  # too short, single segment
            (40.0, 45.0, "Hello, welcome!", "Speaker_B"),
            (45.5, 55.0, "I'm looking for shoes.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        # First segment should be filtered (< 10s and < 2 segments)
        assert len(result) == 1
        assert result[0]["start_time"] == 40.0


# ---------------------------------------------------------------------------
# Tests: Boundary detection
# ---------------------------------------------------------------------------

class TestFindBoundaries:
    def test_no_boundaries(self):
        segments = _make_segments(
            (0.0, 5.0, "I need a new phone case.", "A"),
            (6.0, 10.0, "Sure, let me show you some options.", "B"),
        )
        assert _find_boundaries(segments, []) == []

    def test_silence_gap_boundary(self):
        segments = _make_segments(
            (0.0, 5.0, "Hello.", "A"),
            (50.0, 55.0, "Hi.", "B"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries  # boundary after segment 0

    def test_preprocessing_silence_gaps(self):
        segments = _make_segments(
            (0.0, 100.0, "Talking.", "A"),
            (200.0, 210.0, "More talking.", "B"),
        )
        # Preprocessing detected a silence gap from 100s to 200s
        silence_gaps = [(100.0, 200.0)]
        boundaries = _find_boundaries(segments, silence_gaps)
        assert 0 in boundaries


# ---------------------------------------------------------------------------
# Tests: Pattern matching
# ---------------------------------------------------------------------------

class TestPatternMatching:
    def test_greeting_patterns(self):
        assert _text_matches_patterns("Hello, welcome to our store!", GREETING_PATTERNS)
        assert _text_matches_patterns("Good morning! How can I help you?", GREETING_PATTERNS)
        assert not _text_matches_patterns("I want to buy a phone.", GREETING_PATTERNS)

    def test_farewell_patterns(self):
        assert _text_matches_patterns("Goodbye, have a nice day!", FAREWELL_PATTERNS)
        assert _text_matches_patterns("Thanks for coming, see you!", FAREWELL_PATTERNS)
        assert not _text_matches_patterns("Let me check the stock.", FAREWELL_PATTERNS)

    def test_case_insensitive(self):
        assert _text_matches_patterns("HELLO THERE", GREETING_PATTERNS)
        assert _text_matches_patterns("GOODBYE EVERYONE", FAREWELL_PATTERNS)

    def test_arabic_greetings(self):
        assert _text_matches_patterns("مرحبا، أهلا وسهلا", GREETING_PATTERNS)
        assert _text_matches_patterns("السلام عليكم", GREETING_PATTERNS)
        assert _text_matches_patterns("صباح الخير", GREETING_PATTERNS)
        assert _text_matches_patterns("هلا", GREETING_PATTERNS)

    def test_arabic_farewells(self):
        assert _text_matches_patterns("مع السلامة", FAREWELL_PATTERNS)
        assert _text_matches_patterns("وداعا", FAREWELL_PATTERNS)
        assert _text_matches_patterns("الله يعطيك العافية", FAREWELL_PATTERNS)

    def test_arabic_direct_questions(self):
        assert _text_matches_patterns("بكم هذا؟", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("كم السعر", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("عندك", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("وين القسم الإلكتروني", DIRECT_QUESTION_PATTERNS)

    def test_hindi_greetings(self):
        assert _text_matches_patterns("नमस्ते", GREETING_PATTERNS)
        assert _text_matches_patterns("नमस्कार", GREETING_PATTERNS)
        assert _text_matches_patterns("स्वागत", GREETING_PATTERNS)

    def test_hindi_farewells(self):
        assert _text_matches_patterns("अलविदा", FAREWELL_PATTERNS)
        assert _text_matches_patterns("धन्यवाद", FAREWELL_PATTERNS)
        assert _text_matches_patterns("शुक्रिया", FAREWELL_PATTERNS)

    def test_hindi_direct_questions(self):
        assert _text_matches_patterns("कितना है ये", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("क्या है ये", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("मुझे चाहिए", DIRECT_QUESTION_PATTERNS)

    def test_english_direct_questions(self):
        assert _text_matches_patterns("How much is this?", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("Do you have this in red?", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("Where is the electronics section?", DIRECT_QUESTION_PATTERNS)
        assert _text_matches_patterns("I'm looking for a laptop", DIRECT_QUESTION_PATTERNS)
        assert not _text_matches_patterns("Sure, let me check", DIRECT_QUESTION_PATTERNS)


# ---------------------------------------------------------------------------
# Tests: Filtering
# ---------------------------------------------------------------------------

class TestDirectQuestionBoundary:
    """Test Rule 4: medium gap + direct question = new conversation (no greeting)."""

    def test_medium_gap_with_direct_question(self):
        """Customer walks in after 15s gap and asks 'how much' without greeting."""
        segments = _make_segments(
            (0.0, 5.0, "Let me organize these items.", "Speaker_A"),
            (20.0, 25.0, "How much is this phone?", "Speaker_B"),
            (25.5, 30.0, "That one is $299.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries  # boundary after first segment

    def test_medium_gap_without_question_no_boundary(self):
        """Medium gap but no question and same speaker = no boundary."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check the inventory.", "Speaker_A"),
            (20.0, 25.0, "Sure, take your time.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert boundaries == []

    def test_arabic_direct_question_boundary(self):
        """Arabic customer asks 'بكم' after medium gap."""
        segments = _make_segments(
            (0.0, 5.0, "أرتب هذه العناصر.", "Speaker_A"),
            (18.0, 22.0, "بكم هذا؟", "Speaker_B"),
            (22.5, 28.0, "هذا بخمسين ريال.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries


class TestSpeakerChangeBoundary:
    """Test Rule 5: speaker change after medium gap = new customer."""

    def test_speaker_change_after_medium_gap(self):
        """New speaker after 12s gap = likely new customer."""
        segments = _make_segments(
            (0.0, 3.0, "Welcome!", "Salesperson"),
            (3.5, 6.0, "Thanks!", "Customer_A"),
            (6.5, 9.0, "Here's your receipt.", "Salesperson"),
            (21.0, 24.0, "أبي شغلة", "Customer_B"),  # Arabic: "I need something"
            (24.5, 27.0, "تفضل", "Salesperson"),
        )
        boundaries = _find_boundaries(segments, [])
        # Should detect boundary at index 2 (speaker change after gap)
        assert 2 in boundaries

    def test_is_customer_speaker(self):
        """Heuristic correctly identifies customer vs salesperson."""
        segments = _make_segments(
            (0.0, 2.0, "Hello!", "SP"),
            (2.5, 4.0, "Hi.", "C1"),
            (4.5, 6.0, "Welcome.", "SP"),
            (6.5, 8.0, "Thanks.", "C1"),
            (8.5, 10.0, "Let me check.", "SP"),
        )
        # SP speaks more in opening = salesperson
        assert not _is_customer_speaker("SP", segments, 0)
        assert _is_customer_speaker("C1", segments, 1)


class TestMultilingualSegmentation:
    """End-to-end segmentation with mixed-language conversations."""

    def test_arabic_greeting_creates_boundary(self):
        """Arabic greeting after farewell splits conversations."""
        segments = _make_segments(
            (0.0, 5.0, "Let me help you with that.", "Speaker_A"),
            (5.5, 10.0, "Goodbye, have a nice day!", "Speaker_A"),
            (11.0, 17.0, "مرحبا، أهلا فيك", "Speaker_A"),
            (17.5, 23.0, "أبي جوال جديد", "Speaker_B"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_hindi_farewell_creates_boundary(self):
        """Hindi farewell ends a conversation."""
        segments = _make_segments(
            (0.0, 5.0, "Let me process this.", "Speaker_A"),
            (5.5, 10.0, "शुक्रिया, अलविदा", "Speaker_B"),
            (11.0, 16.0, "Hello, welcome!", "Speaker_A"),
            (16.5, 22.0, "I need a tablet.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2


class TestFilterConversations:
    def test_filters_short_duration(self):
        conversations = [
            {"start_time": 0.0, "end_time": 5.0, "segments": [{"text": "hi"}, {"text": "hello"}], "segment_count": 2},
            {"start_time": 100.0, "end_time": 200.0, "segments": [{"text": "a"}, {"text": "b"}], "segment_count": 2},
        ]
        result = _filter_conversations(conversations)
        assert len(result) == 1
        assert result[0]["start_time"] == 100.0

    def test_filters_single_segment(self):
        conversations = [
            {"start_time": 0.0, "end_time": 30.0, "segments": [{"text": "hi"}], "segment_count": 1},
        ]
        result = _filter_conversations(conversations)
        assert len(result) == 0
