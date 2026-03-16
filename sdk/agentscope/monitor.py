"""Core monitoring functionality for AgentScope."""

import functools
import requests
import threading
import logging
from typing import Optional, List, Callable, Any
from contextvars import ContextVar
from datetime import datetime

from .models import TraceEvent, ExecutionStep, ToolCall, StepType, Status

# Global configuration
_monitor_url: Optional[str] = None
_current_trace: ContextVar[Optional[TraceEvent]] = ContextVar('current_trace', default=None)

logger = logging.getLogger(__name__)


def init_monitor(url: str = "http://localhost:8000"):
    """Initialize the AgentScope monitor.
    
    Args:
        url: The URL of the AgentScope backend server
    """
    global _monitor_url
    _monitor_url = url.rstrip('/')
    logger.info(f"AgentScope monitor initialized: {_monitor_url}")


def get_current_trace() -> Optional[TraceEvent]:
    """Get the current trace in context."""
    return _current_trace.get()


def set_current_trace(trace: Optional[TraceEvent]):
    """Set the current trace in context."""
    _current_trace.set(trace)


def _send_trace(trace: TraceEvent):
    """Send trace to the backend server."""
    global _monitor_url
    if not _monitor_url:
        return
    
    try:
        response = requests.post(
            f"{_monitor_url}/api/traces",
            json=trace.to_dict(),
            timeout=5
        )
        if response.status_code != 200:
            logger.warning(f"Failed to send trace: {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to send trace: {e}")


def trace(name: Optional[str] = None, tags: Optional[List[str]] = None):
    """Decorator to trace an Agent function.
    
    Args:
        name: Name of the trace (defaults to function name)
        tags: List of tags for categorization
    
    Example:
        @trace(name="my_agent", tags=["production"])
        def my_agent(query: str):
            return llm.complete(query)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create new trace
            trace_event = TraceEvent(
                name=name or func.__name__,
                tags=tags or [],
            )
            
            # Set as current trace
            set_current_trace(trace_event)
            
            # Add input step
            input_content = str(args[0]) if args else str(kwargs)
            trace_event.input_query = input_content
            
            input_step = ExecutionStep(
                type=StepType.INPUT,
                content=input_content,
                status=Status.SUCCESS,
            )
            trace_event.add_step(input_step)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Add output step
                output_content = str(result) if result else ""
                trace_event.output_result = output_content
                
                output_step = ExecutionStep(
                    type=StepType.OUTPUT,
                    content=output_content[:500],  # Truncate for display
                    status=Status.SUCCESS,
                )
                trace_event.add_step(output_step)
                trace_event.finish(Status.SUCCESS)
                
                return result
                
            except Exception as e:
                # Add error step
                error_step = ExecutionStep(
                    type=StepType.ERROR,
                    content=str(e),
                    status=Status.ERROR,
                )
                trace_event.add_step(error_step)
                trace_event.finish(Status.ERROR)
                raise
                
            finally:
                # Send trace to backend
                _send_trace(trace_event)
                set_current_trace(None)
        
        return wrapper
    return decorator


# Utility functions for manual tracing

def add_step(
    step_type: StepType,
    content: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    latency_ms: float = 0.0,
    metadata: Optional[dict] = None,
):
    """Add a step to the current trace."""
    trace = get_current_trace()
    if not trace:
        return
    
    step = ExecutionStep(
        type=step_type,
        content=content,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        latency_ms=latency_ms,
        metadata=metadata or {},
        status=Status.SUCCESS,
    )
    trace.add_step(step)


def add_llm_call(
    prompt: str,
    completion: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    latency_ms: float = 0.0,
):
    """Record an LLM call step."""
    add_step(
        step_type=StepType.LLM_CALL,
        content=f"Prompt: {prompt[:200]}...\nCompletion: {completion[:200]}...",
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        latency_ms=latency_ms,
        metadata={"prompt": prompt, "completion": completion},
    )


def add_tool_call(
    tool_name: str,
    arguments: dict,
    result: Any,
    error: Optional[str] = None,
    latency_ms: float = 0.0,
):
    """Record a tool call step."""
    trace = get_current_trace()
    if not trace:
        return
    
    tool_call = ToolCall(
        name=tool_name,
        arguments=arguments,
        result=result,
        error=error,
        latency_ms=latency_ms,
    )
    
    step = ExecutionStep(
        type=StepType.TOOL_CALL,
        content=f"Tool: {tool_name}",
        tool_call=tool_call,
        latency_ms=latency_ms,
        status=Status.ERROR if error else Status.SUCCESS,
    )
    trace.add_step(step)


def add_thinking(content: str):
    """Record a thinking/reasoning step."""
    add_step(StepType.THINKING, content)