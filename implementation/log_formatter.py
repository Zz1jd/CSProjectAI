from __future__ import annotations

MAIN_DIVIDER = "=" * 63
SECONDARY_DIVIDER = "-" * 63
SAMPLE_GAP = "\n" * 3


def format_main_header(title: str) -> str:
    return f"{MAIN_DIVIDER}\n  {title}\n{MAIN_DIVIDER}"


def format_secondary_header(title: str) -> str:
    return f"\n  {title}\n{SECONDARY_DIVIDER}"


def format_divider() -> str:
    return SECONDARY_DIVIDER


def format_section_title(key: str, value: object) -> str:
    return f"{key}: {value}"


def format_debug_message(index: int, content: str) -> str:
    truncated = content[:100].replace("\n", " ")
    return f"DEBUG: Sample {index} prefix: {truncated}..."


def format_debug_empty(index: int) -> str:
    return f"DEBUG: Sample {index} is empty or too short!"


def format_evaluated_function_header() -> str:
    return "================= Evaluated Function ================="


def format_evaluated_function_footer() -> str:
    return "======================================================"


def format_eval_summary(valid: int, total: int, ratio: float) -> str:
    return f"EVAL_SUMMARY: valid={valid} total={total} ratio={ratio:.6f}"
