import tempfile
import unittest
from unittest import mock

from implementation import config as config_lib
from scripts import run_rag_eval
from scripts.compare_rag import ParsedRun


class RunRagEvalTests(unittest.TestCase):
    def test_run_rag_eval_uses_runtime_default_dataset_path(self) -> None:
        runtime_defaults = config_lib.RuntimeDefaults(dataset_path="./custom/setB")
        run_logged_experiment = mock.Mock()
        parsed_run = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=1,
            metadata={},
            total_valid_evals=1,
            total_eval_attempts=1,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch(
                "scripts.run_rag_eval._load_runtime_bindings",
                return_value=(
                    runtime_defaults,
                    config_lib.Config,
                    None,
                    mock.Mock(return_value="20260426_010101"),
                    run_logged_experiment,
                ),
            ), mock.patch(
                "scripts.run_rag_eval.parse_run_log",
                return_value=parsed_run,
            ):
                run_rag_eval.run_rag_eval(
                    experiment_config=run_rag_eval.ExperimentRunConfig(
                        budget=1,
                        results_dir=temp_dir,
                        log_dir="../logs/test_rag_eval",
                    ),
                    model_spec=run_rag_eval.ModelSpec(
                        model_name="gpt-3.5-turbo",
                        result_label="test",
                    ),
                )

        dataset_path = run_logged_experiment.call_args.kwargs["dataset_path"]
        self.assertEqual(dataset_path, "./custom/setB")
        self.assertIsInstance(dataset_path, str)


if __name__ == "__main__":
    unittest.main()
