"""Non-intrusive instrumentation for nanobot using monkey patching."""

import functools
import time
import os
from typing import Any, Optional

from loguru import logger

from ..monitor import init_monitor, trace_scope, add_step
from ..models import StepType, Status


_instrumented = False


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
    
    # Wrap _process_message to create trace context and capture output
    original_process_message = agent_loop_class._process_message
    
    @functools.wraps(original_process_message)
    async def monitored_process_message(self, msg, session_key=None, on_progress=None):
        # Skip system channels
        if hasattr(msg, 'channel') and msg.channel in ("system", "inter_agent"):
            return await original_process_message(self, msg, session_key, on_progress)
        
        # Create trace context
        with trace_scope(
            name="nanobot_message",
            input_query=getattr(msg, 'content', '')[:500],
            tags=["nanobot", getattr(msg, 'channel', 'unknown')]
        ) as trace:
            # Execute and capture result
            result = await original_process_message(self, msg, session_key, on_progress)
            
            # Add output step if we have a result
            if result and hasattr(result, 'content'):
                # Record output step
                add_step(StepType.OUTPUT, result.content[:1000] if result.content else "")
            
            return result
    
    agent_loop_class._process_message = monitored_process_message
    
    logger.info("AgentScope: AgentLoop instrumented")


def instrument():
    """Instrument nanobot classes with AgentScope monitoring."""
    global _instrumented
    
    if _instrumented:
        logger.debug("AgentScope: Already instrumented")
        return
    
    try:
        from nanobot.agent.loop import AgentLoop
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
