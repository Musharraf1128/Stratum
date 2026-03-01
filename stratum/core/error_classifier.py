"""
Error classifier for retry decisions.

Categorizes exceptions as retryable (transient) or non-retryable (permanent)
to decide whether the retry loop should continue.
"""
from __future__ import annotations


RETRYABLE_ERROR_PATTERNS = [
    "connection",
    "timeout",
    "rate limit",
    "503",
    "502",
    "429",
    "service unavailable",
    "temporarily unavailable",
    "server error",
]

NON_RETRYABLE_ERROR_PATTERNS = [
    "invalid api key",
    "permission",
    "invalid input",
    "400",
    "401",
    "403",
    "unauthorized",
    "forbidden",
    "not found",
    "validation error",
]


def is_retryable(error: Exception) -> bool:
    """Check whether an error is retryable.

    Returns True if the error message matches a retryable pattern,
    False if it matches a non-retryable pattern,
    True by default for unknown errors (retry is safer).
    """
    msg = str(error).lower()

    # Check non-retryable first (more specific)
    for pattern in NON_RETRYABLE_ERROR_PATTERNS:
        if pattern in msg:
            return False

    # Check retryable patterns
    for pattern in RETRYABLE_ERROR_PATTERNS:
        if pattern in msg:
            return True

    # Default: retry on unknown errors (safer for transient issues)
    return True
