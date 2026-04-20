"""Very small logging shim used by project modules when absl-py isn't available.

This implements the small subset the codebase uses (`info`, `warning`, `error`, `debug`).
"""
import sys

def _print(prefix: str, *args, **kwargs):
    try:
        print(prefix, *args, **kwargs)
    except Exception:
        # Fallback to stdout
        sys.stdout.write(prefix + ' ' + ' '.join(str(a) for a in args) + '\n')

def info(*args, **kwargs):
    _print('', *args, **kwargs)

def warning(*args, **kwargs):
    _print('WARNING:', *args, **kwargs)

def error(*args, **kwargs):
    _print('ERROR:', *args, **kwargs)

def debug(*args, **kwargs):
    _print('DEBUG:', *args, **kwargs)
