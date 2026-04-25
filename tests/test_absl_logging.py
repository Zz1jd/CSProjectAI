import unittest
from pathlib import Path


class AbslDependencyTests(unittest.TestCase):
    def test_repository_does_not_shadow_installed_absl_py(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        self.assertFalse(
            (project_root / "absl").exists(),
            "Remove the vendored absl shim so Colab can import real absl-py.",
        )


if __name__ == "__main__":
    unittest.main()
