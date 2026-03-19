"""Non-intrusive instrumentation for nanobot using monkey patching."""

import functools
import time
import os
from typing import Any, Optional

from loguru import logger

from ..monitor import (
    init_monitor, trace_scope, add_step, add_llm_call, add_tool_call,
    add_prompt_build_step, add_tool_selection_step
)
from ..models import StepType, Status


# Get backend URL from environment or use default
AGENTSCOPE_BACKEND_URL = os.getenv("AGENTSCOPE_BACKEND_URL", "http://localhost:8000")


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
            
            # Note: Skills loading is already accurately recorded by nanobot's native
            # monitoring in load_skills_for_context(). We don't record it here because
            # list_skills() returns ALL available skills (e.g., 17), not the ACTUALLY
            # loaded skills for this request (e.g., 2).
            
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
            init_monitor(AGENTSCOPE_BACKEND_URL)
            logger.info("AgentScope: Non-intrusive monitoring enabled")
        except Exception as e:
            logger.debug(f"AgentScope: Failed to initialize: {e}")
        
        return await original_run(self)
    
    agent_loop_class.run = monitored_run
    
    # Wrap _process_message to create trace context
    original_process_message = agent_loop_class._process_message
    
    @functools.wraps(original_process_message)
    async def monitored_process_message(self, msg, session_key=None, on_progress=None):
        # Skip system channels
        if hasattr(msg, 'channel') and msg.channel in ("system", "inter_agent"):
            return await original_process_message(self, msg, session_key, on_progress)
        
        # Extract user info for better trace naming
        user_id = getattr(msg, 'user_id', 'unknown')
        channel = getattr(msg, 'channel', 'unknown')
        
        # Create trace context
        with trace_scope(
            name=f"nanobot:{channel}",
            input_query=getattr(msg, 'content', '')[:1000],
            tags=["nanobot", channel, f"user:{user_id}"]
        ) as trace:
            # Execute and capture result
            result = await original_process_message(self, msg, session_key, on_progress)
            
            # Add output step if we have a result
            if result:
                output_content = ""
                if hasattr(result, 'content') and result.content:
                    output_content = result.content[:1000]
                elif hasattr(result, 'text') and result.text:
                    output_content = result.text[:1000]
                else:
                    output_content = str(result)[:1000]
                
                add_step(StepType.OUTPUT, output_content)
            
            return result
    
    agent_loop_class._process_message = monitored_process_message
    
    # Instrument LLM provider calls
    _instrument_provider_calls(agent_loop_class)
    
    logger.info("AgentScope: AgentLoop instrumented")


def _instrument_provider_calls(agent_loop_class):
    """Instrument LLM provider calls."""
    original_run_agent_loop = agent_loop_class._run_agent_loop
    
    @functools.wraps(original_run_agent_loop)
    async def monitored_run_agent_loop(self, initial_messages, on_progress=None):
        start_time = time.time()
        
        # Record tool selection once at the start
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
                    
                    if available_tools:
                        add_tool_selection_step(
                            selected_tool="(available)",
                            available_tools=available_tools,
                            reason=f"{len(available_tools)} tools available"
                        )
        except Exception as e:
            logger.debug(f"AgentScope: Failed to record tools: {e}")
        
        try:
            # Execute the loop
            result = await original_run_agent_loop(self, initial_messages, on_progress=on_progress)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            final_content, tools_used, all_msgs = result
            
            # Record LLM calls summary
            try:
                # Count tokens roughly
                tokens_in = sum(len(str(m.get('content', ''))) // 4 for m in initial_messages)
                tokens_out = len(str(final_content)) // 4 if final_content else 0
                
                add_llm_call(
                    prompt=f"Agent loop with {len(initial_messages)} messages",
                    completion=final_content[:200] if final_content else "",
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    latency_ms=latency_ms
                )
                
                # Record unique tool calls
                if tools_used:
                    recorded_tools = set()
                    for tool_name in tools_used:
                        if tool_name not in recorded_tools:
                            recorded_tools.add(tool_name)
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
            # Record failed call
            latency_ms = (time.time() - start_time) * 1000
            try:
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
