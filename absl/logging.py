"""Very small logging shim used by project modules when absl-py isn't available.

This implements the small subset the codebase uses (`info`, `warning`, `error`, `debug`).
"""
import sys


def _format_message(message, *args) -> str:
    """Apply printf-style formatting used by logging.info(msg, *args)."""
    if not args:
        return str(message)
    try:
        return str(message) % args
    except Exception:
        # Keep output readable even if formatting fails.
        return " ".join([str(message), *(str(arg) for arg in args)])


def _print(prefix: str, message, *args, **kwargs):
    text = _format_message(message, *args)
    line = f"{prefix} {text}" if prefix else text
    try:
        print(line, **kwargs)
    except Exception:
        # Fallback to stdout
        sys.stdout.write(line + "\n")


def info(message, *args, **kwargs):
    _print("INFO:absl:", message, *args, **kwargs)


def warning(message, *args, **kwargs):
    _print("WARNING:absl:", message, *args, **kwargs)


def error(message, *args, **kwargs):
    _print("ERROR:absl:", message, *args, **kwargs)


def debug(message, *args, **kwargs):
    _print("DEBUG:absl:", message, *args, **kwargs)
