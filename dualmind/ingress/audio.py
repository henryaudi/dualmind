"""dualmind.ingress.audio

Microphone capture ingress. Opens the default input device via
sounddevice, applies VAD to discard silence, and emits fixed-size
PCM chunks as raw bytes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import numpy as np
import sounddevice as sd

from .base import Ingress

_RMS_SILENCE_THRESHOLD = 0.01
_SILENCE_CHUNKS_MAX = 10


class AudioIngress(Ingress):
    """Captures PCM audio from the default microphone.

    Config keys
    -----------
    sample_rate   : int   — samples per second (default 16000)
    chunk_ms      : int   — window size in milliseconds (default 300)
    channels      : int   — input channels (default 1)
    dtype         : str   — numpy dtype string (default "float32")
    """

    def __init__(self, config: dict[str, Any], publish: Callable[[bytes], None]) -> None:
        super().__init__(config, publish)
        self._sample_rate = int(config.get("sample_rate", 16_000))
        self._chunk_ms = int(config.get("chunk_ms", 300))
        self._channels = int(config.get("channels", 1))
        self._dtype = str(config.get("dtype", "float32"))
        self._chunk_frames = int(self._sample_rate * self._chunk_ms / 1000)

    @staticmethod
    def _rms(samples: np.ndarray) -> float:
        """Root-mean-square energy used as a silence gate."""
        return float(np.sqrt(np.mean(samples**2)))

    def _capture(self) -> Iterator[bytes]:
        """Yield PCM float32 chunks from the mic, skipping sustained silence."""
        silence_count = 0

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype=self._dtype,
            blocksize=self._chunk_frames,
        ) as stream:
            while self._running:
                frames, _ = stream.read(self._chunk_frames)
                samples = frames[:, 0] if self._channels > 1 else frames.flatten()

                if self._rms(samples) < _RMS_SILENCE_THRESHOLD:
                    silence_count += 1
                    if silence_count > _SILENCE_CHUNKS_MAX:
                        continue
                else:
                    silence_count = 0

                yield samples.astype(np.float32).tobytes()
