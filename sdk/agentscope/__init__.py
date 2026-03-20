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
    # Enhanced monitoring APIs
    add_prompt_build_step,
    add_skills_loading_step,
    add_tool_selection_step,
    add_memory_operation_step,
    add_subagent_call_step,
    add_reasoning_step,
    # Token pricing APIs
    set_token_pricing,
    get_token_pricing,
    calculate_cost,
)
from .models import (
    TraceEvent, ExecutionStep, ToolCall, StepType, Status,
    # Enhanced models
    SkillInfo,
    PromptMessage,
    PromptBuildInfo,
    ToolSelectionInfo,
    MemoryOperationInfo,
    SubAgentCallInfo,
    ReasoningInfo,
)

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
    # Enhanced monitoring APIs
    "add_prompt_build_step",
    "add_skills_loading_step",
    "add_tool_selection_step",
    "add_memory_operation_step",
    "add_subagent_call_step",
    "add_reasoning_step",
    # Token pricing APIs
    "set_token_pricing",
    "get_token_pricing",
    "calculate_cost",
    # Models
    "TraceEvent",
    "ExecutionStep",
    "ToolCall",
    "StepType",
    "Status",
    # Enhanced models
    "SkillInfo",
    "PromptMessage",
    "PromptBuildInfo",
    "ToolSelectionInfo",
    "MemoryOperationInfo",
    "SubAgentCallInfo",
    "ReasoningInfo",
]
