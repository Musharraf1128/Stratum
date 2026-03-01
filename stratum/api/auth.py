"""
Basic API key authentication for Stratum.

Checks the STRATUM_API_KEY environment variable. When the env var is unset,
all requests are allowed (dev mode). When set, mutating routes require a
valid Bearer token.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException


def verify_api_key(authorization: str = Header(None)) -> bool:
    """FastAPI dependency for API key verification.

    - If STRATUM_API_KEY env var is not set: all requests pass (dev mode).
    - If set: requests must include `Authorization: Bearer <key>`.
    """
    api_key = os.getenv("STRATUM_API_KEY")

    if api_key is None:
        return True  # Dev mode — no key required

    if not authorization or authorization != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True
