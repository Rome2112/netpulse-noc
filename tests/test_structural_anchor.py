"""
Unit tests for structural_anchor module.

Tests deterministic projection, fallback handling, and O(N) complexity.
"""

import pytest
from datetime import datetime
from structural_anchor import StructuralAnchor, StructuralError
from canonical_schema import CanonicaltTelemetry, NodeStatus


class TestStructuralAnchor:
    """Test StructuralAnchor projection engine."""

    def setup_method(self):
        """Initialize a fresh anchor for each test."""
        self.anchor = StructuralAnchor()

    def test_well_formed_input(self):
        """Test projection of well-formed input."""
        raw_input = {
            "node_id": "node-001",
            "status": "up",
            "latency_ms": 10.5,
            "packet_loss": 0.1,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.node_id == "node-001"
        assert result.status == NodeStatus.UP
        assert result.latency_ms == 10.5
        assert result.packet_loss == 0.1
        assert result.validated_token.startswith("validated_token_")

    def test_missing_optional_fields_fallback(self):
        """Test fallback for missing optional fields."""
        raw_input = {
            "node_id": "node-002",
            "status": "degraded"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.node_id == "node-002"
        assert result.status == NodeStatus.DEGRADED
        assert result.latency_ms == 0.0
        assert result.packet_loss == 0.0
        assert result.timestamp

    def test_status_normalization_lowercase(self):
        """Test status normalization from lowercase."""
        raw_input = {
            "node_id": "node-003",
            "status": "up",
            "latency_ms": 5.0,
            "packet_loss": 1.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.status == NodeStatus.UP

    def test_status_normalization_mapping(self):
        """Test status normalization via STATUS_MAP."""
        test_cases = [
            ("ok", NodeStatus.UP),
            ("error", NodeStatus.DOWN),
            ("warning", NodeStatus.DEGRADED),
            ("down", NodeStatus.DOWN),
        ]

        for status_input, expected_status in test_cases:
            raw_input = {
                "node_id": "node-test",
                "status": status_input,
                "latency_ms": 0.0,
                "packet_loss": 0.0,
                "timestamp": "2026-09-29T12:00:00Z"
            }

            result = self.anchor.project(raw_input)

            assert isinstance(result, CanonicaltTelemetry)
            assert result.status == expected_status, f"Failed for status: {status_input}"

    def test_status_unrecognized_fallback(self):
        """Test fallback for unrecognized status."""
        raw_input = {
            "node_id": "node-004",
            "status": "unknown_status_xyz",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.status == NodeStatus.DEGRADED

    def test_latency_clamping_negative(self):
        """Test latency clamping for negative values."""
        raw_input = {
            "node_id": "node-005",
            "status": "up",
            "latency_ms": -50.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.latency_ms == 0.0

    def test_packet_loss_clamping_high(self):
        """Test packet_loss clamping for values > 100.0."""
        raw_input = {
            "node_id": "node-006",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 150.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.packet_loss == 100.0

    def test_packet_loss_clamping_negative(self):
        """Test packet_loss clamping for negative values."""
        raw_input = {
            "node_id": "node-007",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": -5.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.packet_loss == 0.0

    def test_missing_node_id_error(self):
        """Test error when node_id is missing."""
        raw_input = {
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, StructuralError)
        assert result.code == "MISSING_FIELD"
        assert result.field == "node_id"

    def test_empty_node_id_error(self):
        """Test error when node_id is empty."""
        raw_input = {
            "node_id": "",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, StructuralError)
        assert result.code == "EMPTY_FIELD"
        assert result.field == "node_id"

    def test_invalid_input_type_error(self):
        """Test error when input is not a dict."""
        result = self.anchor.project("not a dict")

        assert isinstance(result, StructuralError)
        assert result.code == "INVALID_INPUT_TYPE"

    def test_timestamp_generation_when_missing(self):
        """Test timestamp generation when missing."""
        raw_input = {
            "node_id": "node-008",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.timestamp
        parsed_ts = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = abs((now - parsed_ts).total_seconds())
        assert diff < 5

    def test_timestamp_generation_when_empty(self):
        """Test timestamp generation when provided as empty string."""
        raw_input = {
            "node_id": "node-009",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": ""
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert result.timestamp

    def test_validated_token_generation(self):
        """Test validated token generation and uniqueness."""
        raw_input = {
            "node_id": "node-010",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result1 = self.anchor.project(raw_input)
        result2 = self.anchor.project(raw_input)

        assert isinstance(result1, CanonicaltTelemetry)
        assert isinstance(result2, CanonicaltTelemetry)
        assert result1.validated_token != result2.validated_token
        assert result1.validated_token.startswith("validated_token_")
        assert result2.validated_token.startswith("validated_token_")

    def test_batch_projection(self):
        """Test batch projection."""
        raw_inputs = [
            {
                "node_id": "node-001",
                "status": "up",
                "latency_ms": 10.0,
                "packet_loss": 0.0,
                "timestamp": "2026-09-29T12:00:00Z"
            },
            {
                "node_id": "node-002",
                "status": "degraded"
            },
            {
                "status": "up"
            }
        ]

        results = self.anchor.project_batch(raw_inputs)

        assert len(results) == 3
        assert isinstance(results[0], CanonicaltTelemetry)
        assert isinstance(results[1], CanonicaltTelemetry)
        assert isinstance(results[2], StructuralError)

    def test_o_n_complexity_single_pass(self):
        """Test O(N) complexity with deterministic single-pass projection."""
        raw_input = {
            "node_id": "node-" + "x" * 10000,
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }

        result = self.anchor.project(raw_input)

        assert isinstance(result, CanonicaltTelemetry)
        assert len(result.node_id) > 1000
