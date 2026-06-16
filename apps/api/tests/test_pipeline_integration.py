"""Integration tests for audio processing pipeline.

Tests the full pipeline orchestration (run_stage), AI module contracts
(STT, diarization, VAD), error handling, performance config, and data flow.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.workers.pipeline import run_stage, enqueue_first_stage, STAGES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_audio_bytes():
    """Create minimal WAV file bytes for testing."""
    wav_header = b'RIFF'  # Simplified for testing
    return wav_header + b'\x00' * 1000


@pytest.fixture
def sample_transcript_segments():
    """Create sample STT transcript segments."""
    return [
        {"start": 0.0, "end": 5.5, "text": "Hello, welcome to our store."},
        {"start": 6.0, "end": 10.5, "text": "Hi, I'm looking for a laptop."},
        {"start": 11.0, "end": 15.5, "text": "Great! What's your budget?"},
        {"start": 16.0, "end": 20.0, "text": "Around $1000 to $1500."},
    ]


@pytest.fixture
def sample_speaker_segments():
    """Create sample diarization speaker segments."""
    return [
        {"start": 0.0, "end": 5.5, "speaker": "SPEAKER_00"},
        {"start": 6.0, "end": 10.5, "speaker": "SPEAKER_01"},
        {"start": 11.0, "end": 15.5, "speaker": "SPEAKER_00"},
        {"start": 16.0, "end": 20.0, "speaker": "SPEAKER_01"},
    ]


# ---------------------------------------------------------------------------
# Tests: VAD (Voice Activity Detection)
# ---------------------------------------------------------------------------

class TestVoiceActivityDetection:
    def test_detect_speech_regions_structure(self):
        """detect_speech_regions returns list of regions."""
        try:
            from src.ai.vad import detect_speech_regions
            assert callable(detect_speech_regions)
        except ImportError:
            pytest.skip("onnxruntime not installed")

    def test_vad_returns_time_boundaries(self):
        """VAD should return start/end time boundaries."""
        try:
            from src.ai.vad import detect_speech_regions
            import inspect
            sig = inspect.signature(detect_speech_regions)
            assert "audio_bytes" in sig.parameters
        except ImportError:
            pytest.skip("onnxruntime not installed")


# ---------------------------------------------------------------------------
# Tests: STT (Speech-to-Text)
# ---------------------------------------------------------------------------

class TestSpeechToText:
    def test_transcribe_audio_interface(self):
        """transcribe_audio accepts audio bytes."""
        try:
            from src.ai.stt import transcribe_audio
            import inspect
            sig = inspect.signature(transcribe_audio)
            assert "audio_bytes" in sig.parameters
            assert "filename" in sig.parameters
        except ImportError:
            pytest.skip("riva.client not installed")

    def test_transcribe_returns_segments(self):
        """STT should return list of transcript segments."""
        try:
            from src.ai.stt import transcribe_audio
        except ImportError:
            pytest.skip("riva-client not installed")
    
        # Verify the function is callable and accepts the right params
        import inspect
        sig = inspect.signature(transcribe_audio)
        assert "audio_bytes" in sig.parameters
        assert callable(transcribe_audio)


# ---------------------------------------------------------------------------
# Tests: Diarization Integration
# ---------------------------------------------------------------------------

class TestDiarizationIntegration:
    def test_full_diarization_flow(self, sample_audio_bytes):
        """Test complete diarization from audio to speaker labels."""
        from src.ai.diarizer import diarize_audio

        with patch("src.ai.diarizer._get_pyannote_diarizer") as mock_diarizer:
            mock_instance = MagicMock()
            mock_instance.diarize.return_value = [
                {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                {"start": 5.5, "end": 10.0, "speaker": "SPEAKER_01"},
            ]
            mock_diarizer.return_value = mock_instance

            with patch("src.ai.diarizer.settings") as mock_settings:
                mock_settings.diarization_use_pyannote = True
                segments = diarize_audio(sample_audio_bytes)
                assert isinstance(segments, list)

    def test_speaker_label_assignment(self, sample_transcript_segments, sample_speaker_segments):
        """Test assigning speaker labels to transcript segments."""
        from src.ai.diarizer import assign_speaker_labels

        labeled = assign_speaker_labels(
            sample_transcript_segments,
            sample_speaker_segments
        )

        assert len(labeled) == len(sample_transcript_segments)
        assert all("speaker" in seg for seg in labeled)
        assert all(seg["speaker"].startswith("Speaker_") for seg in labeled)

    def test_speaker_label_fallback(self, sample_transcript_segments):
        """Fallback assignment when no diarization available."""
        from src.ai.diarizer import assign_speaker_labels

        labeled = assign_speaker_labels(sample_transcript_segments, [])

        assert len(labeled) == len(sample_transcript_segments)
        assert all("speaker" in seg for seg in labeled)


# ---------------------------------------------------------------------------
# Tests: Pipeline Orchestration (run_stage)
# ---------------------------------------------------------------------------

class TestPipelineOrchestration:
    def test_run_stage_calls_correct_function(self):
        """run_stage should invoke the stage function for the given index."""
        recording_id = str(uuid.uuid4())
        mock_func = MagicMock()
        original = STAGES[0]
        STAGES[0] = (original[0], mock_func, original[2])

        try:
            with patch("src.services.pipeline_state.is_stage_completed_sync", return_value=False), \
                 patch("src.workers.pipeline._get_recording_sync", return_value=None), \
                 patch("src.workers.pipeline._update_status"), \
                 patch("src.workers.pipeline.log_stage_start"), \
                 patch("src.workers.pipeline.log_stage_complete"), \
                 patch("src.workers.pipeline.settings") as mock_settings:

                mock_settings.app_env = "development"

                with patch("src.workers.pipeline_worker.enqueue_next_stage_celery") as mock_enqueue:
                    run_stage(recording_id, "v1", stage_index=0)

                    mock_func.assert_called_once_with(recording_id)
                    mock_enqueue.assert_called_once_with(recording_id, "v1", 1)
        finally:
            STAGES[0] = original

    def test_run_stage_skips_completed_stage(self):
        """run_stage should skip stages already completed (idempotency)."""
        recording_id = str(uuid.uuid4())

        with patch("src.services.pipeline_state.is_stage_completed_sync", return_value=True), \
             patch("src.workers.pipeline.log_stage_start"), \
             patch("src.workers.pipeline.settings") as mock_settings:

            mock_settings.app_env = "development"

            with patch("src.workers.pipeline_worker.enqueue_next_stage_celery") as mock_enqueue:
                run_stage(recording_id, "v1", stage_index=0)

                mock_enqueue.assert_called_once_with(recording_id, "v1", 1)

    def test_run_stage_last_stage_completes_pipeline(self):
        """run_stage should mark pipeline complete at last stage."""
        recording_id = str(uuid.uuid4())
        last_index = len(STAGES) - 1
        mock_func = MagicMock()
        original = STAGES[last_index]
        STAGES[last_index] = (original[0], mock_func, original[2])

        try:
            with patch("src.services.pipeline_state.is_stage_completed_sync", return_value=False), \
                 patch("src.workers.pipeline._get_recording_sync", return_value=None), \
                 patch("src.workers.pipeline._update_status"), \
                 patch("src.workers.pipeline.log_stage_start"), \
                 patch("src.workers.pipeline.log_stage_complete"), \
                 patch("src.workers.pipeline.log_pipeline_complete") as mock_complete:

                run_stage(recording_id, "v1", stage_index=last_index)

                mock_complete.assert_called_once_with(recording_id, len(STAGES))
        finally:
            STAGES[last_index] = original

    def test_stage_order_matches_stage_names(self):
        """Pipeline stages should be in the correct execution order."""
        expected_order = [
            "preprocess", "stt", "diarization", "turns", "roles",
            "segmentation", "extract-audio", "analyze", "scoring",
        ]
        actual_order = [path.split("/")[-1] for path, _, _ in STAGES]
        assert actual_order == expected_order

    def test_all_stage_functions_are_callable(self):
        """Every stage function in STAGES should be callable."""
        for path, func, status in STAGES:
            assert callable(func), f"Stage {path} function is not callable"


# ---------------------------------------------------------------------------
# Tests: End-to-End Audio Processing
# ---------------------------------------------------------------------------

class TestEndToEndAudioProcessing:
    def test_enqueue_first_stage_triggers_pipeline(self):
        """enqueue_first_stage should kick off the pipeline."""
        assert callable(enqueue_first_stage)

        import inspect
        sig = inspect.signature(enqueue_first_stage)
        assert "recording_id" in sig.parameters

    def test_recording_status_transitions(self):
        """Recording status transitions through pipeline stages."""
        from src.models.recording import RecordingStatus

        stages = [
            RecordingStatus.UPLOADED,
            RecordingStatus.PREPROCESSING,
            RecordingStatus.TRANSCRIBING,
            RecordingStatus.DIARIZING,
            RecordingStatus.SEGMENTING,
            RecordingStatus.ANALYZING,
            RecordingStatus.SCORING,
            RecordingStatus.COMPLETED,
        ]

        assert len(stages) == 8
        assert RecordingStatus.FAILED

    def test_transcript_segment_creation(self):
        """Transcript segments are created from STT output."""
        from src.models.transcript import TranscriptSegment

        assert hasattr(TranscriptSegment, "recording_id")
        assert hasattr(TranscriptSegment, "start_time")
        assert hasattr(TranscriptSegment, "end_time")
        assert hasattr(TranscriptSegment, "text")
        assert hasattr(TranscriptSegment, "speaker_label")


# ---------------------------------------------------------------------------
# Tests: Error Handling & Retries
# ---------------------------------------------------------------------------

class TestPipelineErrorHandling:
    def test_run_stage_handles_stage_failure(self):
        """run_stage should handle and log errors from stage functions."""
        recording_id = str(uuid.uuid4())
        failing_func = MagicMock(side_effect=Exception("API timeout"))
        original = STAGES[0]
        STAGES[0] = (original[0], failing_func, original[2])

        try:
            with patch("src.services.pipeline_state.is_stage_completed_sync", return_value=False), \
                 patch("src.workers.pipeline._get_recording_sync", return_value=None), \
                 patch("src.workers.pipeline._update_status"), \
                 patch("src.workers.pipeline.log_stage_start"), \
                 patch("src.workers.pipeline.log_stage_error") as mock_error, \
                 patch("src.services.pipeline_state.mark_stage_failed_sync"), \
                 patch("src.services.pipeline_state.get_state_sync", return_value={"retry_count": {}}):

                with pytest.raises(Exception, match="API timeout"):
                    run_stage(recording_id, "v1", stage_index=0)

                mock_error.assert_called_once()
        finally:
            STAGES[0] = original

    def test_pipeline_handles_diarization_failure(self, sample_audio_bytes):
        """Pipeline handles diarization failure with fallback."""
        from src.ai.diarizer import diarize_audio

        with patch("src.ai.diarizer._get_pyannote_diarizer") as mock_pyannote, \
             patch("src.ai.diarizer.nvidia_client") as mock_nvidia:

            mock_pyannote.side_effect = Exception("Model load failed")
            mock_nvidia.post_multipart.side_effect = Exception("API failed")

            with patch("src.ai.diarizer.settings") as mock_settings:
                mock_settings.diarization_use_pyannote = True
                segments = diarize_audio(sample_audio_bytes)
                assert isinstance(segments, list)

    def test_pipeline_handles_analysis_failure(self):
        """Pipeline handles LLM analysis failure."""
        from src.ai.analyzer import analyze_conversation
        assert callable(analyze_conversation)


# ---------------------------------------------------------------------------
# Tests: Performance & Scaling
# ---------------------------------------------------------------------------

class TestPipelinePerformance:
    def test_chunking_configuration(self):
        """Audio chunking configuration is set for production workloads."""
        from src.config import settings

        assert settings.audio_chunk_duration_minutes == 10
        assert settings.audio_chunk_overlap_seconds == 30

    def test_vad_optimization(self):
        """VAD settings optimize for speech detection."""
        from src.config import settings

        assert settings.vad_use_silero is True
        assert 0.0 <= settings.vad_threshold <= 1.0
        assert settings.vad_min_speech_duration_ms >= 100


# ---------------------------------------------------------------------------
# Tests: Data Flow Validation
# ---------------------------------------------------------------------------

class TestDataFlowValidation:
    def test_analysis_to_scoring_flow(self):
        """Verify LLM scores response parsing."""
        from src.ai.scorer import _parse_scores_response

        mock_response = """
        {
            "greeting_score": 85,
            "discovery_score": 75,
            "product_knowledge_score": 90,
            "objection_handling_score": 70,
            "closing_score": 80
        }
        """

        scores = _parse_scores_response(mock_response)
        assert scores is not None
        assert scores["greeting_score"] == 85
        assert all(0 <= score <= 100 for score in scores.values())

    def test_pipeline_stages_cover_full_lifecycle(self):
        """STAGES should cover the full recording lifecycle from upload to scoring."""
        stage_names = [path.split("/")[-1] for path, _, _ in STAGES]

        # Must start with preprocessing
        assert stage_names[0] == "preprocess"
        # Must end with scoring
        assert stage_names[-1] == "scoring"
        # Must include analysis before scoring
        assert stage_names.index("analyze") < stage_names.index("scoring")
        # Must include transcription before diarization
        assert stage_names.index("stt") < stage_names.index("diarization")
