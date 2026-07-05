"""Stable identifier generator for runtime events and traces

IDs are short, sortable, and URL-safe. We use a time-ordered prefix so that NDJSON logs
and replay traces sort roughly chronologically by id alone, which is convenint when
eyeballing logs.
"""

from __future__ import annotations

import os
import time
from base64 import b32encode


def _short_id() -> str:
    """Return a compact, time-ordered, collision-resistant id."""
    now_ms = int(time.time() * 1000)
    time_bytes = now_ms.to_bytes(6, "big")
    rand_bytes = os.urandom(6)
    return b32encode(time_bytes + rand_bytes).decode("ascii").rstrip("=").lower()


def new_event_id() -> str:
    """Return a new event id, prefixed for readability in logs."""
    return f"evt_{_short_id()}"


def new_trace_id() -> str:
    """Return a new trace id spanning one end-to-end interaction."""
    return f"trc_{_short_id()}"


def new_session_id() -> str:
    """Return a new session id for one runtime session."""
    return f"ses_{_short_id()}"


def new_stream_id() -> str:
    """Return a new stream id for one source stream within a session."""
    return f"str_{_short_id()}"
