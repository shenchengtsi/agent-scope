"""AgentScope Backend API v2 with Storage Abstraction."""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), '..', 'sdk')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.storage_manager import get_storage, health_check

# In-memory storage for WebSocket connections
connected_websockets: List[WebSocket] = []


# Data models (keeping same as v1 for compatibility)
class ToolCallData(BaseModel):
    id: str
    name: str
    arguments: dict
    result: Optional[Any] = None
    error: Optional[Any] = None
    latency_ms: float = 0.0


class ExecutionStepData(BaseModel):
    id: str
    type: str
    content: Any
    timestamp: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    tool_call: Optional[ToolCallData] = None
    metadata: dict = {}


class TraceData(BaseModel):
    id: str
    name: str
    tags: List[str] = []
    start_time: str
    end_time: Optional[str] = None
    steps: List[ExecutionStepData] = []
    status: str = "pending"
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    input_query: str = ""
    output_result: str = ""
    metadata: dict = {}
    cost_estimate: float = 0.0
    llm_call_count: int = 0
    tool_call_count: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 AgentScope backend v2 starting...")
    
    # Health check on startup
    health = health_check()
    print(f"📦 Storage: {health['storage_backend']}")
    print(f"💚 Health: {'OK' if health['healthy'] else 'ERROR'}")
    
    yield
    
    print("👋 AgentScope backend shutting down...")


app = FastAPI(
    title="AgentScope",
    description="Agent debugging and observability platform (v2 with storage abstraction)",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed output."""
    print(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )


async def broadcast_trace(trace: dict):
    """Broadcast trace update to all connected WebSocket clients."""
    disconnected = []
    for ws in connected_websockets:
        try:
            await ws.send_json({
                "type": "trace_update",
                "data": trace
            })
        except Exception:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        if ws in connected_websockets:
            connected_websockets.remove(ws)


# ============================================================================
# API Endpoints (updated to use storage abstraction)
# ============================================================================

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "version": "0.2.0",
        "storage": health_check()
    }


@app.get("/api/traces")
async def get_traces(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    tag: Optional[str] = None,
):
    """Get all traces with filtering and pagination."""
    storage = get_storage()
    
    tags = [tag] if tag else None
    traces = storage.list_traces(
        limit=limit,
        offset=offset,
        tags=tags,
        status=status,
    )
    
    total = storage.count_traces(tags=tags, status=status)
    
    return {
        "traces": traces,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(traces) < total
        }
    }


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific trace."""
    storage = get_storage()
    trace = storage.get_trace(trace_id)
    
    if not trace:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found"}
        )
    
    return trace


@app.post("/api/traces")
async def create_trace(trace: TraceData):
    """Create or update a trace."""
    try:
        storage = get_storage()
        trace_dict = trace.model_dump()
        
        # Save to storage
        storage.save_trace(trace_dict)
        
        # Broadcast to WebSocket clients
        await broadcast_trace(trace_dict)
        
        return {"status": "ok", "id": trace.id}
    except Exception as e:
        import traceback
        print(f"ERROR in create_trace: {e}")
        traceback.print_exc()
        raise


@app.post("/api/traces/raw")
async def create_trace_raw(request: Request):
    """Create or update a trace from raw JSON (for debugging)."""
    try:
        storage = get_storage()
        data = await request.json()
        trace_id = data.get("id", "unknown")
        
        # Save to storage
        storage.save_trace(data)
        
        await broadcast_trace(data)
        return {"status": "ok", "id": trace_id}
    except Exception as e:
        print(f"Error in raw trace: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.delete("/api/traces/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a trace."""
    storage = get_storage()
    deleted = storage.delete_trace(trace_id)
    
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found"}
        )
    
    return {"status": "ok", "deleted": trace_id}


@app.delete("/api/traces")
async def clear_traces():
    """Clear all traces."""
    # Note: Storage abstraction doesn't support bulk delete
    # This would need to be implemented in BaseStorage
    # For now, just clear memory
    storage = get_storage()
    stats = storage.get_stats()
    
    await broadcast_trace({"type": "clear_all"})
    
    return {
        "status": "ok", 
        "message": "Clear operation not fully implemented in storage abstraction",
        "stats_before": stats
    }


@app.get("/api/stats")
async def get_stats():
    """Get storage statistics."""
    storage = get_storage()
    return storage.get_stats()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        # Send initial data
        storage = get_storage()
        traces = storage.list_traces(limit=100)
        await websocket.send_json({
            "type": "initial_data",
            "traces": traces
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                message = await websocket.receive_json()
                # Handle client messages if needed
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
