"""Tests for Celery worker transport layer and stage function contracts.

These tests validate the ACTUAL pipeline architecture:
  - ``pipeline_worker.py`` is the Celery transport (thin wrapper)
  - ``pipeline.py :: run_stage()`` is the orchestrator (business logic)
  - Stage functions (preprocessing, transcription, etc.) are plain Python functions

Architecture summary:
  enqueue_first_stage()  -->  execute_stage.delay()  -->  run_stage()  -->  stage_func()
  [pipeline.py]              [pipeline_worker.py]      [pipeline.py]     [workers/*.py]
"""
import inspect
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if Celery is not installed
pytest.importorskip("celery", reason="Celery not installed")


# ---------------------------------------------------------------------------
# Celery Transport Layer (pipeline_worker.py)
# ---------------------------------------------------------------------------


class TestCeleryTransportLayer:
    """Verify pipeline_worker.py is a thin Celery wrapper."""

    def test_execute_stage_is_registered_celery_task(self):
        """execute_stage should be registered in the Celery task registry."""
        from src.workers.celery_app import app

        assert "src.workers.pipeline_worker.execute_stage" in app.tasks

    def test_execute_stage_signature(self):
        """execute_stage accepts (recording_id, pipeline_version, stage_index, force_rerun)."""
        from src.workers.pipeline_worker import execute_stage

        sig = inspect.signature(execute_stage)
        params = list(sig.parameters.keys())
        # 'self' is injected by Celery bind=True; the user-facing params are:
        assert "recording_id" in params
        assert "pipeline_version" in params
        assert "stage_index" in params
        assert "force_rerun" in params

    def test_execute_stage_has_celery_methods(self):
        """execute_stage should expose Celery task methods (.delay, .apply_async)."""
        from src.workers.pipeline_worker import execute_stage

        assert hasattr(execute_stage, "delay")
        assert hasattr(execute_stage, "apply_async")

    def test_execute_stage_delegates_to_run_stage(self):
        """execute_stage should call pipeline.run_stage() -- not duplicate logic."""
        from src.workers.pipeline_worker import execute_stage

        with patch("src.workers.pipeline_worker.run_stage") as mock_run:
            # bind=True: Celery injects self automatically when called directly
            execute_stage("rec-1", "v1", 0, False)

            mock_run.assert_called_once_with("rec-1", "v1", 0, False)

    def test_enqueue_next_stage_celery_exists(self):
        """enqueue_next_stage_celery should exist for dev-mode dispatch."""
        from src.workers.pipeline_worker import enqueue_next_stage_celery

        assert callable(enqueue_next_stage_celery)

    def test_enqueue_next_stage_celery_calls_delay(self):
        """enqueue_next_stage_celery should call execute_stage.delay()."""
        from src.workers.pipeline_worker import enqueue_next_stage_celery

        with patch("src.workers.pipeline_worker.execute_stage") as mock_task:
            enqueue_next_stage_celery("rec-1", "v1", 3)

            mock_task.delay.assert_called_once_with("rec-1", "v1", 3)

    def test_enqueue_next_stage_celery_signature(self):
        """enqueue_next_stage_celery accepts (recording_id, pipeline_version, stage_index)."""
        from src.workers.pipeline_worker import enqueue_next_stage_celery

        sig = inspect.signature(enqueue_next_stage_celery)
        params = list(sig.parameters.keys())
        assert params == ["recording_id", "pipeline_version", "stage_index"]


# ---------------------------------------------------------------------------
# Pipeline Stage Configuration (pipeline.py :: STAGES)
# ---------------------------------------------------------------------------


class TestPipelineStageConfiguration:
    """Verify pipeline.py STAGES tuple list is correctly wired."""

    def test_stages_has_9_entries(self):
        """Pipeline should define exactly 9 stages."""
        from src.workers.pipeline import STAGES

        assert len(STAGES) == 9

    def test_each_stage_is_path_func_status_tuple(self):
        """Each stage should be (path, callable, status_label)."""
        from src.workers.pipeline import STAGES

        for path, func, status in STAGES:
            assert isinstance(path, str) and path.startswith("/stage/")
            assert callable(func), f"Stage {path} function is not callable"
            assert isinstance(status, str) and len(status) > 0


# ---------------------------------------------------------------------------
# Stage Functions Are Plain Python Functions (Not Celery Tasks)
# ---------------------------------------------------------------------------


class TestStageFunctionContracts:
    """Verify stage functions are plain Python functions that accept recording_id."""

    STAGE_FUNCTIONS = [
        ("src.workers.preprocessing", "preprocess_audio"),
        ("src.workers.transcription", "dispatch_transcription"),
        ("src.workers.diarization", "dispatch_diarization"),
        ("src.workers.turn_builder", "build_conversation_turns"),
        ("src.workers.role_classification", "classify_speaker_roles"),
        ("src.workers.segmentation", "segment_conversations"),
        ("src.workers.audio_stitcher", "extract_conversation_audio"),
        ("src.workers.analysis", "analyze_conversations"),
        ("src.workers.scoring", "score_salesperson"),
    ]

    @pytest.mark.parametrize("module_path,func_name", STAGE_FUNCTIONS)
    def test_stage_function_is_callable(self, module_path, func_name):
        """Each stage function should be importable and callable."""
        import importlib

        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        assert callable(func)

    @pytest.mark.parametrize("module_path,func_name", STAGE_FUNCTIONS)
    def test_stage_function_accepts_recording_id(self, module_path, func_name):
        """Each stage function should accept recording_id as first parameter."""
        import importlib

        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert params[0] == "recording_id", (
            f"{func_name} first param is '{params[0]}', expected 'recording_id'"
        )


# ---------------------------------------------------------------------------
# Preprocessing Constants
# ---------------------------------------------------------------------------


class TestPreprocessingConstants:
    """Verify preprocessing worker constants."""

    def test_target_sample_rate(self):
        from src.workers.preprocessing import TARGET_SAMPLE_RATE

        assert TARGET_SAMPLE_RATE == 16000

    def test_target_channels(self):
        from src.workers.preprocessing import TARGET_CHANNELS

        assert TARGET_CHANNELS == 1

    def test_silence_threshold_db(self):
        from src.workers.preprocessing import SILENCE_THRESHOLD_DB

        assert SILENCE_THRESHOLD_DB == -40

    def test_silence_gap_ms(self):
        from src.workers.preprocessing import SILENCE_GAP_MS

        assert SILENCE_GAP_MS == 30000  # 30 seconds

    def test_target_format(self):
        from src.workers.preprocessing import TARGET_FORMAT

        assert TARGET_FORMAT == "wav"


# ---------------------------------------------------------------------------
# Dual-Mode Dispatcher (pipeline.py :: enqueue_first_stage)
# ---------------------------------------------------------------------------


class TestDualModeDispatcher:
    """Verify the dev/prod dispatch routing in pipeline.py."""

    def test_enqueue_first_stage_exists(self):
        """enqueue_first_stage should be the pipeline entry point."""
        from src.workers.pipeline import enqueue_first_stage

        assert callable(enqueue_first_stage)

    def test_enqueue_first_stage_signature(self):
        """enqueue_first_stage accepts (recording_id, pipeline_version)."""
        from src.workers.pipeline import enqueue_first_stage

        sig = inspect.signature(enqueue_first_stage)
        params = list(sig.parameters.keys())
        assert "recording_id" in params
        assert "pipeline_version" in params

    @patch("src.workers.pipeline.settings")
    def test_dev_mode_dispatches_via_celery(self, mock_settings):
        """In development mode, enqueue_first_stage should use Celery."""
        mock_settings.app_env = "development"

        from src.workers.pipeline import enqueue_first_stage

        with patch("src.workers.pipeline_worker.execute_stage") as mock_task:
            enqueue_first_stage("rec-1", "v1")

            mock_task.delay.assert_called_once_with("rec-1", "v1", 0, False)
