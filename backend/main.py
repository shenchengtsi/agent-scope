"""AgentScope Backend API."""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# In-memory storage for traces (replace with DB in production)
traces: Dict[str, dict] = {}
connected_websockets: List[WebSocket] = []


class ToolCallData(BaseModel):
    id: str
    name: str
    arguments: dict
    result: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0.0


class ExecutionStepData(BaseModel):
    id: str
    type: str
    content: str
    timestamp: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    tool_call: Optional[ToolCallData] = None
    metadata: dict = {}
    status: str = "pending"


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 AgentScope backend starting...")
    yield
    print("👋 AgentScope backend shutting down...")


app = FastAPI(
    title="AgentScope",
    description="Agent debugging and observability platform",
    version="0.1.0",
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


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/traces")
async def get_traces():
    """Get all traces."""
    # Sort by start_time descending
    sorted_traces = sorted(
        traces.values(),
        key=lambda x: x.get("start_time", ""),
        reverse=True
    )
    return {"traces": sorted_traces}


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific trace."""
    if trace_id not in traces:
        return {"error": "Trace not found"}, 404
    return traces[trace_id]


@app.post("/api/traces")
async def create_trace(trace: TraceData):
    """Create or update a trace."""
    trace_dict = trace.model_dump()
    traces[trace.id] = trace_dict
    
    # Broadcast to WebSocket clients
    await broadcast_trace(trace_dict)
    
    return {"status": "ok", "id": trace.id}


@app.delete("/api/traces/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a trace."""
    if trace_id in traces:
        del traces[trace_id]
    return {"status": "ok"}


@app.delete("/api/traces")
async def clear_traces():
    """Clear all traces."""
    traces.clear()
    await broadcast_trace({"type": "clear_all"})
    return {"status": "ok"}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        # Send initial data
        sorted_traces = sorted(
            traces.values(),
            key=lambda x: x.get("start_time", ""),
            reverse=True
        )
        await websocket.send_json({
            "type": "initial",
            "data": sorted_traces
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


# Static files (frontend) - only if build exists
frontend_build_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)