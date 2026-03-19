"""AgentScope Backend API."""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

# In-memory storage for traces (replace with DB in production)
traces: Dict[str, dict] = {}
connected_websockets: List[WebSocket] = []


class ToolCallData(BaseModel):
    id: str
    name: str
    arguments: dict
    result: Optional[Any] = None
    error: Optional[Any] = None
    latency_ms: float = 0.0


# Enhanced monitoring data models
class SkillInfoData(BaseModel):
    name: str
    description: str = ""
    status: str = "loaded"
    error: Optional[str] = None
    load_time_ms: float = 0.0


class PromptMessageData(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


class PromptBuildInfoData(BaseModel):
    messages: List[PromptMessageData] = []
    system_prompt: str = ""
    context_window: int = 0
    max_tokens: int = 0
    temperature: float = 0.0
    top_p: float = 0.0
    model: str = ""


class ToolSelectionInfoData(BaseModel):
    selected_tool: str
    available_tools: List[Dict] = []
    selection_reason: str = ""
    confidence: float = 0.0
    tool_call_id: str = ""


class MemoryOperationInfoData(BaseModel):
    operation: str = ""
    key: str = ""
    namespace: str = "default"
    data_preview: str = ""
    tokens_affected: int = 0
    operation_details: Dict[str, Any] = {}


class SubAgentCallInfoData(BaseModel):
    agent_name: str = ""
    agent_id: str = ""
    input_query: str = ""
    child_trace_id: Optional[str] = None
    timeout: float = 0.0
    result_preview: str = ""


class ReasoningInfoData(BaseModel):
    reasoning_content: str = ""
    reasoning_type: str = ""
    plan_steps: List[str] = []
    confidence: float = 0.0


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
    status: str = "pending"
    # Enhanced monitoring fields
    prompt_info: Optional[PromptBuildInfoData] = None
    skill_info: Optional[List[SkillInfoData]] = None
    tool_selection: Optional[ToolSelectionInfoData] = None
    memory_info: Optional[MemoryOperationInfoData] = None
    subagent_info: Optional[SubAgentCallInfoData] = None
    reasoning_info: Optional[ReasoningInfoData] = None
    # Hierarchy
    sub_steps: List['ExecutionStepData'] = []
    parent_step_id: Optional[str] = None
    depth: int = 0


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
    # Hierarchy
    parent_trace_id: Optional[str] = None
    child_trace_ids: List[str] = []
    depth: int = 0
    # Statistics
    cost_estimate: float = 0.0
    context_window_usage: float = 0.0
    llm_call_count: int = 0
    tool_call_count: int = 0


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
    try:
        trace_dict = trace.model_dump()
        traces[trace.id] = trace_dict
        
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
        data = await request.json()
        trace_id = data.get("id", "unknown")
        traces[trace_id] = data
        await broadcast_trace(data)
        return {"status": "ok", "id": trace_id}
    except Exception as e:
        print(f"Error in raw trace: {e}")
        return {"status": "error", "message": str(e)}


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


@app.get("/api/traces/{trace_id}/children")
async def get_child_traces(trace_id: str):
    """Get child traces of a specific trace."""
    if trace_id not in traces:
        return {"error": "Trace not found"}, 404
    
    trace = traces[trace_id]
    child_ids = trace.get("child_trace_ids", [])
    child_traces = [traces[cid] for cid in child_ids if cid in traces]
    return {"children": child_traces}


class CompareRequest(BaseModel):
    trace_id_1: str
    trace_id_2: str


@app.post("/api/traces/compare")
async def compare_traces(request: CompareRequest):
    """Compare two traces and return differences."""
    if request.trace_id_1 not in traces:
        return {"error": f"Trace {request.trace_id_1} not found"}, 404
    if request.trace_id_2 not in traces:
        return {"error": f"Trace {request.trace_id_2} not found"}, 404
    
    trace1 = traces[request.trace_id_1]
    trace2 = traces[request.trace_id_2]
    
    # Calculate differences
    diff = {
        "trace1_id": request.trace_id_1,
        "trace2_id": request.trace_id_2,
        "latency_diff_ms": trace2.get("total_latency_ms", 0) - trace1.get("total_latency_ms", 0),
        "tokens_diff": trace2.get("total_tokens", 0) - trace1.get("total_tokens", 0),
        "steps_count_diff": len(trace2.get("steps", [])) - len(trace1.get("steps", [])),
        "cost_diff": trace2.get("cost_estimate", 0) - trace1.get("cost_estimate", 0),
        "status_changed": trace1.get("status") != trace2.get("status"),
        "trace1_status": trace1.get("status"),
        "trace2_status": trace2.get("status"),
    }
    
    return {"comparison": diff}


@app.get("/api/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time metrics for all traces."""
    if not traces:
        return {
            "total_traces": 0,
            "success_rate": 0,
            "avg_latency_ms": 0,
            "total_tokens": 0,
            "total_cost": 0,
        }
    
    total = len(traces)
    successful = sum(1 for t in traces.values() if t.get("status") == "success")
    latencies = [t.get("total_latency_ms", 0) for t in traces.values()]
    tokens = [t.get("total_tokens", 0) for t in traces.values()]
    costs = [t.get("cost_estimate", 0) for t in traces.values()]
    
    return {
        "total_traces": total,
        "success_rate": successful / total if total > 0 else 0,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "total_tokens": sum(tokens),
        "total_cost": sum(costs),
    }


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