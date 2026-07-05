"""Canonical vocabulary shared by every producer and subscriber

Centralizing these strings the C-core protobuf, the Python agents, and the replay logs
aligned. Event-type strings are intentionally plain `str` constants (not an enum) so
new specialist agents can introduce their own types without editing a central enum;
`Modality` and `Lane` are closed sets, so they are `StrEnum`.
"""

from __future__ import annotations

from enum import StrEnum


class Modality(StrEnum):
    """High-level input/output modality."""

    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    FILE = "file"
    SENSOR = "sensor"
    CONTROL = "control"
    STATE = "state"
    MIXED = "mixed"


class Lane(StrEnum):
    """Processing lane that determines latency/priority class.

    FAST  - low-latency partial understanding of the most recent chunk.
    RETRO - periodic re-evaluation/stitching that may revise earlier output.
    FINAL - authoritative output at an utterance/task/control boundary.
    """

    FAST = "fast"
    RETRO = "retro"
    FINAL = "final"


# --- Event types ---
# Namespaced "domain.action" strings. Producers publish these; agents subscribe by exact
# type or prefix (see InProcBus in A2).

# Ingest (Produced by C-core / simulators)
EVT_CHUNK_CREATED = "chunk.created"

# Speech-to-text
EVT_TRANSCRIPT_PARTIAL = "transcript.partial"
EVT_TRANSCRIPT_FINAL = "transcript.final"
EVT_TRANSCRIPT_REVISED = "transcript.revised"

# Affect / scene understanding
EVT_EMOTION_OBSERVED = "emotion.observed"
EVT_SCENE_OBSERVED = "scene.observed"
EVT_SENSOR_READING = "sensor.reading"

# Fusion / reasoning
EVT_WORLD_STATE_UPDATED = "world_state.updated"
EVT_PLAN_DECISION = "plan.decision"

# Output
EVT_RESPONSE_TEXT = "response.text"
EVT_SPEECH_EMITTED = "speech.emitted"

# Actuation (later milestones)
EVT_ACTION_INTENT = "action.intent"


# Payload schema files, kept parallel to /schemas for validation + replay
class PayloadSchema(StrEnum):
    CHUNK = "chunk-event.json"
    TRANSCRIPT = "transcript-revision.json"
    EMOTION = "emotion-observation.json"
    SENSOR = "sensor-reading.json"
    WORLD_STATE = "world-state.json"
    PLAN_DECISION = "plan-decision.json"
    RESPONSE = "response-text.json"
    ACTION_INTENT = "action-intent.json"
