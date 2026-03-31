"""Non-intrusive instrumentation for nanobot using monkey patching."""

import functools
import time
import os
from typing import Any, Optional

from loguru import logger

from ..monitor import (
    init_monitor, trace_scope, add_step, add_llm_call, add_tool_call,
    add_prompt_build_step, add_skills_loading_step, add_reasoning_step,
    add_tool_selection_step, add_memory_operation_step
)
from ..models import StepType, Status, ExecutionStep


_instrumented = False


def _extract_skills_from_context(context_builder) -> list:
    """Extract skills list from ContextBuilder."""
    skills_data = []
    try:
        if hasattr(context_builder, 'skills') and context_builder.skills:
            skills_loader = context_builder.skills
            if hasattr(skills_loader, 'list_skills'):
                raw_skills = skills_loader.list_skills(filter_unavailable=False)
                for skill in raw_skills:
                    skills_data.append({
                        "name": skill.get("name", "unknown"),
                        "source": skill.get("source", "unknown"),
                        "status": "loaded"  # Simplified status
                    })
    except Exception as e:
        logger.debug(f"AgentScope: Failed to extract skills: {e}")
    return skills_data


def _instrument_context_builder(context_builder_class):
    """Instrument ContextBuilder to capture prompt building."""
    original_build_messages = context_builder_class.build_messages
    
    @functools.wraps(original_build_messages)
    def monitored_build_messages(self, *args, **kwargs):
        # Call original method
        result = original_build_messages(self, *args, **kwargs)
        
        # Record prompt build
        try:
            # Extract info from kwargs and self
            history = kwargs.get('history', args[0] if args else [])
            current_message = kwargs.get('current_message', '')
            
            # Build messages list for monitoring
            messages = []
            if isinstance(history, list):
                messages.extend(history)
            if current_message:
                messages.append({"role": "user", "content": current_message})
            
            # Get system prompt
            system_prompt = ""
            if hasattr(self, 'build_system_prompt'):
                try:
                    system_prompt = self.build_system_prompt()[:500]  # Truncate
                except:
                    pass
            
            # Record skills loading first (if available)
            skills_data = _extract_skills_from_context(self)
            if skills_data:
                from ..monitor import get_current_trace
                if get_current_trace():
                    add_skills_loading_step(skills=skills_data, total_time_ms=0)
                    logger.debug(f"AgentScope: Recorded {len(skills_data)} skills")
            
            # Record prompt build
            if result and isinstance(result, list):
                from ..monitor import get_current_trace
                if get_current_trace():
                    add_prompt_build_step(
                        messages=result,
                        system_prompt=system_prompt,
                        model_config={}  # Model config will be recorded at LLM call
                    )
                    logger.debug(f"AgentScope: Recorded prompt with {len(result)} messages")
                    
        except Exception as e:
            logger.debug(f"AgentScope: Failed to record prompt build: {e}")
        
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
            init_monitor("http://localhost:8000")
            logger.info("AgentScope: Non-intrusive monitoring enabled")
        except Exception as e:
            logger.debug(f"AgentScope: Failed to initialize: {e}")
        
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
        async def wrapped_on_stream_end():
            if original_on_stream_end:
                await original_on_stream_end()

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
    
    # Instrument LLM provider calls
    _instrument_provider_calls(agent_loop_class)
    
    logger.info("AgentScope: AgentLoop instrumented")


def _instrument_provider_calls(agent_loop_class):
    """Instrument LLM provider chat calls."""
    original_run_agent_loop = agent_loop_class._run_agent_loop
    
    @functools.wraps(original_run_agent_loop)
    async def monitored_run_agent_loop(self, initial_messages, on_progress=None, on_stream=None, on_stream_end=None, **kwargs):
        start_time = time.time()
        
        # Record agent loop start
        loop_step = None
        try:
            from ..monitor import get_current_trace
            trace = get_current_trace()
            if trace:
                loop_step = ExecutionStep(
                    type=StepType.THINKING,
                    content=f"🔄 Agent Loop: Processing {len(initial_messages)} messages with LLM",
                    status=Status.RUNNING,
                    metadata={"message_count": len(initial_messages)}
                )
                trace.add_step(loop_step)
        except Exception as e:
            logger.debug(f"AgentScope: Failed to add agent_loop step: {e}")

        # Record tool selection (available tools)
        try:
            if hasattr(self, 'tools') and self.tools:
                tool_defs = self.tools.get_definitions()
                if tool_defs:
                    available_tools = []
                    for tool in tool_defs:
                        if isinstance(tool, dict):
                            available_tools.append({
                                "name": tool.get('name', tool.get('function', {}).get('name', 'unknown')),
                                "description": tool.get('description', tool.get('function', {}).get('description', ''))
                            })
                    
                    # Only record if there are tools
                    if available_tools:
                        from ..monitor import get_current_trace
                        if get_current_trace():
                            add_tool_selection_step(
                                selected_tool="(available)",
                                available_tools=available_tools,
                                reason=f"{len(available_tools)} tools available for this request"
                            )
        except Exception as e:
            logger.debug(f"AgentScope: Failed to record tools: {e}")
        
        try:
            # Execute the loop
            result = await original_run_agent_loop(self, initial_messages, on_progress=on_progress, on_stream=on_stream, on_stream_end=on_stream_end, **kwargs)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            final_content, tools_used, all_msgs = result
            
            # Update agent loop step to success
            if loop_step:
                loop_step.status = Status.SUCCESS
                loop_step.latency_ms = latency_ms
                loop_step.content += f"\n✓ Completed in {latency_ms:.0f}ms"
            
            # Record LLM calls from messages
            try:
                from ..monitor import get_current_trace
                if get_current_trace():
                    # Count tokens roughly (this is an approximation)
                    tokens_in = sum(len(str(m.get('content', ''))) // 4 for m in initial_messages)
                    tokens_out = len(str(final_content)) // 4 if final_content else 0
                    
                    add_llm_call(
                        prompt=f"Agent loop with {len(initial_messages)} messages",
                        completion=final_content[:200] if final_content else "",
                        tokens_input=tokens_in,
                        tokens_output=tokens_out,
                        latency_ms=latency_ms
                    )
                    
                    # Record tool calls
                    for tool_name in tools_used:
                        add_tool_call(
                            tool_name=tool_name,
                            arguments={},
                            result="executed",
                            latency_ms=0
                        )
                        
            except Exception as e:
                logger.debug(f"AgentScope: Failed to record LLM call: {e}")
            
            return result
            
        except Exception as e:
            # Update agent loop step to error
            if loop_step:
                loop_step.status = Status.ERROR
                loop_step.content += f"\n✗ Error: {str(e)[:100]}"
            
            # Record failed call
            latency_ms = (time.time() - start_time) * 1000
            try:
                from ..monitor import get_current_trace
                if get_current_trace():
                    add_llm_call(
                        prompt="Agent loop",
                        completion=f"Error: {str(e)}",
                        tokens_input=0,
                        tokens_output=0,
                        latency_ms=latency_ms
                    )
            except:
                pass
            raise
    
    agent_loop_class._run_agent_loop = monitored_run_agent_loop
    logger.info("AgentScope: AgentLoop._run_agent_loop instrumented")


def instrument():
    """Instrument nanobot classes with AgentScope monitoring."""
    global _instrumented
    
    if _instrumented:
        logger.debug("AgentScope: Already instrumented")
        return
    
    try:
        from nanobot.agent.loop import AgentLoop
        from nanobot.agent.context import ContextBuilder
        
        _instrument_context_builder(ContextBuilder)
        _instrument_agent_loop(AgentLoop)
        
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
