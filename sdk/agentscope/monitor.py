"""Core monitoring functionality for AgentScope - Scheme 3 Implementation.

This module provides deep monitoring with low intrusion using:
1. Context Manager pattern (trace_scope)
2. ContextVars for context propagation
3. Auto-instrumentation for LLM clients and tools
"""

import functools
import requests
import threading
import logging
import time
import json
from typing import Optional, List, Callable, Any, Dict
from contextvars import ContextVar
from contextlib import contextmanager
from datetime import datetime

from .models import TraceEvent, ExecutionStep, ToolCall, StepType, Status

# Global configuration
_monitor_url: Optional[str] = None
_current_trace: ContextVar[Optional[TraceEvent]] = ContextVar('current_trace', default=None)

logger = logging.getLogger(__name__)

# Track which clients have been instrumented (to avoid double wrapping)
_instrumented_clients: set = set()
_original_openai_create: Optional[Callable] = None


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
            try:
                error_detail = response.json()
                logger.warning(f"Error detail: {error_detail}")
            except:
                logger.warning(f"Response text: {response.text[:200]}")
    except Exception as e:
        logger.warning(f"Failed to send trace: {e}")


# =============================================================================
# Scheme 3: Context Manager Pattern (trace_scope)
# =============================================================================

@contextmanager
def trace_scope(
    name: str,
    input_query: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Context manager for tracing Agent execution.
    
    This is the core of Scheme 3 - creating a "tracing bubble" where all
    LLM calls, tool executions, and memory operations are automatically recorded.
    
    Args:
        name: Name of the trace
        input_query: The input query/prompt
        tags: List of tags for categorization
        metadata: Additional metadata
        
    Example:
        with trace_scope("my_agent", input_query="Hello"):
            result = llm.chat("Hello")  # Auto-recorded
            tool_result = search("query")  # Auto-recorded
            return result
    """
    trace_event = TraceEvent(
        name=name,
        tags=tags or [],
        input_query=input_query,
    )
    
    if metadata:
        trace_event.metadata = metadata
    
    # Set as current trace in context
    token = _current_trace.set(trace_event)
    
    # Add input step
    if input_query:
        input_step = ExecutionStep(
            type=StepType.INPUT,
            content=input_query[:1000],
            status=Status.SUCCESS,
        )
        trace_event.add_step(input_step)
    
    logger.debug(f"AgentScope: Started trace {trace_event.id} for {name}")
    
    try:
        yield trace_event
        trace_event.finish(Status.SUCCESS)
        logger.debug(f"AgentScope: Trace {trace_event.id} finished successfully")
    except Exception as e:
        # Add error step
        error_step = ExecutionStep(
            type=StepType.ERROR,
            content=str(e)[:500],
            status=Status.ERROR,
        )
        trace_event.add_step(error_step)
        trace_event.finish(Status.ERROR)
        logger.debug(f"AgentScope: Trace {trace_event.id} finished with error: {e}")
        raise
    finally:
        # Send trace to backend
        _send_trace(trace_event)
        # Clear context
        _current_trace.reset(token)


# =============================================================================
# Auto-Instrumentation: LLM Clients
# =============================================================================

def _wrap_openai_chat_completion(original_create):
    """Wrap OpenAI's chat.completions.create method to auto-trace LLM calls."""
    
    @functools.wraps(original_create)
    def wrapped_create(self, *args, **kwargs):
        trace = get_current_trace()
        if not trace:
            # No active trace, just call original
            return original_create(self, *args, **kwargs)
        
        # Extract information for tracing
        model = kwargs.get('model', 'unknown')
        messages = kwargs.get('messages', [])
        
        # Build prompt preview
        prompt_preview = ""
        if messages:
            last_msg = messages[-1] if isinstance(messages, list) else messages
            if isinstance(last_msg, dict):
                prompt_preview = last_msg.get('content', '')[:200]
            else:
                prompt_preview = str(last_msg)[:200]
        
        start_time = time.time()
        tokens_input = 0
        tokens_output = 0
        
        try:
            # Call original method
            result = original_create(self, *args, **kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract token usage if available
            if hasattr(result, 'usage') and result.usage:
                tokens_input = getattr(result.usage, 'prompt_tokens', 0)
                tokens_output = getattr(result.usage, 'completion_tokens', 0)
            
            # Extract completion content
            completion_preview = ""
            if hasattr(result, 'choices') and result.choices:
                choice = result.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    completion_preview = getattr(choice.message, 'content', '')[:200]
                elif hasattr(choice, 'text'):
                    completion_preview = choice.text[:200]
            
            # Add LLM call step to trace
            step = ExecutionStep(
                type=StepType.LLM_CALL,
                content=f"Model: {model}\nPrompt: {prompt_preview}...\nCompletion: {completion_preview}...",
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=latency_ms,
                metadata={
                    'model': model,
                    'messages_count': len(messages) if isinstance(messages, list) else 1,
                    'prompt_preview': prompt_preview,
                    'completion_preview': completion_preview,
                },
                status=Status.SUCCESS,
            )
            trace.add_step(step)
            logger.debug(f"AgentScope: Recorded LLM call to {model} ({latency_ms:.1f}ms)")
            
            return result
            
        except Exception as e:
            # Record error
            latency_ms = (time.time() - start_time) * 1000
            step = ExecutionStep(
                type=StepType.LLM_CALL,
                content=f"Model: {model}\nError: {str(e)}",
                latency_ms=latency_ms,
                metadata={'model': model, 'error': str(e)},
                status=Status.ERROR,
            )
            trace.add_step(step)
            raise
    
    return wrapped_create


def instrument_llm(client: Any) -> Any:
    """Instrument an LLM client to auto-trace all calls.
    
    Currently supports:
    - OpenAI client (openai.OpenAI)
    - OpenAI Async client (openai.AsyncOpenAI)
    
    Args:
        client: The LLM client instance
        
    Returns:
        The instrumented client (same instance, methods wrapped)
        
    Example:
        import openai
        client = instrument_llm(openai.OpenAI())
        
        with trace_scope("my_agent"):
            # This call will be automatically traced
            response = client.chat.completions.create(...)
    """
    global _instrumented_clients, _original_openai_create
    
    # Check if already instrumented
    client_id = id(client)
    if client_id in _instrumented_clients:
        return client
    
    # Try to detect client type and instrument
    client_class = client.__class__.__name__
    module_name = getattr(client.__class__, '__module__', '')
    
    try:
        if 'openai' in module_name.lower():
            # OpenAI client
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                orig_create = client.chat.completions.create
                if not hasattr(orig_create, '_agentscope_wrapped'):
                    client.chat.completions.create = _wrap_openai_chat_completion(orig_create)
                    client.chat.completions.create._agentscope_wrapped = True
                    _original_openai_create = orig_create
                    logger.info(f"AgentScope: Instrumented {client_class}")
        
        _instrumented_clients.add(client_id)
        
    except Exception as e:
        logger.warning(f"AgentScope: Failed to instrument client: {e}")
    
    return client


def instrument_openai():
    """Globally instrument the OpenAI module.
    
    This patches the OpenAI class so all new instances are automatically
    instrumented.
    
    Example:
        instrument_openai()
        
        # All OpenAI clients created after this will be auto-traced
        client = openai.OpenAI()
    """
    try:
        import openai
        
        original_init = openai.OpenAI.__init__
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Auto-instrument this instance
            instrument_llm(self)
        
        openai.OpenAI.__init__ = patched_init
        logger.info("AgentScope: OpenAI module instrumented globally")
        
    except ImportError:
        logger.warning("AgentScope: OpenAI not installed, skipping global instrumentation")
    except Exception as e:
        logger.warning(f"AgentScope: Failed to instrument OpenAI: {e}")


# =============================================================================
# Auto-Instrumentation: Tools
# =============================================================================

def instrumented_tool(func: Optional[Callable] = None, *, name: Optional[str] = None):
    """Decorator to auto-trace tool function calls.
    
    Args:
        func: The function to decorate (when used without parentheses)
        name: Optional custom name for the tool (defaults to function name)
        
    Returns:
        Decorated function that auto-traces its execution
        
    Example:
        @instrumented_tool
        def search(query: str) -> str:
            return requests.get(f"https://api.com?q={query}").text
        
        @instrumented_tool(name="weather_api")
        def get_weather(city: str) -> dict:
            return {"temp": 25, "weather": "sunny"}
            
        with trace_scope("agent"):
            result = search("python")  # Auto-traced
    """
    def decorator(f: Callable) -> Callable:
        tool_name = name or f.__name__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            trace = get_current_trace()
            if not trace:
                # No active trace, just call original
                return f(*args, **kwargs)
            
            # Build arguments dict
            arguments = {}
            if args:
                arguments['args'] = [str(a)[:100] for a in args]
            if kwargs:
                arguments['kwargs'] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            start_time = time.time()
            error_msg = None
            result = None
            success = False
            
            try:
                result = f(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                
                # Format result for recording (handle None as valid return value)
                result_str = None
                if success:
                    try:
                        result_str = json.dumps(result, ensure_ascii=False)[:500] if result is not None else "null"
                    except (TypeError, ValueError):
                        result_str = str(result)[:500]
                
                # Add tool call step
                tool_call = ToolCall(
                    name=tool_name,
                    arguments=arguments,
                    result=result_str,
                    error=error_msg,
                    latency_ms=latency_ms,
                )
                
                step = ExecutionStep(
                    type=StepType.TOOL_CALL,
                    content=f"Tool: {tool_name}\nArgs: {json.dumps(arguments, ensure_ascii=False)[:200]}",
                    tool_call=tool_call,
                    latency_ms=latency_ms,
                    status=Status.ERROR if error_msg else Status.SUCCESS,
                )
                trace.add_step(step)
                logger.debug(f"AgentScope: Recorded tool call {tool_name} ({latency_ms:.1f}ms)")
        
        return wrapper
    
    if func is not None:
        # Used without parentheses: @instrumented_tool
        return decorator(func)
    else:
        # Used with parentheses: @instrumented_tool(name="...")
        return decorator


# =============================================================================
# Legacy Decorator (for backward compatibility)
# =============================================================================

def trace(name: Optional[str] = None, tags: Optional[List[str]] = None):
    """Decorator to trace an Agent function (legacy API).
    
    This is kept for backward compatibility. New code should use trace_scope().
    
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
            input_content = str(args[0]) if args else str(kwargs)
            
            with trace_scope(
                name=name or func.__name__,
                input_query=input_content,
                tags=tags
            ):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# Utility functions for manual tracing
# =============================================================================

def add_step(
    step_type: StepType,
    content: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    latency_ms: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
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
    """Manually record an LLM call step."""
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
    """Manually record a tool call step."""
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


def add_memory(action: str, details: str):
    """Record a memory operation step."""
    add_step(
        step_type=StepType.THINKING,
        content=f"Memory {action}: {details}",
    )
