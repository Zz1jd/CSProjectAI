from __future__ import annotations

from urllib.parse import urlsplit
from urllib.parse import urlunsplit


_OPENAI_ENDPOINT_SUFFIXES = (
    "/chat/completions",
    "/embeddings",
    "/responses",
    "/completions",
)


def normalize_openai_base_url(base_url: str) -> str:
    """Normalize OpenAI-compatible URLs to the base path expected by the SDK."""

    normalized = base_url.strip()
    if not normalized:
        return normalized
    if "://" not in normalized:
        normalized = f"https://{normalized.lstrip('/')}"

    parts = urlsplit(normalized)
    path = parts.path.rstrip("/")
    for suffix in _OPENAI_ENDPOINT_SUFFIXES:
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break

    return urlunsplit((parts.scheme or "https", parts.netloc, path, "", ""))