"""AgentScope - Agent debugging and observability platform."""

from .monitor import (
    init_monitor,
    trace,
    trace_scope,
    instrument_llm,
    instrument_openai,
    instrumented_tool,
    get_current_trace,
    add_step,
    add_llm_call,
    add_tool_call,
    add_thinking,
    add_memory,
)
from .models import TraceEvent, ExecutionStep, ToolCall, StepType, Status

__version__ = "0.2.0"
__all__ = [
    # Core initialization
    "init_monitor",
    # Tracing APIs
    "trace",
    "trace_scope",
    # Auto-instrumentation
    "instrument_llm",
    "instrument_openai",
    "instrumented_tool",
    # Utilities
    "get_current_trace",
    "add_step",
    "add_llm_call",
    "add_tool_call",
    "add_thinking",
    "add_memory",
    # Models
    "TraceEvent",
    "ExecutionStep",
    "ToolCall",
    "StepType",
    "Status",
]
