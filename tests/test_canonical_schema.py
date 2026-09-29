"""
Unit tests for canonical_schema module.

Tests immutability, validation, and constraint enforcement.
"""

import pytest
from datetime import datetime
from canonical_schema import CanonicaltTelemetry, NodeStatus


class TestNodeStatus:
    """Test NodeStatus enum."""
    
    def test_valid_statuses(self):
        """Test all valid status values."""
        assert NodeStatus.UP.value == "UP"
        assert NodeStatus.DEGRADED.value == "DEGRADED"
        assert NodeStatus.DOWN.value == "DOWN"
    
    def test_enum_membership(self):
        """Test enum membership checks."""
        assert NodeStatus.UP in NodeStatus
        assert "UP" not in NodeStatus  # Strings don't work


class TestCanonicaltTelemetry:
    """Test CanonicaltTelemetry dataclass."""
    
    def test_valid_instantiation(self):
        """Test valid instantiation with all fields."""
        telemetry = CanonicaltTelemetry(
            node_id="node-001",
            status=NodeStatus.UP,
            latency_ms=10.5,
            packet_loss=0.1,
            timestamp="2026-09-29T12:00:00Z",
            validated_token="test_token_001"
        )
        
        assert telemetry.node_id == "node-001"
        assert telemetry.status == NodeStatus.UP
        assert telemetry.latency_ms == 10.5
        assert telemetry.packet_loss == 0.1
        assert telemetry.timestamp == "2026-09-29T12:00:00Z"
        assert telemetry.validated_token == "test_token_001"
    
    def test_immutability(self):
        """Test that instances are immutable (frozen)."""
        telemetry = CanonicaltTelemetry(
            node_id="node-001",
            status=NodeStatus.UP,
            latency_ms=10.5,
            packet_loss=0.1,
            timestamp="2026-09-29T12:00:00Z"
        )
        
        with pytest.raises(AttributeError):
            telemetry.node_id = "node-002"
        
        with pytest.raises(AttributeError):
            telemetry.latency_ms = 20.0
    
    def test_invalid_node_id_empty_string(self):
        """Test validation rejects empty node_id."""
        with pytest.raises(ValueError, match="node_id must be non-empty string"):
            CanonicaltTelemetry(
                node_id="",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_node_id_none(self):
        """Test validation rejects None node_id."""
        with pytest.raises(ValueError, match="node_id must be non-empty string"):
            CanonicaltTelemetry(
                node_id=None,  # type: ignore
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_status_type(self):
        """Test validation rejects non-enum status."""
        with pytest.raises(ValueError, match="status must be NodeStatus enum"):
            CanonicaltTelemetry(
                node_id="node-001",
                status="up",  # type: ignore
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_latency_negative(self):
        """Test validation rejects negative latency."""
        with pytest.raises(ValueError, match="latency_ms must be non-negative number"):
            CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=-10.0,
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_packet_loss_too_high(self):
        """Test validation rejects packet_loss > 100.0."""
        with pytest.raises(ValueError, match="packet_loss must be 0.0-100.0"):
            CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=150.0,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_packet_loss_negative(self):
        """Test validation rejects negative packet_loss."""
        with pytest.raises(ValueError, match="packet_loss must be 0.0-100.0"):
            CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=-0.1,
                timestamp="2026-09-29T12:00:00Z"
            )
    
    def test_invalid_timestamp_empty(self):
        """Test validation rejects empty timestamp."""
        with pytest.raises(ValueError, match="timestamp must be non-empty string"):
            CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp=""
            )
    
    def test_invalid_timestamp_format(self):
        """Test validation rejects malformed ISO 8601 timestamp."""
        with pytest.raises(ValueError, match="timestamp must be valid ISO 8601"):
            CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp="not-a-timestamp"
            )
    
    def test_valid_timestamp_variants(self):
        """Test valid ISO 8601 timestamp formats."""
        timestamps = [
            "2026-09-29T12:00:00Z",
            "2026-09-29T12:00:00+00:00",
            "2026-09-29T12:00:00.123Z",
        ]
        
        for ts in timestamps:
            telemetry = CanonicaltTelemetry(
                node_id="node-001",
                status=NodeStatus.UP,
                latency_ms=10.0,
                packet_loss=0.0,
                timestamp=ts
            )
            assert telemetry.timestamp == ts
    
    def test_optional_validated_token(self):
        """Test validated_token is optional."""
        telemetry = CanonicaltTelemetry(
            node_id="node-001",
            status=NodeStatus.UP,
            latency_ms=10.0,
            packet_loss=0.0,
            timestamp="2026-09-29T12:00:00Z"
        )
        
        assert telemetry.validated_token is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        telemetry = CanonicaltTelemetry(
            node_id="node-001",
            status=NodeStatus.UP,
            latency_ms=10.5,
            packet_loss=0.1,
            timestamp="2026-09-29T12:00:00Z",
            validated_token="token-001"
        )
        
        result = telemetry.to_dict()
        
        assert result["node_id"] == "node-001"
        assert result["status"] == "UP"
        assert result["latency_ms"] == 10.5
        assert result["packet_loss"] == 0.1
        assert result["timestamp"] == "2026-09-29T12:00:00Z"
        assert result["validated_token"] == "token-001"
    
    def test_boundary_values(self):
        """Test boundary condition values."""
        # Minimum valid values
        telemetry_min = CanonicaltTelemetry(
            node_id="a",
            status=NodeStatus.DOWN,
            latency_ms=0.0,
            packet_loss=0.0,
            timestamp="2026-09-29T12:00:00Z"
        )
        assert telemetry_min.latency_ms == 0.0
        assert telemetry_min.packet_loss == 0.0
        
        # Maximum valid values
        telemetry_max = CanonicaltTelemetry(
            node_id="x" * 1000,
            status=NodeStatus.DEGRADED,
            latency_ms=999999.99,
            packet_loss=100.0,
            timestamp="2026-09-29T12:00:00Z"
        )
        assert telemetry_max.packet_loss == 100.0
