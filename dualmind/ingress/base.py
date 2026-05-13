"""dualmind.ingress.base

Abstract base class for all input sources. Concrete subclasses open a
hardware device, yield raw buffers from _capture(), and push each chunk
to the runtime via the publish callable supplied at construction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from typing import Any


class Ingress(ABC):
    """Base for all input sources (e.g. microphone, camera, file, network).

    Subclasses implement _capture() as a generator that yields raw
    buffers. The base class drives the capture loop and forwards each
    buffer to the publish callable — Phase 1 passes a Python bus method;
    Phase 5 swaps in dm_push_audio / dm_push_video from the C runtime.
    """

    def __init__(self, config: dict[str, Any], publish: Callable[[bytes], None]) -> None:
        self._config = config
        self._publish = publish
        self._running = False

    def open(self) -> None:
        """Open the hardware device. Called once before the capture loop."""

    def close(self) -> None:
        """Release the hardware device. Called once after the capture loop."""

    @abstractmethod
    def _capture(self) -> Iterator[bytes]:
        """Yield raw buffers until stop() is called."""

    def run(self) -> None:
        """Open the device, stream chunks to the runtime, then close."""
        self._running = True
        self.open()
        try:
            for chunk in self._capture():
                if not self._running:
                    break
                self._publish(chunk)
        finally:
            self.close()
            self._running = False

    def stop(self) -> None:
        """Signal the capture loop to exit after the current chunk."""
        self._running = False
