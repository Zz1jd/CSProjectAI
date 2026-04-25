import io
import unittest
from contextlib import redirect_stdout

from absl import logging


class AbslLoggingTests(unittest.TestCase):
    def test_info_uses_target_prefix_style_and_printf_formatting(self) -> None:
        stream = io.StringIO()
        with redirect_stdout(stream):
            logging.info("Best score of island %d increased to %s", 0, -1161.98)

        self.assertEqual(
            stream.getvalue(),
            "INFO:absl:Best score of island 0 increased to -1161.98\n",
        )


if __name__ == "__main__":
    unittest.main()
