"""dualmind.workers.stt

Speech-to-text worker. Receives raw PCM float32 bytes from the audio
chunker and returns a UTF-8 encoded transcript. Consecutive partial
transcripts are merged using a token-overlap heuristic to suppress
duplicated words at chunk boundaries.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from faster_whisper import WhisperModel

from .base import Worker


class STTWorker(Worker):
    """Runs Whisper inference on a single audio chunk.

    Config keys
    -----------
    model_size    : str   — Whisper model variant (default "base.en")
    device        : str   — "cpu" or "cuda" (default "cpu")
    compute_type  : str   — quantisation (default "int8")
    sample_rate   : int   — must match AudioIngress (default 16000)
    language      : str   — ISO-639-1 code or None for auto (default "en")
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._sample_rate = int(config.get("sample_rate", 16_000))
        self._language = config.get("language", "en") or None
        self._model = WhisperModel(
            config.get("model_size", "base.en"),
            device=config.get("device", "cpu"),
            compute_type=config.get("compute_type", "int8"),
        )
        self._prev_tokens: list[str] = []

    # ------------------------------------------------------------------
    # Partial-transcript merge
    # ------------------------------------------------------------------

    @staticmethod
    def _longest_overlap(prev: list[str], curr: list[str]) -> int:
        """Return the length of the longest suffix of prev that is a prefix of curr."""
        max_overlap = min(len(prev), len(curr))
        for n in range(max_overlap, 0, -1):
            if prev[-n:] == curr[:n]:
                return n
        return 0

    def _merge(self, curr_tokens: list[str]) -> str:
        """Append only the novel tokens from curr onto the running transcript."""
        overlap = self._longest_overlap(self._prev_tokens, curr_tokens)
        new_tokens = curr_tokens[overlap:]
        self._prev_tokens = curr_tokens
        return " ".join(new_tokens)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _handle(self, payload: bytes) -> bytes:
        """Transcribe one PCM chunk and return de-duplicated UTF-8 text."""
        samples = np.frombuffer(payload, dtype=np.float32)
        segments, _ = self._model.transcribe(
            samples,
            language=self._language,
            vad_filter=False,
            word_timestamps=False,
        )
        tokens = " ".join(seg.text.strip() for seg in segments).split()
        text = self._merge(tokens)
        return text.encode()
