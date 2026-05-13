"""dualmind.workers.base

Abstract base class for all inference workers. A worker receives a raw
payload as bytes, runs a model, and returns a result as bytes. No IO,
no threading, no routing — pure inference.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Worker(ABC):
    """Base for all inference workers (STT, vision, LLM).

    The C runtime owns the thread this runs on and decides when to call
    it. _handle() must be a pure function: bytes in, bytes out.

    Config keys are worker-specific; see each concrete subclass.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    @abstractmethod
    def _handle(self, payload: bytes) -> bytes:
        """Run inference on payload and return a serialised result."""
