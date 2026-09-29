````markdown
# netpulse-noc: Network Operations Center Monitor

A production-grade Network Operations Center (NOC) backend implementing **Isomorphic Structural Theory (IST)** for deterministic, schema-first network telemetry governance.

## Core Philosophy

**Structure is an upstream mathematical invariant, not a runtime guess.**

This project rejects traditional runtime JSON parsing, retry loops, and reactive error-handling in favor of an **upstream, ex-ante structural governance model**:

- ✅ **Canonical Schema First**: All data must conform to an immutable schema before application logic executes
- ✅ **Deterministic Projection**: Raw inputs are structurally anchored to canonical shape with O(N) complexity
- ✅ **Zero Runtime Drift**: Type system + frozen dataclasses prevent mutation
- ✅ **Traceable Fallbacks**: Malformed data receives explicit `validated_token` signals, not exceptions
- ✅ **Guaranteed Fidelity**: Absolute data contract compliance at ingestion time

---

## Architecture

### `canonical_schema.py`

Defines the immutable, non-negotiable source of truth for all network telemetry data.

**Key Components:**

```python
class NodeStatus(str, Enum):
    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"

@dataclass(frozen=True)
class CanonicaltTelemetry:
    node_id: str              # Unique node identifier
    status: NodeStatus        # Constrained enum status
    latency_ms: float         # Non-negative latency
    packet_loss: float        # 0.0-100.0 percentage
    timestamp: str            # ISO 8601 timestamp
    validated_token: Optional[str]  # Provenance signal
```

**Guarantees:**
- Frozen immutability prevents accidental mutation
- Type system enforces schema before instantiation
- `__post_init__` validation fails fast on constraint violations
- No invalid instances can exist in memory

---

### `structural_anchor.py`

Deterministic upstream projection engine that transforms raw, sparse, or drifting telemetry inputs onto the canonical schema shape.

**Key Components:**

```python
class StructuralAnchor:
    def project(self, raw_input: Dict[str, Any]) -> Union[CanonicaltTelemetry, StructuralError]:
        """Project raw input onto canonical schema (O(N) complexity)"""
        # Single-pass traversal, no exceptions thrown
        # All anomalies structurally resolved with fallback signals
```

**Behavior:**

| Scenario | Handling |
|----------|----------|
| Well-formed input | ✅ Direct projection to canonical schema |
| Missing optional field | ⚡ Deterministic fallback (e.g., `latency_ms=0.0`) |
| Malformed status string | 🔄 Normalization via STATUS_MAP (e.g., "warning" → `DEGRADED`) |
| Out-of-range numeric | 📎 Clamping (e.g., packet_loss=-5 → 0.0, packet_loss=150 → 100.0) |
| Missing timestamp | ⏰ Generate current ISO 8601 timestamp |
| Critical field missing | ❌ Return `StructuralError` with traceable code |

**Traceable Signals:**

All successfully projected inputs receive a `validated_token_{index}` signal for data provenance tracking:

```python
def _generate_validated_token(self) -> str:
    return f"validated_token_{self._projection_counter}"
```

---

### `noc_server.py`

Lightweight backend server that ingests raw telemetry streams, projects through StructuralAnchor, and serves guaranteed schema-compliant packets.

**Key Components:**

```python
class TelemetryStore:
    """Bounded in-memory store with O(1) append, tracks stats"""
    
class NOCServer:
    def ingest(self, raw_telemetry: Dict) -> Dict
    def ingest_batch(self, raw_telemetries: List) -> Dict
    def get_telemetry(self, node_id: Optional[str]) -> Dict
    def get_stats(self) -> Dict
    def health_check(self) -> Dict
```

**Guarantees:**
- Zero parser exceptions (all handled structurally)
- Zero runtime schema drift (canonical schema enforced at ingestion)
- Absolute data contract fidelity (every packet is type-validated)
- Traceable provenance (every accepted packet carries validated_token)

---

## Quick Start

### Installation

```bash
git clone https://github.com/Rome2112/netpulse-noc.git
cd netpulse-noc
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Run Simulation

```bash
python noc_server.py
```

**Output Example:**

```
================================================================================
Network Operations Center (NOC) Server - Isomorphic Structural Theory
================================================================================

[INIT] NOC server initialized with structural anchor engine

[HEALTH] Status: healthy

[INGEST] Ingesting 7 raw telemetry samples...

[BATCH RESULT]
  Total: 7
  Accepted: 5
  Rejected: 2

[ACCEPTED TELEMETRY PACKETS]
  - node-001: UP, latency=12.5ms, loss=0.1%, token=validated_token_1
  - node-002: DEGRADED, latency=0.0ms, loss=0.0%, token=validated_token_2
  - node-003: DEGRADED, latency=45.0ms, loss=5.5%, token=validated_token_3
  - node-004: DOWN, latency=999.0ms, loss=100.0%, token=validated_token_4
  - node-005: UP, latency=0.0ms, loss=100.0%, token=validated_token_5

[REJECTED INPUTS]
  - MISSING_FIELD: node_id is required but not present (field: node_id)
  - EMPTY_FIELD: node_id cannot be empty (field: node_id)

[TELEMETRY STORE] 5 canonical packets:
  {"node_id": "node-001", "status": "UP", "latency_ms": 12.5, "packet_loss": 0.1, "timestamp": "...", "validated_token": "validated_token_1"}
  ...

[SERVER STATS]
  Timestamp: 2026-09-29T...Z
  Telemetry Store:
    - Accepted: 5
    - Rejected: 2
    - Current Size: 5

================================================================================
NOC Server Operational - Zero Parser Exceptions, Zero Runtime Schema Drift
================================================================================
```

---

## Design Principles

### 1. **Upstream Governance**
Structure is established before runtime, not discovered through error-handling loops.

### 2. **Immutability as Law**
Frozen dataclasses prevent accidental mutation; the schema is untouchable once instantiated.

### 3. **Determinism Over Reactivity**
All inputs follow deterministic projection rules, eliminating nondeterministic error paths.

### 4. **Fallback Signals, Not Exceptions**
Malformed data receives traceable `validated_token` signals rather than throwing exceptions or silently dropping packets.

### 5. **O(N) Complexity Guarantee**
Single-pass projection with no repeated validation or traversal.

### 6. **Type-Driven Validation**
The Python type system + dataclass validation serve as compile-time + instantiation-time contracts.

---

## Testing the Structural Anchor

```python
from structural_anchor import StructuralAnchor
from canonical_schema import CanonicaltTelemetry, StructuralError

anchor = StructuralAnchor()

# Well-formed input
result1 = anchor.project({
    "node_id": "node-001",
    "status": "up",
    "latency_ms": 10.5,
    "packet_loss": 0.5,
    "timestamp": "2026-09-29T12:00:00Z"
})
assert isinstance(result1, CanonicaltTelemetry)
assert result1.status.value == "UP"

# Sparse input (missing latency, packet_loss)
result2 = anchor.project({
    "node_id": "node-002",
    "status": "degraded"
})
assert isinstance(result2, CanonicaltTelemetry)
assert result2.latency_ms == 0.0  # Fallback
assert result2.packet_loss == 0.0  # Fallback

# Malformed input (missing node_id)
result3 = anchor.project({
    "status": "up"
})
assert isinstance(result3, StructuralError)
assert result3.code == "MISSING_FIELD"
assert result3.field == "node_id"
```

---

## Production Deployment

For production deployment, extend with:

1. **FastAPI Server**: `api_server.py` for `/ingest` and `/telemetry` endpoints
2. **Persistence Layer**: Replace in-memory `TelemetryStore` with persistent DB
3. **Metrics & Monitoring**: Prometheus metrics for ingestion rates, projection success/failure
4. **Distributed Tracing**: `validated_token` integration with OpenTelemetry
5. **Scaling**: Horizontal scaling via message queue (e.g., Kafka) and multiple anchor instances

---

## License

MIT

---

## Contributing

This project prioritizes structural clarity and IST principles. All contributions should:
- Maintain immutability guarantees
- Preserve O(N) complexity bounds
- Never introduce runtime exception throwing in projection paths
- Include traceable provenance signals for all data flows

````
