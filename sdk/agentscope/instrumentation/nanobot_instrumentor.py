"""Non-intrusive instrumentation for nanobot using monkey patching."""

import functools
import time
import os
from typing import Any, Optional, Callable

from loguru import logger

from ..monitor import (
    init_monitor, trace_scope, add_step, add_llm_call, add_tool_call,
    add_prompt_build_step, add_tool_selection_step
)
from ..models import StepType, Status, ExecutionStep


# Get backend URL from environment or use default
AGENTSCOPE_BACKEND_URL = os.getenv("AGENTSCOPE_BACKEND_URL", "http://localhost:8000")

# Constants
TOOL_CALL_PENDING_RESULT = "[Tool call requested by LLM, execution pending]"


_instrumented = False


def _instrument_context_builder(context_builder_class):
    """Instrument ContextBuilder to capture prompt building."""
    original_build_messages = context_builder_class.build_messages
    
    @functools.wraps(original_build_messages)
    def monitored_build_messages(self, *args, **kwargs):
        # Call original method first
        result = original_build_messages(self, *args, **kwargs)
        
        # Record prompt build
        try:
            from ..monitor import get_current_trace
            trace = get_current_trace()
            if not trace:
                return result
            
            # Get call sequence number for this trace
            if not hasattr(trace, '_build_messages_count'):
                trace._build_messages_count = 0
            trace._build_messages_count += 1
            call_num = trace._build_messages_count
            
            # Get system prompt
            system_prompt = ""
            if hasattr(self, 'build_system_prompt'):
                try:
                    system_prompt = self.build_system_prompt()[:500]  # Truncate
                except:
                    pass
            
            # Record prompt build with sequence info
            if result and isinstance(result, list):
                add_prompt_build_step(
                    messages=result,
                    system_prompt=system_prompt,
                    model_config={},
                    metadata={"call_sequence": call_num}
                )
                logger.debug(f"AgentScope: Recorded prompt with {len(result)} messages (call #{call_num})")
                    
        except Exception as e:
            logger.warning(f"AgentScope: Failed to record prompt build: {e}")
        
        return result
    
    context_builder_class.build_messages = monitored_build_messages
    logger.info("AgentScope: ContextBuilder instrumented")


def _instrument_agent_loop(agent_loop_class):
    """Instrument AgentLoop class."""
    
    # Wrap the main run method
    original_run = agent_loop_class.run
    
    @functools.wraps(original_run)
    async def monitored_run(self):
        try:
            init_monitor(AGENTSCOPE_BACKEND_URL)
            logger.info("AgentScope: Non-intrusive monitoring enabled")
        except Exception as e:
            logger.warning(f"AgentScope: Failed to initialize: {e}")
        
        return await original_run(self)
    
    agent_loop_class.run = monitored_run
    
    # Wrap _process_message to create trace context
    original_process_message = agent_loop_class._process_message
    
    @functools.wraps(original_process_message)
    async def monitored_process_message(self, msg, session_key=None, on_progress=None, on_stream=None, on_stream_end=None):
        # Skip system channels
        if hasattr(msg, 'channel') and msg.channel in ("system", "inter_agent"):
            return await original_process_message(self, msg, session_key, on_progress, on_stream=on_stream, on_stream_end=on_stream_end)

        # Extract user info for better trace naming
        user_id = getattr(msg, 'user_id', 'unknown')
        channel = getattr(msg, 'channel', 'unknown')

        # Buffer to collect streaming content
        stream_content_parts = []
        
        # Wrap on_stream callback to capture streaming content
        original_on_stream = on_stream
        async def wrapped_on_stream(content):
            if content:
                stream_content_parts.append(str(content))
            if original_on_stream:
                await original_on_stream(content)
        
        # Wrap on_stream_end callback
        original_on_stream_end = on_stream_end
        async def wrapped_on_stream_end(*args, **kwargs):
            if original_on_stream_end:
                await original_on_stream_end(*args, **kwargs)

        # Create trace context
        with trace_scope(
            name=f"nanobot:{channel}",
            input_query=getattr(msg, 'content', '')[:1000],
            tags=["nanobot", channel, f"user:{user_id}"]
        ) as trace:
            # Execute and capture result
            result = await original_process_message(
                self, msg, session_key, on_progress,
                on_stream=wrapped_on_stream if on_stream else None,
                on_stream_end=wrapped_on_stream_end if on_stream_end else None
            )
            
            # Determine output content
            output_content = None
            
            # Case 1: Result has explicit content
            if result:
                if hasattr(result, 'content') and result.content:
                    output_content = result.content[:2000]
                elif hasattr(result, 'text') and result.text:
                    output_content = result.text[:2000]
                else:
                    output_str = str(result)
                    if output_str and output_str != 'None':
                        output_content = output_str[:2000]
            
            # Case 2: Stream content was captured
            if not output_content and stream_content_parts:
                output_content = ''.join(stream_content_parts)[:2000]
            
            # Case 3: Try to infer from last tool call (e.g., message tool)
            if not output_content:
                from ..monitor import get_current_trace
                current_trace = get_current_trace()
                if current_trace and current_trace.steps:
                    last_step = current_trace.steps[-1]
                    if last_step.type == StepType.TOOL_CALL and last_step.tool_call:
                        tool_name = last_step.tool_call.name
                        if tool_name == 'message':
                            output_content = f"[Response sent via {tool_name} tool]"
            
            # Record output step if we have content
            if output_content:
                add_step(StepType.OUTPUT, output_content)
            else:
                # Record a placeholder to indicate completion
                add_step(StepType.OUTPUT, "[Response completed]")
            
            return result
    
    agent_loop_class._process_message = monitored_process_message
    
    logger.info("AgentScope: AgentLoop instrumented")


async def _record_llm_iteration(
    original_func: Callable,
    iteration_count: int,
    is_streaming: bool,
    all_tools_used: list,
    **kwargs
) -> Any:
    """
    Record a single LLM iteration.
    
    This is a shared function for both streaming and non-streaming LLM calls.
    
    Args:
        original_func: The original LLM function to call
        iteration_count: Current iteration number
        is_streaming: Whether this is a streaming call
        all_tools_used: List to collect tool names
        **kwargs: Arguments passed to the original function
    
    Returns:
        The response from the original function
    """
    # Record prompt build before LLM call
    messages = kwargs.get('messages', [])
    tools = kwargs.get('tools', [])
    if messages:
        try:
            # Build comprehensive model config with all LLM parameters
            model_config = {
                "model": kwargs.get('model', 'unknown'),
                "iteration": iteration_count,
                "streaming": is_streaming,
            }
            
            # Add optional LLM parameters if present
            if 'temperature' in kwargs:
                model_config["temperature"] = kwargs['temperature']
            if 'max_tokens' in kwargs:
                model_config["max_tokens"] = kwargs['max_tokens']
            if 'reasoning_effort' in kwargs:
                model_config["reasoning_effort"] = kwargs['reasoning_effort']
            
            # Add tools info
            if tools:
                tool_names = []
                for tool in tools:
                    if isinstance(tool, dict):
                        name = tool.get('name') or tool.get('function', {}).get('name', 'unknown')
                        tool_names.append(name)
                if tool_names:
                    model_config["tools_available"] = len(tool_names)
                    model_config["tool_names"] = tool_names[:10]  # First 10 tools
            
            add_prompt_build_step(
                messages=messages,
                system_prompt="",
                model_config=model_config,
                metadata={
                    "iteration": iteration_count,
                    "type": "agent_loop_iteration",
                    "streaming": is_streaming,
                    "tools_count": len(tools) if tools else 0,
                    "has_temperature": 'temperature' in kwargs,
                    "has_max_tokens": 'max_tokens' in kwargs,
                    "has_reasoning_effort": 'reasoning_effort' in kwargs,
                }
            )
            tool_info = f", {len(tools)} tools" if tools else ""
            logger.debug(f"AgentScope: Recorded iteration #{iteration_count} prompt "
                        f"({len(messages)} messages{tool_info}, streaming={is_streaming})")
        except Exception as e:
            logger.warning(f"AgentScope: Failed to record prompt: {e}")
    
    # Call LLM
    start_time = time.time()
    try:
        response = await original_func(**kwargs)
    except Exception as e:
        logger.error(f"AgentScope: LLM call failed in iteration #{iteration_count}: {e}")
        raise
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Record LLM call
    try:
        # Build prompt preview (last 3 messages)
        prompt_text = "\n".join([
            f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:200]}"
            for m in messages[-3:]
        ])
        completion_text = str(getattr(response, 'content', '') or '')[:500]
        
        # Get token usage (use actual or estimate)
        usage = getattr(response, 'usage', None) or {}
        tokens_in = usage.get('prompt_tokens')
        tokens_out = usage.get('completion_tokens')
        
        if tokens_in is None:
            # Estimate: ~4 chars per token for English/Chinese mix
            tokens_in = sum(len(str(m.get('content', ''))) // 4 for m in messages)
        if tokens_out is None:
            tokens_out = len(completion_text) // 4
        
        add_llm_call(
            prompt=f"[Iteration {iteration_count}] {prompt_text[:500]}",
            completion=completion_text,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=latency_ms
        )
        logger.debug(f"AgentScope: Recorded iteration #{iteration_count} LLM call "
                    f"(tokens_in={tokens_in}, tokens_out={tokens_out})")
        
        # Record tool calls if present (LLM requested tools)
        tool_calls = getattr(response, 'tool_calls', None)
        if tool_calls:
            for tc in tool_calls:
                tool_name = getattr(tc, 'name', str(tc))
                tool_args = getattr(tc, 'arguments', {})
                if not isinstance(tool_args, dict):
                    tool_args = {"args": str(tool_args)}
                
                add_tool_call(
                    tool_name=tool_name,
                    arguments=tool_args,
                    result=TOOL_CALL_PENDING_RESULT,
                    latency_ms=0
                )
                all_tools_used.append(tool_name)
                logger.debug(f"AgentScope: Recorded tool call request: {tool_name}")
                    
    except Exception as e:
        logger.warning(f"AgentScope: Failed to record LLM call: {e}")
    
    return response


def _instrument_agent_runner(agent_runner_class):
    """Instrument AgentRunner to capture each iteration of the agent loop."""
    original_run = agent_runner_class.run
    
    @functools.wraps(original_run)
    async def monitored_run(self, spec):
        # Get current trace (created by _process_message)
        from ..monitor import get_current_trace
        trace = get_current_trace()
        
        # Record available tools once
        try:
            if hasattr(spec, 'tools') and spec.tools:
                tool_defs = spec.tools.get_definitions()
                if tool_defs:
                    available_tools = []
                    for tool in tool_defs:
                        if isinstance(tool, dict):
                            available_tools.append({
                                "name": tool.get('name', tool.get('function', {}).get('name', 'unknown')),
                                "description": tool.get('description', tool.get('function', {}).get('description', ''))
                            })
                    
                    if available_tools:
                        add_tool_selection_step(
                            selected_tool="(available)",
                            available_tools=available_tools,
                            reason=f"{len(available_tools)} tools available for agent loop"
                        )
        except Exception as e:
            logger.warning(f"AgentScope: Failed to record tool selection: {e}")
        
        # Track iteration count
        iteration_count = 0
        all_tools_used = []
        successful_tool_calls = 0
        failed_tool_calls = 0
        
        # Store original provider methods
        original_chat_with_retry = self.provider.chat_with_retry
        original_chat_stream_with_retry = self.provider.chat_stream_with_retry
        
        # Create monitored wrappers using shared logic
        async def monitored_chat_with_retry(**kwargs):
            nonlocal iteration_count
            iteration_count += 1
            return await _record_llm_iteration(
                original_chat_with_retry,
                iteration_count,
                is_streaming=False,
                all_tools_used=all_tools_used,
                **kwargs
            )
        
        async def monitored_chat_stream_with_retry(**kwargs):
            nonlocal iteration_count
            iteration_count += 1
            logger.info(f"AgentScope: LLM streaming call iteration #{iteration_count}")
            return await _record_llm_iteration(
                original_chat_stream_with_retry,
                iteration_count,
                is_streaming=True,
                all_tools_used=all_tools_used,
                **kwargs
            )
        
        # Replace provider methods temporarily
        logger.info(f"AgentScope: Replacing provider methods on {type(self.provider).__name__}")
        self.provider.chat_with_retry = monitored_chat_with_retry
        self.provider.chat_stream_with_retry = monitored_chat_stream_with_retry
        
        try:
            # Execute the agent run
            logger.debug(f"AgentScope: Starting agent run with monitoring")
            result = await original_run(self, spec)
            
            # Unpack result
            final_content, tools_used, all_messages = result
            
            # Count successful/failed tool calls by analyzing steps
            for step in trace.steps if trace else []:
                if step.type == StepType.TOOL_CALL and step.tool_call:
                    # Check if tool call has error
                    if step.tool_call.error:
                        failed_tool_calls += 1
                    else:
                        successful_tool_calls += 1
            
            # Determine completion status
            completion_status = "success"
            if trace and trace.status == Status.ERROR:
                completion_status = "failed"
            elif iteration_count >= spec.max_iterations:
                completion_status = "timeout"
            
            # Update trace evaluation metrics
            if trace:
                trace.iteration_count = iteration_count
                trace.successful_tool_calls = successful_tool_calls
                trace.failed_tool_calls = failed_tool_calls
                trace.completion_status = completion_status
                logger.info(f"AgentScope: Updated evaluation metrics - "
                           f"iterations={iteration_count}, "
                           f"successful_tools={successful_tool_calls}, "
                           f"failed_tools={failed_tool_calls}, "
                           f"status={completion_status}")
            
            # Record summary
            logger.info(f"AgentScope: Agent loop completed with {iteration_count} iterations, "
                       f"{len(all_tools_used)} tool calls, "
                       f"status={completion_status}")
            
            return result
            
        finally:
            # Restore original methods
            self.provider.chat_with_retry = original_chat_with_retry
            self.provider.chat_stream_with_retry = original_chat_stream_with_retry
    
    agent_runner_class.run = monitored_run
    logger.info("AgentScope: AgentRunner instrumented")


def instrument():
    """Instrument nanobot classes with AgentScope monitoring."""
    global _instrumented
    
    if _instrumented:
        logger.debug("AgentScope: Already instrumented")
        return
    
    try:
        from nanobot.agent.loop import AgentLoop
        from nanobot.agent.context import ContextBuilder
        from nanobot.agent.runner import AgentRunner
        
        _instrument_context_builder(ContextBuilder)
        _instrument_agent_loop(AgentLoop)
        _instrument_agent_runner(AgentRunner)
        
        _instrumented = True
        logger.info("AgentScope: Non-intrusive instrumentation complete")
        
    except ImportError as e:
        logger.warning(f"AgentScope: Cannot instrument nanobot: {e}")
    except Exception as e:
        logger.warning(f"AgentScope: Instrumentation failed: {e}")


def uninstrument():
    """Restore original methods."""
    global _instrumented
    _instrumented = False
    logger.info("AgentScope: Instrumentation removed (restart required)")


if os.getenv("AGENTSCOPE_AUTO_INSTRUMENT", "false").lower() == "true":
    try:
        instrument()
    except Exception:
        pass
