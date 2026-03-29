from __future__ import annotations

import re
from dataclasses import dataclass

from config import get_settings

settings = get_settings()

# ── Patterns that signal prompt injection or abuse ────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"you\s+are\s+now\s+(?:an?\s+)?(?:evil|unrestricted|jailbroken)",
        r"disregard\s+your\s+(previous\s+)?instructions?",
        r"act\s+as\s+(?:if\s+you\s+(?:have\s+)?no\s+restrictions?|dan|evil)",
        r"repeat\s+after\s+me",
        r"system\s*prompt",
        r"<\s*script",                  # XSS attempt
        r"--\s*drop\s+table",           # SQL injection attempt
        r"\bexec\s*\(",                 # code execution attempt
        r"bypass\s+(safety|filter|guard)",
    ]
]

# ── Patterns that should never appear in output ───────────────────────────────
_SENSITIVE_OUTPUT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(?:api[_\s]?key|secret[_\s]?key)\s*[:=]\s*\S+",
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",   # email
        r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",                 # credit card
        r"\bpassword\s*[:=]\s*\S+",
        r"Bearer\s+[A-Za-z0-9\-._~+\/]+=*",                          # bearer token
    ]
]


@dataclass(slots=True)
class FilterResult:
    passed: bool
    reason: str = ""


def filter_input(user_input: str) -> FilterResult:
    """Validate user input before passing it to the agent."""

    # Length guard
    if not user_input.strip():
        return FilterResult(passed=False, reason="Input must not be empty.")

    if len(user_input) > settings.max_input_length:
        return FilterResult(
            passed=False,
            reason=f"Input exceeds maximum length of {settings.max_input_length} characters.",
        )

    # Injection detection
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(user_input):
            return FilterResult(
                passed=False,
                reason=f"Input blocked: potential prompt injection detected ({pattern.pattern!r}).",
            )

    return FilterResult(passed=True)


def filter_output(output: str) -> FilterResult:
    """Scan agent output for sensitive data before returning to the caller."""

    if len(output) > settings.max_output_length:
        return FilterResult(
            passed=False,
            reason=f"Output exceeded maximum length of {settings.max_output_length} characters.",
        )

    for pattern in _SENSITIVE_OUTPUT_PATTERNS:
        if pattern.search(output):
            return FilterResult(
                passed=False,
                reason=f"Output blocked: sensitive data detected ({pattern.pattern!r}).",
            )

    return FilterResult(passed=True)


def sanitize_output(output: str) -> str:
    """Redact sensitive patterns from output instead of blocking entirely."""
    for pattern in _SENSITIVE_OUTPUT_PATTERNS:
        output = pattern.sub("[REDACTED]", output)
    return output