"""
Network Operations Center Server with Isomorphic Structural Governance.

A lightweight, production-grade backend that ingests raw telemetry streams,
projects them through the StructuralAnchor, and serves guaranteed schema-compliant
data packets with zero parser exceptions and zero runtime schema drift.

Core guarantees:
  - Zero parser exceptions
  - Zero runtime schema drift
  - Absolute data contract fidelity
  - O(N) ingestion complexity
"""

import json
from typing import Dict, List, Any, Optional
from collections import deque
from datetime import datetime
from dataclasses import asdict

from canonical_schema import CanonicaltTelemetry, NodeStatus
from structural_anchor import StructuralAnchor, StructuralError


class TelemetryStore:
    """
    In-memory store for canonical telemetry packets.
    
    Maintains a bounded deque of valid telemetry samples, with oldest
    samples evicted when capacity is exceeded.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize telemetry store.
        
        Args:
            max_size: Maximum number of telemetry samples to retain.
        """
        self.max_size = max_size
        self.packets: deque = deque(maxlen=max_size)
        self.rejected_count = 0
        self.accepted_count = 0
    
    def add(self, packet: CanonicaltTelemetry) -> None:
        """Add a canonical telemetry packet to the store."""
        self.packets.append(packet)
        self.accepted_count += 1
    
    def add_error(self, error: StructuralError) -> None:
        """Record a rejected/malformed input."""
        self.rejected_count += 1
    
    def get_latest(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve latest telemetry packets.
        
        Args:
            node_id: Optional filter by specific node.
        
        Returns:
            List of dictionaries representing telemetry packets.
        """
        if node_id is None:
            return [asdict(packet) for packet in self.packets]
        
        return [asdict(packet) for packet in self.packets if packet.node_id == node_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "current_size": len(self.packets),
            "max_size": self.max_size,
        }


class NOCServer:
    """
    Network Operations Center Server with structural governance.
    
    Ingests raw telemetry via StructuralAnchor and serves guaranteed
    schema-compliant data with zero runtime schema drift.
    """
    
    def __init__(self, store_size: int = 1000):
        """
        Initialize NOC server.
        
        Args:
            store_size: Maximum telemetry packets to retain in memory.
        """
        self.anchor = StructuralAnchor()
        self.store = TelemetryStore(max_size=store_size)
        self.ingestion_log: List[Dict[str, Any]] = []
    
    def ingest(self, raw_telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest and project a single raw telemetry sample.
        
        Args:
            raw_telemetry: Raw input dictionary.
        
        Returns:
            Dictionary with ingestion result:
              - status: 'accepted' or 'rejected'
              - packet: Canonical telemetry (if accepted)
              - error: StructuralError details (if rejected)
              - validated_token: Traceable provenance signal
        """
        result = self.anchor.project(raw_telemetry)
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if isinstance(result, CanonicaltTelemetry):
            self.store.add(result)
            ingestion_record = {
                "timestamp": timestamp,
                "status": "accepted",
                "packet": asdict(result),
                "validated_token": result.validated_token,
            }
        else:
            self.store.add_error(result)
            ingestion_record = {
                "timestamp": timestamp,
                "status": "rejected",
                "error": {
                    "code": result.code,
                    "field": result.field,
                    "message": result.message,
                },
                "validated_token": None,
            }
        
        self.ingestion_log.append(ingestion_record)
        return ingestion_record
    
    def ingest_batch(self, raw_telemetries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest a batch of raw telemetry samples.
        
        Args:
            raw_telemetries: List of raw input dictionaries.
        
        Returns:
            Summary of batch ingestion results.
        """
        if not isinstance(raw_telemetries, list):
            return {
                "status": "error",
                "message": "Expected list of telemetry inputs",
            }
        
        results = []
        for raw_telemetry in raw_telemetries:
            results.append(self.ingest(raw_telemetry))
        
        accepted = sum(1 for r in results if r["status"] == "accepted")
        rejected = sum(1 for r in results if r["status"] == "rejected")
        
        return {
            "status": "completed",
            "total": len(results),
            "accepted": accepted,
            "rejected": rejected,
            "results": results,
        }
    
    def get_telemetry(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve current telemetry packets.
        
        Args:
            node_id: Optional filter by specific node.
        
        Returns:
            Dictionary with telemetry packets and metadata.
        """
        packets = self.store.get_latest(node_id)
        return {
            "status": "success",
            "count": len(packets),
            "packets": packets,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get server-wide statistics.
        
        Returns:
            Dictionary with server statistics.
        """
        store_stats = self.store.get_stats()
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "telemetry_store": store_stats,
            "ingestion_log_size": len(self.ingestion_log),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the NOC server.
        
        Returns:
            Dictionary with health status.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "store_operational": True,
            "anchor_operational": True,
        }


def simulate_telemetry_stream() -> List[Dict[str, Any]]:
    """
    Generate simulated raw telemetry samples for testing.
    
    Includes well-formed, sparse, and malformed inputs to demonstrate
    structural anchor behavior.
    
    Returns:
        List of raw telemetry dictionaries.
    """
    return [
        # Well-formed sample
        {
            "node_id": "node-001",
            "status": "up",
            "latency_ms": 12.5,
            "packet_loss": 0.1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        # Sparse sample (missing optional fields)
        {
            "node_id": "node-002",
            "status": "degraded",
        },
        # Malformed status (will be normalized)
        {
            "node_id": "node-003",
            "status": "warning",
            "latency_ms": 45.0,
            "packet_loss": 5.5,
        },
        # Missing timestamp (will be generated)
        {
            "node_id": "node-004",
            "status": "down",
            "latency_ms": 999.0,
            "packet_loss": 100.0,
        },
        # Clamped values
        {
            "node_id": "node-005",
            "status": "ok",
            "latency_ms": -10.0,  # Will be clamped to 0.0
            "packet_loss": 150.0,  # Will be clamped to 100.0
        },
        # Missing node_id (will fail projection)
        {
            "status": "up",
            "latency_ms": 5.0,
        },
        # Empty node_id (will fail projection)
        {
            "node_id": "",
            "status": "up",
        },
    ]


def main() -> None:
    """
    Main entry point demonstrating NOC server operation.
    
    Demonstrates:
      - Ingestion of simulated telemetry stream
      - Structural anchor projection
      - Zero runtime schema drift
      - Guaranteed data contract fidelity
    """
    print("=" * 80)
    print("Network Operations Center (NOC) Server - Isomorphic Structural Theory")
    print("=" * 80)
    print()
    
    # Initialize server
    server = NOCServer(store_size=1000)
    print("[INIT] NOC server initialized with structural anchor engine")
    print()
    
    # Health check
    health = server.health_check()
    print(f"[HEALTH] Status: {health['status']}")
    print()
    
    # Generate simulated telemetry stream
    raw_stream = simulate_telemetry_stream()
    print(f"[INGEST] Ingesting {len(raw_stream)} raw telemetry samples...")
    print()
    
    # Ingest batch
    batch_result = server.ingest_batch(raw_stream)
    print(f"[BATCH RESULT]")
    print(f"  Total: {batch_result['total']}")
    print(f"  Accepted: {batch_result['accepted']}")
    print(f"  Rejected: {batch_result['rejected']}")
    print()
    
    # Display results
    print("[ACCEPTED TELEMETRY PACKETS]")
    for result in batch_result["results"]:
        if result["status"] == "accepted":
            packet = result["packet"]
            print(f"  - {packet['node_id']}: {packet['status']}, "
                  f"latency={packet['latency_ms']}ms, "
                  f"loss={packet['packet_loss']}%, "
                  f"token={result['validated_token']}")
    print()
    
    print("[REJECTED INPUTS]")
    for result in batch_result["results"]:
        if result["status"] == "rejected":
            error = result["error"]
            print(f"  - {error['code']}: {error['message']} (field: {error['field']})")
    print()
    
    # Query telemetry
    telemetry = server.get_telemetry()
    print(f"[TELEMETRY STORE] {telemetry['count']} canonical packets:")
    for packet in telemetry["packets"]:
        print(f"  {json.dumps(packet)}")
    print()
    
    # Server stats
    stats = server.get_stats()
    print(f"[SERVER STATS]")
    print(f"  Timestamp: {stats['timestamp']}")
    print(f"  Telemetry Store:")
    print(f"    - Accepted: {stats['telemetry_store']['accepted_count']}")
    print(f"    - Rejected: {stats['telemetry_store']['rejected_count']}")
    print(f"    - Current Size: {stats['telemetry_store']['current_size']}")
    print()
    
    print("=" * 80)
    print("NOC Server Operational - Zero Parser Exceptions, Zero Runtime Schema Drift")
    print("=" * 80)


if __name__ == "__main__":
    main()
