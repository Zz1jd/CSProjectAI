from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from implementation import config as config_lib


class ConfigEnvFileTests(unittest.TestCase):
    def test_load_dotenv_map_parses_key_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dotenv_path = Path(tmp_dir) / ".env"
            dotenv_path.write_text(
                """
# comment line
FUNSEARCH_API_KEY=abc123
export FUNSEARCH_EMBEDDING_API_KEY='def456'
IGNORED_LINE
                """.strip()
                + "\n",
                encoding="utf-8",
            )

            loaded = config_lib._load_dotenv_map(dotenv_path)

            self.assertEqual(loaded.get("FUNSEARCH_API_KEY"), "abc123")
            self.assertEqual(loaded.get("FUNSEARCH_EMBEDDING_API_KEY"), "def456")
            self.assertNotIn("IGNORED_LINE", loaded)

    def test_read_env_str_prefers_process_environment(self) -> None:
        previous_cache = config_lib._DOTENV_CACHE
        previous_env = os.environ.get("FUNSEARCH_API_KEY")
        try:
            config_lib._DOTENV_CACHE = {"FUNSEARCH_API_KEY": "from-dotenv"}
            os.environ["FUNSEARCH_API_KEY"] = "from-env"

            self.assertEqual(config_lib._read_env_str("FUNSEARCH_API_KEY"), "from-env")
        finally:
            if previous_env is None:
                os.environ.pop("FUNSEARCH_API_KEY", None)
            else:
                os.environ["FUNSEARCH_API_KEY"] = previous_env
            config_lib._DOTENV_CACHE = previous_cache


if __name__ == "__main__":
    unittest.main()
