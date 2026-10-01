"""Canonical schema for the netpulse-noc telemetry contract.

This module defines the immutable source of truth used by the StructuralAnchor and
server ingestion layer. Structure is treated as an ex-ante invariant, and the
schema is enforced before any application logic can operate on telemetry values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class NodeStatus(str, Enum):
    """Canonical network node status values."""

    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


@dataclass(frozen=True)
class CanonicalTelemetry:
    """Immutable canonical telemetry record.

    Every telemetry packet accepted by the system must conform to this structure.
    Mutation is prevented by frozen=True and validation occurs before the object is
    created.
    """

    node_id: str
    status: NodeStatus
    latency_ms: float
    packet_loss: float
    timestamp: str
    validated_token: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id must be a non-empty string")
        if not isinstance(self.status, NodeStatus):
            raise ValueError("status must be a NodeStatus enum")
        if not isinstance(self.latency_ms, (int, float)) or self.latency_ms < 0:
            raise ValueError("latency_ms must be a non-negative number")
        if not isinstance(self.packet_loss, (int, float)) or not 0.0 <= self.packet_loss <= 100.0:
            raise ValueError("packet_loss must be between 0.0 and 100.0")
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string")
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be valid ISO 8601") from exc

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "latency_ms": float(self.latency_ms),
            "packet_loss": float(self.packet_loss),
            "timestamp": self.timestamp,
            "validated_token": self.validated_token,
        }


# Backwards-compatible alias used by the earlier scaffold and tests.
CanonicaltTelemetry = CanonicalTelemetry

__all__ = ["NodeStatus", "CanonicalTelemetry", "CanonicaltTelemetry"]
