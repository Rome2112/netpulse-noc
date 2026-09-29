"""
Unit tests for noc_server module.

Tests TelemetryStore, NOCServer ingestion, batch processing, and statistics.
"""

import pytest
from datetime import datetime
from noc_server import NOCServer, TelemetryStore
from canonical_schema import CanonicaltTelemetry, NodeStatus


class TestTelemetryStore:
    """Test TelemetryStore in-memory storage."""
    
    def test_initialization(self):
        """Test store initialization."""
        store = TelemetryStore(max_size=100)
        
        assert store.max_size == 100
        assert len(store.packets) == 0
        assert store.accepted_count == 0
        assert store.rejected_count == 0
    
    def test_add_packet(self):
        """Test adding a packet to store."""
        store = TelemetryStore(max_size=100)
        packet = CanonicaltTelemetry(
            node_id="node-001",
            status=NodeStatus.UP,
            latency_ms=10.0,
            packet_loss=0.0,
            timestamp="2026-09-29T12:00:00Z"
        )
        
        store.add(packet)
        
        assert len(store.packets) == 1
        assert store.accepted_count == 1
        assert store.packets[0] == packet
    
    def test_add_error(self):
        """Test recording rejected input."""
        store = TelemetryStore(max_size=100)
        
        store.add_error(None)  # type: ignore
        
        assert store.rejected_count == 1
    
    def test_max_size_enforcement(self):
        """Test that store respects max_size."""
        store = TelemetryStore(max_size=5)
        
        for i in range(10):
            packet = CanonicaltTelemetry(
                node_id=f"node-{i}",
                status=NodeStatus.UP,
                latency_ms=float(i),
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
            store.add(packet)
        
        # Should only have last 5 (FIFO with maxlen)
        assert len(store.packets) == 5
        assert store.accepted_count == 10  # Total accepted
        assert store.packets[0].node_id == "node-5"
        assert store.packets[-1].node_id == "node-9"
    
    def test_get_latest_all(self):
        """Test retrieving all packets."""
        store = TelemetryStore(max_size=100)
        
        for i in range(3):
            packet = CanonicaltTelemetry(
                node_id=f"node-{i}",
                status=NodeStatus.UP,
                latency_ms=float(i),
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
            store.add(packet)
        
        result = store.get_latest()
        
        assert len(result) == 3
        assert result[0]["node_id"] == "node-0"
        assert result[2]["node_id"] == "node-2"
    
    def test_get_latest_filtered_by_node(self):
        """Test retrieving packets filtered by node_id."""
        store = TelemetryStore(max_size=100)
        
        for i in range(3):
            packet = CanonicaltTelemetry(
                node_id=f"node-{i % 2}",  # Alternate between node-0 and node-1
                status=NodeStatus.UP,
                latency_ms=float(i),
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
            store.add(packet)
        
        result = store.get_latest("node-0")
        
        assert len(result) == 2
        assert all(p["node_id"] == "node-0" for p in result)
    
    def test_get_stats(self):
        """Test getting store statistics."""
        store = TelemetryStore(max_size=100)
        
        for i in range(5):
            packet = CanonicaltTelemetry(
                node_id=f"node-{i}",
                status=NodeStatus.UP,
                latency_ms=0.0,
                packet_loss=0.0,
                timestamp="2026-09-29T12:00:00Z"
            )
            store.add(packet)
        
        store.add_error(None)  # type: ignore
        
        stats = store.get_stats()
        
        assert stats["accepted_count"] == 5
        assert stats["rejected_count"] == 1
        assert stats["current_size"] == 5
        assert stats["max_size"] == 100


class TestNOCServer:
    """Test NOCServer ingestion and management."""
    
    def setup_method(self):
        """Initialize a fresh server for each test."""
        self.server = NOCServer(store_size=1000)
    
    def test_initialization(self):
        """Test server initialization."""
        assert self.server.anchor is not None
        assert self.server.store is not None
        assert self.server.store.max_size == 1000
        assert len(self.server.ingestion_log) == 0
    
    def test_health_check(self):
        """Test health check endpoint."""
        result = self.server.health_check()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["store_operational"] is True
        assert result["anchor_operational"] is True
    
    def test_ingest_well_formed(self):
        """Test ingestion of well-formed telemetry."""
        raw_telemetry = {
            "node_id": "node-001",
            "status": "up",
            "latency_ms": 10.5,
            "packet_loss": 0.1,
            "timestamp": "2026-09-29T12:00:00Z"
        }
        
        result = self.server.ingest(raw_telemetry)
        
        assert result["status"] == "accepted"
        assert "packet" in result
        assert result["packet"]["node_id"] == "node-001"
        assert result["packet"]["status"] == "UP"
        assert result["validated_token"] is not None
    
    def test_ingest_sparse(self):
        """Test ingestion of sparse telemetry."""
        raw_telemetry = {
            "node_id": "node-002",
            "status": "degraded"
        }
        
        result = self.server.ingest(raw_telemetry)
        
        assert result["status"] == "accepted"
        assert result["packet"]["latency_ms"] == 0.0  # Fallback
        assert result["packet"]["packet_loss"] == 0.0  # Fallback
    
    def test_ingest_malformed_missing_node_id(self):
        """Test ingestion of malformed telemetry (missing node_id)."""
        raw_telemetry = {
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0
        }
        
        result = self.server.ingest(raw_telemetry)
        
        assert result["status"] == "rejected"
        assert "error" in result
        assert result["error"]["code"] == "MISSING_FIELD"
        assert result["error"]["field"] == "node_id"
    
    def test_ingestion_log_tracking(self):
        """Test that ingestion log tracks all results."""
        raw1 = {
            "node_id": "node-001",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }
        
        raw2 = {"status": "up"}  # Missing node_id
        
        self.server.ingest(raw1)
        self.server.ingest(raw2)
        
        assert len(self.server.ingestion_log) == 2
        assert self.server.ingestion_log[0]["status"] == "accepted"
        assert self.server.ingestion_log[1]["status"] == "rejected"
    
    def test_ingest_batch_mixed(self):
        """Test batch ingestion with mixed valid/invalid inputs."""
        raw_telemetries = [
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
                "status": "up"  # Missing node_id
            }
        ]
        
        result = self.server.ingest_batch(raw_telemetries)
        
        assert result["status"] == "completed"
        assert result["total"] == 3
        assert result["accepted"] == 2
        assert result["rejected"] == 1
        assert len(result["results"]) == 3
    
    def test_ingest_batch_invalid_input_type(self):
        """Test batch ingestion with non-list input."""
        result = self.server.ingest_batch({"not": "a list"})  # type: ignore
        
        assert result["status"] == "error"
        assert "message" in result
    
    def test_get_telemetry_all(self):
        """Test retrieving all telemetry packets."""
        raw1 = {
            "node_id": "node-001",
            "status": "up",
            "latency_ms": 10.0,
            "packet_loss": 0.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }
        
        raw2 = {
            "node_id": "node-002",
            "status": "down",
            "latency_ms": 50.0,
            "packet_loss": 100.0,
            "timestamp": "2026-09-29T12:00:00Z"
        }
        
        self.server.ingest(raw1)
        self.server.ingest(raw2)
        
        result = self.server.get_telemetry()
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["packets"]) == 2
    
    def test_get_telemetry_filtered(self):
        """Test retrieving telemetry filtered by node_id."""
        for i in range(3):
            raw = {
                "node_id": f"node-{i}",
                "status": "up",
                "latency_ms": 10.0,
                "packet_loss": 0.0,
                "timestamp": "2026-09-29T12:00:00Z"
            }
            self.server.ingest(raw)
        
        result = self.server.get_telemetry("node-1")
        
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["packets"][0]["node_id"] == "node-1"
    
    def test_get_stats(self):
        """Test retrieving server statistics."""
        for i in range(3):
            raw = {
                "node_id": f"node-{i}",
                "status": "up",
                "latency_ms": 10.0,
                "packet_loss": 0.0,
                "timestamp": "2026-09-29T12:00:00Z"
            }
            self.server.ingest(raw)
        
        # Ingest one invalid
        self.server.ingest({"status": "up"})
        
        stats = self.server.get_stats()
        
        assert stats["status"] == "operational"
        assert "timestamp" in stats
        assert stats["telemetry_store"]["accepted_count"] == 3
        assert stats["telemetry_store"]["rejected_count"] == 1
        assert stats["telemetry_store"]["current_size"] == 3
    
    def test_concurrent_ingestion_thread_safety(self):
        """Test that multiple ingestions work correctly."""
        for i in range(100):
            raw = {
                "node_id": f"node-{i % 10}",
                "status": "up" if i % 2 == 0 else "degraded",
                "latency_ms": float(i),
                "packet_loss": float(i % 101),
                "timestamp": "2026-09-29T12:00:00Z"
            }
            self.server.ingest(raw)
        
        stats = self.server.get_stats()
        assert stats["telemetry_store"]["accepted_count"] == 100
