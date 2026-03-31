"""AgentScope Backend API v2 - Complete Implementation.

This is the production-ready version with all endpoints implemented.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), '..', 'sdk')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from storage_manager import get_storage, health_check, reset_storage

# In-memory storage for WebSocket connections
connected_websockets: List[WebSocket] = []


# ============================================================================
# Data Models
# ============================================================================

class ToolCallData(BaseModel):
    id: str
    name: str
    arguments: dict
    result: Optional[Any] = None
    error: Optional[Any] = None
    latency_ms: float = 0.0


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


class SkillInfoData(BaseModel):
    name: str
    description: str = ""
    status: str = "loaded"
    error: Optional[str] = None
    load_time_ms: float = 0.0


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
    cost_estimate: float = 0.0
    llm_call_count: int = 0
    tool_call_count: int = 0
    parent_trace_id: Optional[str] = None
    child_trace_ids: List[str] = []


class CompareRequest(BaseModel):
    trace_id_1: str
    trace_id_2: str


class CompareResult(BaseModel):
    trace1_id: str
    trace2_id: str
    latency_diff_ms: float
    tokens_diff: int
    steps_count_diff: int
    cost_diff: float
    status_changed: bool
    trace1_status: str
    trace2_status: str


class RealtimeMetrics(BaseModel):
    total_traces: int
    success_rate: float
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    traces_per_minute: float
    error_rate: float


class BatchDeleteRequest(BaseModel):
    trace_ids: List[str]


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 AgentScope Backend v2 starting...")
    print("="*60)
    
    # Health check on startup
    health = health_check()
    print(f"📦 Storage Backend: {health['storage_backend']}")
    print(f"💚 Health Status: {'OK' if health['healthy'] else 'ERROR'}")
    if health.get('stats'):
        print(f"📊 Initial Stats: {health['stats']}")
    print("="*60)
    
    yield
    
    print("="*60)
    print("👋 AgentScope Backend v2 shutting down...")
    print("="*60)


app = FastAPI(
    title="AgentScope",
    description="Agent debugging and observability platform - v2 Complete",
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


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed output."""
    print(f"❌ Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    print(f"❌ Unhandled error: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )


# ============================================================================
# WebSocket Utilities
# ============================================================================

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


async def broadcast_event(event_type: str, data: dict):
    """Broadcast a general event to all WebSocket clients."""
    disconnected = []
    for ws in connected_websockets:
        try:
            await ws.send_json({
                "type": event_type,
                "data": data
            })
        except Exception:
            disconnected.append(ws)
    
    for ws in disconnected:
        if ws in connected_websockets:
            connected_websockets.remove(ws)


# ============================================================================
# API Endpoints - Health & Info
# ============================================================================

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    storage = get_storage()
    is_healthy = storage.health_check()
    
    return {
        "status": "ok" if is_healthy else "error",
        "version": "0.2.0",
        "timestamp": datetime.now().isoformat(),
        "storage": {
            "backend": storage.__class__.__name__,
            "healthy": is_healthy,
            "stats": storage.get_stats() if is_healthy else None
        }
    }


@app.get("/api/info")
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": "AgentScope API",
        "version": "0.2.0",
        "endpoints": {
            "traces": "/api/traces",
            "trace_detail": "/api/traces/{id}",
            "trace_children": "/api/traces/{id}/children",
            "compare": "/api/traces/compare",
            "stats": "/api/stats",
            "metrics": "/api/metrics/realtime",
            "health": "/api/health",
        },
        "storage_backends": ["memory", "sqlite"],
        "websocket": "/ws"
    }


# ============================================================================
# API Endpoints - Trace CRUD
# ============================================================================

@app.get("/api/traces")
async def get_traces(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
):
    """Get all traces with filtering and pagination.
    
    Query Parameters:
        limit: Maximum number of traces to return (1-1000)
        offset: Number of traces to skip
        status: Filter by status (success, error, pending)
        tag: Filter by tag
        search: Search in name and input_query
        start_time: Filter traces after this ISO timestamp
        end_time: Filter traces before this ISO timestamp
    """
    storage = get_storage()
    
    # Build filters
    tags = [tag] if tag else None
    
    # Parse time filters
    start_dt = None
    end_dt = None
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            pass
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    # Get traces from storage
    traces = storage.list_traces(
        limit=limit,
        offset=offset,
        tags=tags,
        status=status,
        start_time=start_dt,
        end_time=end_dt,
    )
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        traces = [
            t for t in traces
            if (search_lower in t.get("name", "").lower() or
                search_lower in t.get("input_query", "").lower())
        ]
    
    # Get total count for pagination
    total = storage.count_traces(
        tags=tags,
        status=status,
        start_time=start_dt,
        end_time=end_dt,
    )
    
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
    """Get a specific trace by ID."""
    storage = get_storage()
    trace = storage.get_trace(trace_id)
    
    if not trace:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found", "trace_id": trace_id}
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
        
        return {
            "status": "ok",
            "id": trace.id,
            "message": "Trace saved successfully"
        }
    except Exception as e:
        import traceback
        print(f"❌ ERROR in create_trace: {e}")
        traceback.print_exc()
        raise


@app.post("/api/traces/raw")
async def create_trace_raw(request: Request):
    """Create or update a trace from raw JSON (for debugging)."""
    try:
        storage = get_storage()
        data = await request.json()
        trace_id = data.get("id", "unknown")
        
        # Ensure required fields
        if "start_time" not in data:
            data["start_time"] = datetime.now().isoformat()
        
        # Save to storage
        storage.save_trace(data)
        
        await broadcast_trace(data)
        return {
            "status": "ok",
            "id": trace_id,
            "message": "Raw trace saved"
        }
    except Exception as e:
        print(f"❌ Error in raw trace: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.delete("/api/traces/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a trace by ID."""
    storage = get_storage()
    deleted = storage.delete_trace(trace_id)
    
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found", "trace_id": trace_id}
        )
    
    await broadcast_event("trace_deleted", {"trace_id": trace_id})
    
    return {
        "status": "ok",
        "deleted": trace_id,
        "message": "Trace deleted successfully"
    }


@app.post("/api/traces/batch-delete")
async def batch_delete_traces(request: BatchDeleteRequest):
    """Delete multiple traces by ID."""
    storage = get_storage()
    deleted = []
    failed = []
    
    for trace_id in request.trace_ids:
        if storage.delete_trace(trace_id):
            deleted.append(trace_id)
        else:
            failed.append(trace_id)
    
    await broadcast_event("traces_batch_deleted", {
        "deleted_count": len(deleted),
        "failed_count": len(failed)
    })
    
    return {
        "status": "ok",
        "deleted": deleted,
        "failed": failed,
        "message": f"Deleted {len(deleted)} traces, {len(failed)} failed"
    }


# ============================================================================
# API Endpoints - Trace Relations
# ============================================================================

@app.get("/api/traces/{trace_id}/children")
async def get_child_traces(trace_id: str):
    """Get child traces of a specific trace."""
    storage = get_storage()
    
    # Get parent trace
    trace = storage.get_trace(trace_id)
    if not trace:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found", "trace_id": trace_id}
        )
    
    # Get child traces
    child_ids = trace.get("child_trace_ids", [])
    children = []
    
    for child_id in child_ids:
        child = storage.get_trace(child_id)
        if child:
            children.append(child)
    
    return {
        "trace_id": trace_id,
        "children": children,
        "count": len(children)
    }


@app.get("/api/traces/{trace_id}/parent")
async def get_parent_trace(trace_id: str):
    """Get parent trace of a specific trace."""
    storage = get_storage()
    
    trace = storage.get_trace(trace_id)
    if not trace:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found", "trace_id": trace_id}
        )
    
    parent_id = trace.get("parent_trace_id")
    if not parent_id:
        return {"parent": None, "message": "No parent trace"}
    
    parent = storage.get_trace(parent_id)
    if not parent:
        return {"parent": None, "message": "Parent trace not found", "parent_id": parent_id}
    
    return {"parent": parent}


# ============================================================================
# API Endpoints - Comparison & Analysis
# ============================================================================

@app.post("/api/traces/compare", response_model=CompareResult)
async def compare_traces(request: CompareRequest):
    """Compare two traces and return differences."""
    storage = get_storage()
    
    trace1 = storage.get_trace(request.trace_id_1)
    trace2 = storage.get_trace(request.trace_id_2)
    
    if not trace1:
        return JSONResponse(
            status_code=404,
            content={"error": f"Trace {request.trace_id_1} not found"}
        )
    if not trace2:
        return JSONResponse(
            status_code=404,
            content={"error": f"Trace {request.trace_id_2} not found"}
        )
    
    # Calculate differences
    diff = CompareResult(
        trace1_id=request.trace_id_1,
        trace2_id=request.trace_id_2,
        latency_diff_ms=trace2.get("total_latency_ms", 0) - trace1.get("total_latency_ms", 0),
        tokens_diff=trace2.get("total_tokens", 0) - trace1.get("total_tokens", 0),
        steps_count_diff=len(trace2.get("steps", [])) - len(trace1.get("steps", [])),
        cost_diff=trace2.get("cost_estimate", 0) - trace1.get("cost_estimate", 0),
        status_changed=trace1.get("status") != trace2.get("status"),
        trace1_status=trace1.get("status", "unknown"),
        trace2_status=trace2.get("status", "unknown"),
    )
    
    return diff


@app.get("/api/traces/{trace_id}/timeline")
async def get_trace_timeline(trace_id: str):
    """Get timeline analysis of a trace."""
    storage = get_storage()
    trace = storage.get_trace(trace_id)
    
    if not trace:
        return JSONResponse(
            status_code=404,
            content={"error": "Trace not found", "trace_id": trace_id}
        )
    
    steps = trace.get("steps", [])
    
    # Analyze step types
    step_types = {}
    for step in steps:
        step_type = step.get("type", "unknown")
        step_types[step_type] = step_types.get(step_type, 0) + 1
    
    # Calculate timeline
    timeline = []
    cumulative_latency = 0
    for step in steps:
        latency = step.get("latency_ms", 0)
        cumulative_latency += latency
        timeline.append({
            "step_id": step.get("id"),
            "type": step.get("type"),
            "timestamp": step.get("timestamp"),
            "latency_ms": latency,
            "cumulative_latency_ms": cumulative_latency,
        })
    
    return {
        "trace_id": trace_id,
        "total_steps": len(steps),
        "step_types": step_types,
        "timeline": timeline,
        "total_latency_ms": trace.get("total_latency_ms", 0),
    }


# ============================================================================
# API Endpoints - Statistics & Metrics
# ============================================================================

@app.get("/api/stats")
async def get_stats():
    """Get storage statistics."""
    storage = get_storage()
    stats = storage.get_stats()
    
    # Add additional computed stats
    total = stats.get("total_traces", 0)
    
    if total > 0 and "by_status" in stats:
        by_status = stats["by_status"]
        success = by_status.get("success", 0)
        stats["success_rate"] = success / total
        stats["error_rate"] = by_status.get("error", 0) / total
    
    return stats


@app.get("/api/metrics/realtime", response_model=RealtimeMetrics)
async def get_realtime_metrics():
    """Get real-time metrics for all traces."""
    storage = get_storage()
    
    # Get recent traces (last hour) using UTC
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_traces = storage.list_traces(
        limit=10000,
        start_time=one_hour_ago,
    )
    
    if not recent_traces:
        return RealtimeMetrics(
            total_traces=0,
            success_rate=0.0,
            avg_latency_ms=0.0,
            total_tokens=0,
            total_cost=0.0,
            traces_per_minute=0.0,
            error_rate=0.0,
        )
    
    total = len(recent_traces)
    successful = sum(1 for t in recent_traces if t.get("status") == "success")
    errors = sum(1 for t in recent_traces if t.get("status") == "error")
    
    latencies = [t.get("total_latency_ms", 0) for t in recent_traces if t.get("total_latency_ms", 0) > 0]
    tokens = [t.get("total_tokens", 0) for t in recent_traces]
    costs = [t.get("cost_estimate", 0) for t in recent_traces]
    
    # Calculate traces per minute
    if len(recent_traces) >= 2:
        times = [datetime.fromisoformat(t.get("start_time", "").replace('Z', '+00:00')) 
                 for t in recent_traces if t.get("start_time")]
        if times:
            time_span_minutes = (max(times) - min(times)).total_seconds() / 60
            traces_per_minute = total / time_span_minutes if time_span_minutes > 0 else 0
        else:
            traces_per_minute = 0
    else:
        traces_per_minute = 0
    
    return RealtimeMetrics(
        total_traces=total,
        success_rate=successful / total if total > 0 else 0,
        avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0,
        total_tokens=sum(tokens),
        total_cost=sum(costs),
        traces_per_minute=traces_per_minute,
        error_rate=errors / total if total > 0 else 0,
    )


@app.get("/api/metrics/historical")
async def get_historical_metrics(
    hours: int = Query(24, ge=1, le=168),
    interval: str = Query("hour", pattern="^(hour|day)$"),
):
    """Get historical metrics over time."""
    storage = get_storage()
    
    # Calculate time range using UTC (consistent with storage)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Get traces in range
    traces = storage.list_traces(
        limit=10000,
        start_time=start_time,
        end_time=end_time,
    )
    
    # Group by interval (convert UTC to local time - Asia/Shanghai)
    from collections import defaultdict
    import pytz
    
    local_tz = pytz.timezone('Asia/Shanghai')
    buckets = defaultdict(lambda: {"count": 0, "success": 0, "error": 0, "latency": [], "tokens": [], "cost": []})
    
    for trace in traces:
        ts = trace.get("start_time", "")
        if not ts:
            continue
        
        try:
            # Parse as UTC and convert to local time
            dt_utc = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            dt_local = dt_utc.astimezone(local_tz)
            
            if interval == "hour":
                bucket_key = dt_local.strftime("%Y-%m-%d %H:00")
            else:
                bucket_key = dt_local.strftime("%Y-%m-%d")
            
            buckets[bucket_key]["count"] += 1
            if trace.get("status") == "success":
                buckets[bucket_key]["success"] += 1
            elif trace.get("status") == "error":
                buckets[bucket_key]["error"] += 1
            
            buckets[bucket_key]["latency"].append(trace.get("total_latency_ms", 0))
            buckets[bucket_key]["tokens"].append(trace.get("total_tokens", 0))
            buckets[bucket_key]["cost"].append(trace.get("cost_estimate", 0))
        except ValueError:
            continue
    
    # Format results
    results = []
    for bucket_key in sorted(buckets.keys()):
        bucket = buckets[bucket_key]
        count = bucket["count"]
        results.append({
            "timestamp": bucket_key,
            "total_traces": count,
            "success_rate": bucket["success"] / count if count > 0 else 0,
            "error_rate": bucket["error"] / count if count > 0 else 0,
            "avg_latency_ms": sum(bucket["latency"]) / len(bucket["latency"]) if bucket["latency"] else 0,
            "total_tokens": sum(bucket["tokens"]),
            "total_cost": sum(bucket["cost"]),
        })
    
    return {
        "interval": interval,
        "hours": hours,
        "data": results
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_websockets.append(websocket)
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    print(f"🔌 WebSocket client connected: {client_info}")
    
    try:
        # Send initial data
        storage = get_storage()
        traces = storage.list_traces(limit=100)
        await websocket.send_json({
            "type": "initial_data",
            "traces": traces,
            "count": len(traces)
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                data = json.loads(message)
                
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                
                elif msg_type == "subscribe":
                    # Client can subscribe to specific trace updates
                    trace_id = data.get("trace_id")
                    await websocket.send_json({
                        "type": "subscribed",
                        "trace_id": trace_id
                    })
                
                elif msg_type == "get_trace":
                    # Client requests specific trace
                    trace_id = data.get("trace_id")
                    trace = storage.get_trace(trace_id)
                    await websocket.send_json({
                        "type": "trace_data",
                        "trace": trace,
                        "found": trace is not None
                    })
                
                elif msg_type == "get_recent":
                    # Client requests recent traces
                    limit = data.get("limit", 10)
                    traces = storage.list_traces(limit=limit)
                    await websocket.send_json({
                        "type": "recent_traces",
                        "traces": traces
                    })
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        print(f"👋 WebSocket client disconnected: {client_info}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


# ============================================================================
# Static Files (Frontend)
# ============================================================================

frontend_build_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
    print(f"📁 Serving frontend from: {frontend_build_path}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("AGENTSCOPE_PORT", "8000"))
    host = os.getenv("AGENTSCOPE_HOST", "0.0.0.0")
    
    print(f"🚀 Starting AgentScope Backend v2 on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
