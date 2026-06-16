"""Tests for conversation segmentation logic (AI-05)."""
import pytest

from src.ai.segmenter import (
    GREETING_PATTERNS,
    FAREWELL_PATTERNS,
    DIRECT_QUESTION_PATTERNS,
    MEDIUM_GAP_THRESHOLD,
    SILENCE_GAP_THRESHOLD,
    _find_boundaries,
    _filter_conversations,
    _text_matches_patterns,
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
        """A gap > 60 seconds splits into two conversations."""
        segments = _make_segments(
            (0.0, 5.0, "Hello, welcome!", "Speaker_A"),
            (5.5, 10.0, "Goodbye, have a nice day!", "Speaker_B"),
            (80.0, 85.0, "Next customer please!", "Speaker_A"),
            (85.5, 90.0, "I want to return this.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2
        assert result[0]["end_time"] == 10.0
        assert result[1]["start_time"] == 80.0

    def test_greeting_creates_boundary(self):
        """A farewell+greeting combo starts a new conversation even without a large gap."""
        segments = _make_segments(
            (0.0, 5.0, "That's everything.", "Speaker_A"),
            (5.5, 12.0, "Goodbye, have a nice day!", "Speaker_A"),
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
            (0.0, 3.0, "Goodbye!", "Speaker_A"),  # farewell + 37s gap → boundary
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
            (70.0, 75.0, "Hi.", "B"),
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
    """Test: medium gap + farewell = new conversation (Rule 3)."""

    def test_medium_gap_with_farewell(self):
        """Customer leaves after farewell, new customer arrives after 25s gap."""
        segments = _make_segments(
            (0.0, 5.0, "Goodbye, have a nice day!", "Speaker_A"),
            (30.0, 35.0, "How much is this phone?", "Speaker_B"),
            (35.5, 40.0, "That one is $299.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries  # boundary after first segment

    def test_medium_gap_without_farewell_no_boundary(self):
        """Medium gap but no farewell = no boundary."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check the inventory.", "Speaker_A"),
            (25.0, 30.0, "Sure, take your time.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert boundaries == []

    def test_arabic_farewell_boundary(self):
        """Arabic farewell + medium gap creates boundary."""
        segments = _make_segments(
            (0.0, 5.0, "مع السلامة، وداعا", "Speaker_A"),
            (30.0, 35.0, "بكم هذا؟", "Speaker_B"),
            (35.5, 40.0, "هذا بخمسين ريال.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries


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


# ===========================================================================
# Real-World Multilingual Test Cases
# These simulate messy, real retail conversations in the Gulf region where
# Arabic, English, Hindi, and Urdu mix freely (code-switching).
# ===========================================================================

class TestCodeSwitching:
    """Real-world: speakers mix languages mid-sentence (Gulf retail norm)."""

    def test_arabic_english_code_switch_greeting(self):
        """Speaker greets in Arabic then switches to English mid-sentence."""
        segments = _make_segments(
            (0.0, 5.0, "Let me organize these items.", "Speaker_A"),
            (5.5, 12.0, "All sorted now. Goodbye!", "Speaker_A"),
            (13.0, 19.0, "مرحبا، welcome! How can I help you?", "Speaker_A"),
            (19.5, 25.0, "I'm looking for a phone case.", "Speaker_B"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_english_arabic_code_switch_farewell(self):
        """Speaker says goodbye mixing English and Arabic."""
        segments = _make_segments(
            (0.0, 5.0, "Let me wrap that for you.", "Speaker_A"),
            (5.5, 10.0, "Thanks, شكرا كتير! Bye bye!", "Speaker_B"),
            (11.0, 16.0, "هلا، good morning! Welcome.", "Speaker_A"),
            (16.5, 22.0, "I need to return something.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_hindi_english_code_switch_question(self):
        """Hindi-English mix question after medium gap + farewell."""
        segments = _make_segments(
            (0.0, 5.0, "Goodbye, see you later!", "Speaker_A"),
            (30.0, 35.0, "यह कितना का है, how much is this?", "Speaker_B"),
            (35.5, 40.0, "This one is 150 riyals.", "Speaker_A"),
        )
        boundaries = _find_boundaries(segments, [])
        assert 0 in boundaries


class TestTransliteratedArabic:
    """Real-world: STT often outputs Arabic as transliterated Latin text.

    Many STT engines produce 'marhaba' instead of 'مرحبا' when the
    language detection is ambiguous or the speaker has a strong accent.
    """

    def test_transliterated_greeting_marhaba(self):
        """'marhaba' should be detected as a greeting."""
        assert _text_matches_patterns("marhaba, welcome!", GREETING_PATTERNS)

    def test_transliterated_greeting_salam(self):
        """'salam alaikum' should be detected as a greeting."""
        assert _text_matches_patterns("salam alaikum", GREETING_PATTERNS)

    def test_transliterated_greeting_sabah_alkhair(self):
        """'sabah alkhair' should be detected as a greeting."""
        assert _text_matches_patterns("sabah alkhair", GREETING_PATTERNS)

    def test_transliterated_farewell_ma_salama(self):
        """'ma salama' should be detected as a farewell."""
        assert _text_matches_patterns("ma salama, see you", FAREWELL_PATTERNS)

    def test_transliterated_farewell_shukran(self):
        """'shukran' should be detected as a farewell."""
        assert _text_matches_patterns("shukran, thanks a lot", FAREWELL_PATTERNS)

    def test_transliterated_question_bikam(self):
        """'bikam' (how much) should be detected as a direct question."""
        assert _text_matches_patterns("bikam hada?", DIRECT_QUESTION_PATTERNS)

    def test_transliterated_question_ain(self):
        """'ain' (where) should be detected as a direct question."""
        assert _text_matches_patterns("ain al-qism al-kahraba'i", DIRECT_QUESTION_PATTERNS)

    def test_transliterated_greeting_hala(self):
        """'hala' should be detected as a greeting."""
        assert _text_matches_patterns("hala wallah, welcome", GREETING_PATTERNS)

    def test_transliterated_segmentation_e2e(self):
        """End-to-end: transliterated Arabic greeting creates boundary."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check the inventory.", "Speaker_A"),
            (5.5, 10.0, "That's all, goodbye.", "Speaker_A"),
            (11.0, 17.0, "marhaba! How can I help you?", "Speaker_A"),
            (17.5, 23.0, "I need a charger for my phone.", "Speaker_B"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2


class TestGulfDialect:
    """Real-world: Gulf dialect differs from MSA (Modern Standard Arabic).

    Common Gulf expressions that STT may capture.
    """

    def test_gulf_greeting_hala_wallah(self):
        """'هلا والله' is a very common Gulf greeting."""
        assert _text_matches_patterns("هلا والله", GREETING_PATTERNS)

    def test_gulf_greeting_yahla(self):
        """'يا هلا' is another common Gulf greeting."""
        assert _text_matches_patterns("يا هلا", GREETING_PATTERNS)

    def test_gulf_how_can_i_help_tafaddal(self):
        """'تفضل' (please go ahead / how can I help) is ubiquitous."""
        assert _text_matches_patterns("تفضل، كيف أساعدك؟", GREETING_PATTERNS)

    def test_gulf_farewell_allah_y3ateek_al3afya(self):
        """Common Gulf farewell — already tested in Arabic but with diacritics."""
        assert _text_matches_patterns("الله يعطيك العافية", FAREWELL_PATTERNS)

    def test_gulf_farewell_fi_aman_allah(self):
        """'في أمان الله' — common Gulf farewell."""
        assert _text_matches_patterns("في أمان الله", FAREWELL_PATTERNS)

    def test_gulf_direct_question_ash_u3indik(self):
        """'وش عندك' (what do you have) — Gulf dialect question."""
        assert _text_matches_patterns("وش عندك؟", DIRECT_QUESTION_PATTERNS)

    def test_gulf_direct_question_abi(self):
        """'أبي' (I want) — very common Gulf customer opener."""
        assert _text_matches_patterns("أبي جوال جديد", DIRECT_QUESTION_PATTERNS)


class TestFalsePositivePrevention:
    """Real-world: words containing greeting-like substrings shouldn't trigger.

    E.g., 'this' contains 'hi', 'highlight' contains 'hi',
    'child' contains 'hi', 'knight' contains 'hi'.
    """

    def test_hi_not_matched_inside_word(self):
        """'hi' inside a word should not trigger greeting."""
        assert not _text_matches_patterns(
            "Let me highlight this item for you.", GREETING_PATTERNS
        )

    def test_hi_in_child_not_matched(self):
        """'hi' in 'child' should not trigger greeting."""
        assert not _text_matches_patterns(
            "This child safety lock is popular.", GREETING_PATTERNS
        )

    def test_bye_inside_word_not_matched(self):
        """'bye' inside a word should not trigger farewell."""
        assert not _text_matches_patterns(
            "We need to check the bypass valve.", FAREWELL_PATTERNS
        )


class TestRapidCustomerTurnover:
    """Real-world: busy retail with quick succession of short conversations.

    Multiple customers arrive in quick succession with only 10-15s gaps.
    """

    def test_three_quick_conversations(self):
        """Three customers in rapid succession, each with farewell+greeting transition."""
        segments = _make_segments(
            # Customer 1
            (0.0, 3.0, "Hello, welcome!", "Salesperson"),
            (3.5, 7.0, "I need batteries.", "Customer_1"),
            (7.5, 11.0, "Here you go, anything else?", "Salesperson"),
            (11.5, 14.0, "Goodbye, thanks!", "Customer_1"),
            # Customer 2 — new greeting after farewell
            (17.0, 20.0, "مرحبا! Welcome!", "Salesperson"),
            (20.5, 24.0, "أبي شاحن", "Customer_2"),
            (24.5, 28.0, "Here you go.", "Salesperson"),
            (28.5, 31.0, "Goodbye, see you!", "Customer_2"),
            # Customer 3 — new greeting after farewell
            (33.0, 36.0, "Good afternoon! How can I help?", "Salesperson"),
            (36.5, 40.0, "Where is the accessories section?", "Customer_3"),
            (40.5, 44.0, "Right this way, follow me.", "Salesperson"),
            (44.5, 48.0, "Thanks a lot.", "Customer_3"),
        )
        result = segment_conversations(segments)
        assert len(result) == 3
        # Verify each conversation has correct speakers
        assert result[0]["segment_count"] == 4
        assert result[1]["segment_count"] == 4
        assert result[2]["segment_count"] == 4

    def test_medium_gap_no_greeting_same_speaker_no_split(self):
        """Salesperson talking to same customer after short pause — no split."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check the back room.", "Salesperson"),
            (18.0, 22.0, "Yes, we have that in stock.", "Salesperson"),
            (22.5, 27.0, "Great, I'll take two.", "Customer"),
        )
        result = segment_conversations(segments)
        assert len(result) == 1


class TestLongConversationTopicShift:
    """Real-world: long conversation where customer browses multiple topics
    without any greeting or farewell — should stay as ONE conversation."""

    def test_long_browsing_session_stays_one_conversation(self):
        """Customer browses phones, then cables, then cases — no boundary."""
        segments = _make_segments(
            (0.0, 5.0, "Hello, welcome to our store.", "Salesperson"),
            (5.5, 10.0, "I'm looking for a smartphone.", "Customer"),
            (10.5, 15.0, "Sure, what's your budget?", "Salesperson"),
            (15.5, 20.0, "Around 1000 riyals.", "Customer"),
            (20.5, 25.0, "Let me show you some options.", "Salesperson"),
            (25.5, 30.0, "This one looks good.", "Customer"),
            (30.5, 35.0, "Great choice. Do you want a case too?", "Salesperson"),
            (35.5, 40.0, "Yes, show me some cases.", "Customer"),
            (40.5, 45.0, "Here are our popular cases.", "Salesperson"),
            (45.5, 50.0, "I'll take the blue one.", "Customer"),
        )
        result = segment_conversations(segments)
        assert len(result) == 1
        assert result[0]["segment_count"] == 10


class TestUrduPatterns:
    """Real-world: many retail workers in the Gulf speak Urdu.

    Urdu greetings/farewells often appear in transcript segments.
    """

    def test_urdu_greeting_assalam_o_alaikum(self):
        """Urdu greeting 'السلام علیکم' should be detected."""
        assert _text_matches_patterns("السلام علیکم", GREETING_PATTERNS)

    def test_urdu_greeting_adab(self):
        """Urdu greeting 'آداب' should be detected."""
        assert _text_matches_patterns("آداب", GREETING_PATTERNS)

    def test_urdu_farewell_khuda_hafiz(self):
        """Urdu farewell 'خدا حافظ' should be detected."""
        assert _text_matches_patterns("خدا حافظ", FAREWELL_PATTERNS)

    def test_urdu_farewell_allah_hafiz(self):
        """Urdu farewell 'اللہ حافظ' should be detected."""
        assert _text_matches_patterns("اللہ حافظ", FAREWELL_PATTERNS)

    def test_urdu_thanks_shukriya(self):
        """Urdu 'شکریہ' (thank you) as farewell."""
        assert _text_matches_patterns("شکریہ بہت زیادہ", FAREWELL_PATTERNS)


class TestPreprocessingSilenceGapIntegration:
    """Real-world: preprocessing pipeline detects silence gaps in audio.

    These gaps may not align perfectly with segment boundaries.
    """

    def test_silence_gap_overlapping_segment_boundary(self):
        """Preprocessing silence gap overlaps with segment transition."""
        segments = _make_segments(
            (0.0, 50.0, "Let me check that for you.", "Speaker_A"),
            (50.5, 100.0, "That's everything, goodbye!", "Speaker_A"),
            (135.0, 140.0, "مرحبا، welcome!", "Speaker_A"),
            (140.5, 148.0, "I need a new laptop.", "Speaker_B"),
        )
        # Preprocessing detected silence from 100s to 135s
        silence_gaps = [(100.0, 135.0)]
        result = segment_conversations(segments, silence_gaps)
        assert len(result) == 2

    def test_short_silence_gap_does_not_split(self):
        """A short silence gap (5s) should NOT create a boundary."""
        segments = _make_segments(
            (0.0, 10.0, "Let me think about this.", "Speaker_A"),
            (15.0, 20.0, "Take your time.", "Speaker_A"),
        )
        silence_gaps = [(10.0, 15.0)]
        result = segment_conversations(segments, silence_gaps)
        assert len(result) == 1


class TestEdgeCases:
    """Real-world edge cases from production recordings."""

    def test_single_segment_returns_empty(self):
        """A single segment can't form a valid conversation (< 2 segments)."""
        segments = _make_segments(
            (0.0, 60.0, "Long monologue about products.", "Speaker_A"),
        )
        result = segment_conversations(segments)
        assert len(result) == 0

    def test_all_segments_are_greetings(self):
        """Edge case: every segment starts with a greeting (broken diarization)."""
        segments = _make_segments(
            (0.0, 3.0, "Hello!", "Speaker_A"),
            (3.5, 6.0, "Welcome!", "Speaker_B"),
            (6.5, 9.0, "Good morning!", "Speaker_C"),
            (9.5, 12.0, "Hey there!", "Speaker_D"),
        )
        # Should not crash; each greeting creates a boundary
        result = segment_conversations(segments)
        # Most will be filtered as too short (< 10s or < 2 segments)
        assert isinstance(result, list)

    def test_consecutive_farewell_and_greeting_adjacent(self):
        """Farewell immediately followed by greeting — clean split."""
        segments = _make_segments(
            (0.0, 8.0, "Here's your receipt.", "Speaker_A"),
            (8.5, 12.0, "Goodbye, see you tomorrow!", "Speaker_A"),
            (12.5, 17.0, "Hello, welcome to our store!", "Speaker_A"),
            (17.5, 23.0, "I'd like to return this shirt.", "Speaker_B"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2

    def test_no_false_boundary_on_repeated_speaker(self):
        """Same speaker continuing after short gap — no boundary."""
        segments = _make_segments(
            (0.0, 5.0, "Let me check our inventory system.", "Salesperson"),
            (7.0, 12.0, "Yes, we have it in the back.", "Salesperson"),
            (12.5, 17.0, "I'll go grab it for you.", "Salesperson"),
        )
        result = segment_conversations(segments)
        assert len(result) == 1

    def test_mixed_script_arabic_numerals_in_text(self):
        """Text with Arabic script mixed with numerals shouldn't break matching."""
        segments = _make_segments(
            (0.0, 5.0, "That will be 150 ريال.", "Speaker_A"),
            (5.5, 10.0, "مع السلامة، thank you!", "Speaker_B"),
            (11.0, 16.0, "هلا، good evening!", "Speaker_A"),
            (16.5, 22.0, "أبي أراجع الطلب رقم 4532.", "Speaker_C"),
        )
        result = segment_conversations(segments)
        assert len(result) == 2
        assert len(result) == 2
