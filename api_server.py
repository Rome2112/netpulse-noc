"""
FastAPI server for Network Operations Center with HTTP endpoints.

Provides REST API for telemetry ingestion, retrieval, and server statistics
with full schema validation and structural governance.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from config import config
from noc_server import NOCServer

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Network Operations Center (NOC)",
    description="Production telemetry ingestion with Isomorphic Structural Theory",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NOC server
noc_server = NOCServer(store_size=config.TELEMETRY_STORE_MAX_SIZE)

logger.info("NOC API Server initialized with structural anchor engine")


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"NOC Server starting on {config.HOST}:{config.PORT}")
    logger.info(f"Telemetry store capacity: {config.TELEMETRY_STORE_MAX_SIZE}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("NOC Server shutting down")


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status with timestamp.
    """
    return noc_server.health_check()


@app.get("/stats", tags=["metrics"])
async def get_stats() -> Dict[str, Any]:
    """
    Get server statistics.
    
    Returns:
        Server metrics including ingestion counts and store state.
    """
    return noc_server.get_stats()


@app.post("/ingest", tags=["ingestion"])
async def ingest_telemetry(request: Request) -> Dict[str, Any]:
    """
    Ingest a single raw telemetry sample.
    
    The raw input is projected through the StructuralAnchor onto the canonical
    schema with deterministic fallback handling.
    
    Args:
        request: HTTP request body (raw telemetry dict).
    
    Returns:
        Ingestion result with status, canonical packet (if accepted), or error details.
    
    Raises:
        HTTPException: If request body is invalid JSON.
    """
    try:
        raw_telemetry = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON in /ingest: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
    
    if not isinstance(raw_telemetry, dict):
        raise HTTPException(
            status_code=400,
            detail="Request body must be a JSON object"
        )
    
    result = noc_server.ingest(raw_telemetry)
    return result


@app.post("/ingest/batch", tags=["ingestion"])
async def ingest_batch(request: Request) -> Dict[str, Any]:
    """
    Ingest a batch of raw telemetry samples.
    
    Each input is independently projected through the StructuralAnchor.
    
    Args:
        request: HTTP request body (list of raw telemetry dicts).
    
    Returns:
        Batch ingestion summary with per-item results.
    
    Raises:
        HTTPException: If request body is invalid JSON or not a list.
    """
    try:
        raw_telemetries = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON in /ingest/batch: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
    
    if not isinstance(raw_telemetries, list):
        raise HTTPException(
            status_code=400,
            detail="Request body must be a JSON array"
        )
    
    result = noc_server.ingest_batch(raw_telemetries)
    return result


@app.get("/telemetry", tags=["queries"])
async def get_telemetry(node_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve current telemetry packets.
    
    Args:
        node_id: Optional filter by specific node ID.
    
    Returns:
        Dictionary with telemetry packets and metadata.
    """
    return noc_server.get_telemetry(node_id)


@app.get("/telemetry/{node_id}", tags=["queries"])
async def get_node_telemetry(node_id: str) -> Dict[str, Any]:
    """
    Retrieve telemetry for a specific node.
    
    Args:
        node_id: Node identifier.
    
    Returns:
        Dictionary with telemetry packets for the node.
    """
    return noc_server.get_telemetry(node_id)


@app.get("/info", tags=["metadata"])
async def get_info() -> Dict[str, Any]:
    """
    Get server information.
    
    Returns:
        Server metadata including version and architecture details.
    """
    return {
        "status": "operational",
        "service": "Network Operations Center (NOC)",
        "version": "0.1.0",
        "architecture": "Isomorphic Structural Theory (IST)",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "philosophy": "Structure is an upstream mathematical invariant, not a runtime guess",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
    )
