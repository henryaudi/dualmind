"""dualmind.types

Core primitive types shared across the entire DualMind runtime. These
mirror the protobuf definitions in proto/envelope.proto and serve as
the canonical Python representation of every message flowing through
the bus.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class Modality(Enum):
    Audio = "audio"
    Video = "video"
    Text = "text"


class Lane(Enum):
    Fast = "fast"
    Retro = "retro"
    Final = "final"


@dataclass(frozen=True)
class Envelope:
    type: str
    modality: Modality
    lane: Lane
    session: str
    seq: int
    payload: bytes
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    ts: float = field(default_factory=time.time)
    rev: int = 1

    def revise(self) -> Envelope:
        """Return a corrected copy with rev incremented.

        Used by the retro lane to supersede an earlier result without
        mutating the original.
        """
        return Envelope(
            type=self.type,
            modality=self.modality,
            lane=self.lane,
            session=self.session,
            seq=self.seq,
            payload=self.payload,
            id=self.id,
            ts=time.time(),
            rev=self.rev + 1,
        )
