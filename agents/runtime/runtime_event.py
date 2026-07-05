"""The runtime event envelope: the single unit that flows across the bus.

Every piece of media and every derived result is an `Event`. Events are immutable; an
agent never mutates an event it received. Instead it `derives` a child event, which
preserves lineage (`parent_event_ids`) and propagates the `trace_id`, `session_id`.

This module is deliberately transport-free. `to_dict`/`from_dict` give us
NDJSON logging and replay today; the same shape maps 1:1 onto the protobuf
message we define for gRPC in Track C.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Self

from agents.runtime.runtime_event_types import Lane, Modality
from agents.runtime.runtime_ids import new_event_id, new_trace_id


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class Event:
    """One immmutable runtime event envelope

    Attributes:
        event_id: Unique id for this event.
        event_type: Canonical "domain.action" type (see event_types).
        session_id: Session this event belongs to.
        stream_id: Source stream within the session.
        modality: High-level modality of the underlying signal.
        producer: Name of the component that emitted this event.
        created_at: ISO-8601 UTC creation timestamp.
        trace_id: End-to-end interaction id, propagated across derivations.
        lane: Processing lane / priority class.
        revision: Monotonic revision; higher supersedes lower for same lineage.
        parent_event_ids: Direct upstream events this was derived from.
        node_id: Originating node (for distributed routing/telemetry).
        correlation_id: Optional sub-operation correlation id.
        payload_schema: Filename of the schema describing `payload`.
        payload: Event body. For media, this holds a `payload_ref` (shm key /
            offset / len) rather than raw bytes, so large media stays in the
            C-core ring instead of being copied across the bus.
    """

    event_type: str
    session_id: str
    stream_id: str
    modality: Modality
    producer: str
    payload_schema: str
    payload: dict[str, Any] = field(default_factory=dict)

    # Auto/derived metadata
    event_id: str = field(default_factory=new_event_id)
    created_at: str = field(default_factory=utc_now_iso)
    trace_id: str = field(default_factory=new_trace_id)
    lane: Lane = Lane.FAST
    revision: int = 0
    parent_event_ids: tuple[str, ...] = ()
    node_id: str = "local"
    correlation_id: str | None = None

    @classmethod
    def new(
        cls,
        *,
        event_type: str,
        session_id: str,
        stream_id: str,
        modality: Modality,
        producer: str,
        payload_schema: str,
        payload: dict[str, Any] | None = None,
        trace_id: str | None = None,
        lane: Lane = Lane.FAST,
        node_id: str = "local",
        correlation_id: str | None = None,
    ) -> Self:
        """Create a fresh root event (no parents). Use at ingress boundaries"""
        return cls(
            event_type=event_type,
            session_id=session_id,
            stream_id=stream_id,
            modality=modality,
            producer=producer,
            payload_schema=payload_schema,
            payload=payload or {},
            trace_id=trace_id or new_trace_id(),
            lane=lane,
            node_id=node_id,
            correlation_id=correlation_id,
        )

    def derive(
        self,
        *,
        event_type: str,
        producer: str,
        payload_schema: str,
        payload: dict[str, Any] | None = None,
        modality: Modality | None = None,
        lane: Lane | None = None,
        revision: int | None = None,
    ) -> Event:
        """Create a child event: propagates trace/session/stream, records lineage."""
        return Event(
            event_type=event_type,
            session_id=self.session_id,
            stream_id=self.stream_id,
            modality=modality or self.modality,
            producer=producer,
            payload_schema=payload_schema,
            payload=payload or {},
            trace_id=self.trace_id,
            lane=lane or self.lane,
            revision=self.revision if revision is None else revision,
            parent_event_ids=(self.event_id,),
            node_id=self.node_id,
            correlation_id=self.correlation_id,
        )

    def with_revision(self, revision: int) -> Event:
        """Return a superseding copy with a bumped revision and fresh id."""
        return replace(self, revision=revision, event_id=new_event_id())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict (NDJSON logging / replay)."""
        d: dict[str, Any] = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "stream_id": self.stream_id,
            "modality": str(self.modality),
            "producer": self.producer,
            "created_at": self.created_at,
            "trace_id": self.trace_id,
            "lane": str(self.lane),
            "revision": self.revision,
            "parent_event_ids": list(self.parent_event_ids),
            "node_id": self.node_id,
            "payload_schema": self.payload_schema,
            "payload": self.payload,
        }

        if self.correlation_id is not None:
            d["correlation_id"] = self.correlation_id
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        """Reconstruct an Event from a logged/replayed dict."""
        return cls(
            event_type=d["event_type"],
            session_id=d["session_id"],
            stream_id=d["stream_id"],
            modality=Modality(d["modality"]),
            producer=d["producer"],
            payload_schema=d["payload_schema"],
            payload=d.get("payload", {}),
            event_id=d["event_id"],
            created_at=d["created_at"],
            trace_id=d.get("trace_id", ""),
            lane=Lane(d.get("lane", Lane.FAST)),
            revision=d.get("revision", 0),
            parent_event_ids=tuple(d.get("parent_event_ids", ())),
            node_id=d.get("node_id", "local"),
            correlation_id=d.get("correlation_id"),
        )
