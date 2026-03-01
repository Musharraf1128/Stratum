"""
In-memory per-process rate limiter for agent call frequency.

This is a simple token-bucket implementation for v0. Not distributed —
each process maintains its own rate limit state.
"""
from __future__ import annotations

import time


class InMemoryRateLimiter:
    """Per-process rate limiting. Not distributed — v0 only."""

    def __init__(self):
        self._last_call: dict[str, float] = {}  # agent_id -> timestamp

    def check_and_record(self, agent_id: str, rate_limit_rps: float) -> bool:
        """Returns True if the call is allowed. Records call time if allowed.

        Args:
            agent_id: The agent identifier to rate-limit.
            rate_limit_rps: Maximum calls per second for this agent.

        Returns:
            True if allowed, False if rate-limited.
        """
        if rate_limit_rps <= 0:
            return True  # No rate limit configured

        now = time.monotonic()
        min_interval = 1.0 / rate_limit_rps
        last = self._last_call.get(agent_id)

        if last is not None and (now - last) < min_interval:
            return False

        self._last_call[agent_id] = now
        return True

    def reset(self) -> None:
        """Clear all rate limit state."""
        self._last_call.clear()


# Global singleton
RATE_LIMITER = InMemoryRateLimiter()
