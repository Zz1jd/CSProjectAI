import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from implementation import profile as profile_lib


class _DummySummaryWriter:
    def __init__(self, log_dir: str) -> None:
        self.log_dir = log_dir

    def add_scalar(self, *args, **kwargs) -> None:
        pass

    def add_scalars(self, *args, **kwargs) -> None:
        pass


class _DummyProgram:
    global_sample_nums = 1
    score = -1161.9876066089935
    sample_time = 1.25
    evaluate_time = 4.5

    def __str__(self) -> str:
        return "def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return -distance_data[current_node]"


class ProfileLoggingTests(unittest.TestCase):
    def test_profiler_emits_verbose_evaluated_function_log(self) -> None:
        original_writer = profile_lib.SummaryWriter
        profile_lib.SummaryWriter = _DummySummaryWriter
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                profiler = profile_lib.Profiler(log_dir=tmpdir)
                stream = io.StringIO()
                with redirect_stdout(stream):
                    profiler.register_function(_DummyProgram())

                output = stream.getvalue()
                self.assertIn("================= Evaluated Function =================", output)
                self.assertIn("Score        : -1161.9876066089935", output)
                self.assertTrue(os.path.exists(os.path.join(tmpdir, "samples", "samples_1.json")))
        finally:
            profile_lib.SummaryWriter = original_writer

    def test_profiler_fails_explicitly_when_tensorboard_writer_is_unavailable(self) -> None:
        original_writer = profile_lib.SummaryWriter
        original_error = profile_lib._SUMMARY_WRITER_IMPORT_ERROR
        profile_lib.SummaryWriter = None
        profile_lib._SUMMARY_WRITER_IMPORT_ERROR = ModuleNotFoundError("No module named 'tensorboard'")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with self.assertRaisesRegex(RuntimeError, "TensorBoard SummaryWriter is unavailable"):
                    profile_lib.Profiler(log_dir=tmpdir)
        finally:
            profile_lib.SummaryWriter = original_writer
            profile_lib._SUMMARY_WRITER_IMPORT_ERROR = original_error


if __name__ == "__main__":
    unittest.main()
