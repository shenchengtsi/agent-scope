# AgentScope Integration Guide

Complete guide for integrating AgentScope observability into your AI Agent framework.

---

## Table of Contents

1. [Integration Overview](#integration-overview)
2. [Integration Strategy](#integration-strategy)
3. [Instrumentation Points](#instrumentation-points)
4. [Framework-Specific Guides](#framework-specific-guides)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Integration Overview

### What Gets Monitored

AgentScope captures the complete execution lifecycle:

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  ENTRY POINT (trace_scope)                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Context Building                                │    │
│  │  add_thinking("Building context...")             │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │  LLM Call                                          │  │
│  │  add_llm_call(prompt, completion, tokens, latency) │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │  Tool Execution                                    │  │
│  │  add_tool_call(name, args, result, latency)        │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │  LLM Call (Response Synthesis)                     │  │
│  │  add_llm_call(...)                                 │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  └───────────────────────▼───────────────────────────┘  │
│                    OUTPUT (trace ends)                   │
└─────────────────────────────────────────────────────────┘
```

### Value Proposition

| Capability | Business Value |
|------------|----------------|
| Execution Visualization | Reduce debugging time by 80% |
| Token Monitoring | Cut API costs by 30-50% |
| Latency Tracking | Improve user experience |
| Error Detection | Increase system reliability |
| Audit Logging | Meet compliance requirements |

---

## Integration Strategy

### Choose Your Approach

#### Option 1: Direct Instrumentation (Recommended)

Modify your framework's source code to add monitoring hooks.

**Pros:**
- Most reliable and performant
- Full access to internal state
- Clean, maintainable code

**Cons:**
- Requires source code modification
- Need to re-apply after framework updates

**Best for:** Production systems, custom frameworks

#### Option 2: Monkey Patching (Quick Start)

Dynamically replace methods at runtime.

**Pros:**
- No source code changes
- Quick to implement

**Cons:**
- Fragile (breaks with framework updates)
- Limited access to internal state
- Harder to debug

**Best for:** Prototyping, frameworks you don't control

#### Option 3: Wrapper Classes

Create wrapper classes around framework components.

**Pros:**
- Clean separation of concerns
- Works with any framework

**Cons:**
- Requires changes to how you instantiate agents
- May miss some internal events

**Best for:** When you control agent instantiation

---

## Instrumentation Points

### Required: Entry Point

Wrap the main agent execution:

```python
from agentscope import trace_scope, add_thinking

async def process_request(user_input, session_id=None):
    """Main entry point for agent execution."""
    
    with trace_scope(
        name="agent_session",
        input_query=user_input[:1000],
        tags=["production", "customer_support"],
        metadata={
            "session_id": session_id,
            "user_tier": "premium",
            "version": "2.1.0",
        }
    ):
        add_thinking("Initializing agent context...")
        
        # Your existing agent logic
        result = await agent.run(user_input)
        
        return result
```

**Why this matters:** Creates the root trace that all subsequent steps attach to.

### Recommended: LLM Calls

Monitor every LLM invocation:

```python
from agentscope import add_llm_call
import time

async def call_llm(messages, model=None, tools=None):
    """Wrapped LLM call with monitoring."""
    
    start_time = time.time()
    
    try:
        response = await llm_client.chat.completions.create(
            model=model or "gpt-4",
            messages=messages,
            tools=tools,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract token usage
        tokens_in = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
        tokens_out = response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0
        
        # Record the call
        add_llm_call(
            prompt=str(messages)[:500],
            completion=response.choices[0].message.content[:500] if response.choices else "",
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=latency_ms,
        )
        
        return response
        
    except Exception as e:
        # Record failed call
        latency_ms = (time.time() - start_time) * 1000
        add_llm_call(
            prompt=str(messages)[:500],
            completion=f"Error: {str(e)}",
            latency_ms=latency_ms,
        )
        raise
```

**Value Metrics:**
- Token usage per call
- API cost tracking
- Latency percentiles (p50, p95, p99)
- Model performance comparison

### Recommended: Tool Executions

Track all tool/function calls:

```python
from agentscope import add_tool_call
import time

async def execute_tool(tool_name: str, arguments: dict):
    """Execute tool with monitoring."""
    
    start_time = time.time()
    
    try:
        # Execute the tool
        result = await tool_registry.execute(tool_name, arguments)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Record successful execution
        add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=str(result)[:500],  # Truncate long results
            latency_ms=latency_ms,
        )
        
        return result
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        # Record failed execution
        add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=None,
            error=str(e),
            latency_ms=latency_ms,
        )
        raise
```

**Business Value:**
- Identify slow tools
- Track tool success rates
- Debug tool argument issues
- Optimize tool selection

### Optional: Memory Operations

```python
from agentscope import add_memory

def save_memory(key: str, value: any):
    """Save to memory with tracking."""
    add_memory("save", f"Key: {key}, Value: {str(value)[:100]}")
    memory.store(key, value)

def load_memory(key: str):
    """Load from memory with tracking."""
    add_memory("load", f"Key: {key}")
    return memory.retrieve(key)
```

### Optional: Reasoning Steps

```python
from agentscope import add_thinking

# Record agent's reasoning process
add_thinking("Breaking down user query into sub-tasks")
add_thinking("Identifying relevant tools for task execution")
add_thinking("Synthesizing results from multiple sources")
```

---

## Framework-Specific Guides

### nanobot Integration

**Files to modify:**
- `nanobot/agent/loop.py` — Agent loop instrumentation
- `nanobot/agent/monitoring.py` — Monitoring utilities

**Step 1: Add monitoring utilities**

Create `nanobot/agent/monitoring.py`:

```python
"""AgentScope monitoring integration for nanobot."""

try:
    from agentscope import (
        init_monitor,
        trace_scope,
        add_llm_call,
        add_tool_call,
        add_thinking,
        add_memory,
    )
    from agentscope.models import TraceEvent, StepType, Status
    _AGENTSCOPE_AVAILABLE = True
except ImportError:
    _AGENTSCOPE_AVAILABLE = False
    # Define stubs
    def init_monitor(*args): pass
    def trace_scope(*args, **kwargs): 
        from contextlib import nullcontext
        return nullcontext()
    def add_llm_call(*args): pass
    def add_tool_call(*args): pass
    def add_thinking(*args): pass
    def add_memory(*args): pass

def add_llm_call_step(model, messages_count, tools_count,
                      response_content, tool_calls,
                      tokens_in=0, tokens_out=0, latency_ms=0):
    """Record LLM call with nanobot-specific formatting."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    content = f"Model: {model}\n"
    content += f"Messages: {messages_count}, Tools: {tools_count}\n"
    
    if tool_calls:
        content += f"Tool calls requested: {len(tool_calls)}\n"
        for tc in tool_calls:
            content += f"  - {tc.get('name', 'unknown')}\n"
    
    if response_content:
        content += f"Response: {response_content[:200]}"
    
    add_llm_call(
        prompt=f"Messages: {messages_count}",
        completion=content,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=latency_ms,
    )

def add_tool_execution_step(tool_name, arguments, result, 
                           error=None, latency_ms=0):
    """Record tool execution."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    add_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        result=str(result)[:500] if result else None,
        error=error,
        latency_ms=latency_ms,
    )
```

**Step 2: Instrument the agent loop**

Modify `nanobot/agent/loop.py`:

```python
from nanobot.agent.monitoring import (
    init_monitor,
    add_llm_call_step,
    add_tool_execution_step,
    _AGENTSCOPE_AVAILABLE,
)

class AgentLoop:
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Initialize AgentScope
        if _AGENTSCOPE_AVAILABLE:
            init_monitor("http://localhost:8000")
    
    async def _run_agent_loop(self, initial_messages, ...):
        """Agent loop with full monitoring."""
        messages = initial_messages
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            tool_defs = self.tools.get_definitions()
            
            # ===== MONITOR: LLM Call =====
            import time
            llm_start = time.time()
            
            response = await self.provider.chat_with_retry(
                messages=messages,
                tools=tool_defs,
                model=self.model,
            )
            
            llm_latency = (time.time() - llm_start) * 1000
            
            if _AGENTSCOPE_AVAILABLE:
                add_llm_call_step(
                    model=self.model,
                    messages_count=len(messages),
                    tools_count=len(tool_defs),
                    response_content=response.content if not response.has_tool_calls else None,
                    tool_calls=[{"name": tc.name, "args": tc.arguments} 
                               for tc in response.tool_calls] if response.has_tool_calls else [],
                    tokens_in=getattr(response.usage, 'prompt_tokens', 0) if response.usage else 0,
                    tokens_out=getattr(response.usage, 'completion_tokens', 0) if response.usage else 0,
                    latency_ms=llm_latency,
                )
            # =============================
            
            if response.has_tool_calls:
                # Process tool calls
                for tool_call in response.tool_calls:
                    
                    # ===== MONITOR: Tool Execution =====
                    tool_start = time.time()
                    
                    try:
                        result = await self.tools.execute(
                            tool_call.name, 
                            tool_call.arguments
                        )
                        
                        tool_latency = (time.time() - tool_start) * 1000
                        
                        if _AGENTSCOPE_AVAILABLE:
                            add_tool_execution_step(
                                tool_name=tool_call.name,
                                arguments=tool_call.arguments,
                                result=result,
                                latency_ms=tool_latency,
                            )
                            
                    except Exception as e:
                        tool_latency = (time.time() - tool_start) * 1000
                        
                        if _AGENTSCOPE_AVAILABLE:
                            add_tool_execution_step(
                                tool_name=tool_call.name,
                                arguments=tool_call.arguments,
                                result=None,
                                error=str(e),
                                latency_ms=tool_latency,
                            )
                        raise
                    # ====================================
                    
                    messages = self.context.add_tool_result(...)
            else:
                # Final response
                return response.content
```

### LangChain Integration

Use LangChain's callback system:

```python
from langchain.callbacks.base import BaseCallbackHandler
from agentscope import trace_scope, add_llm_call, add_tool_call

class AgentScopeCallback(BaseCallbackHandler):
    """LangChain callback for AgentScope integration."""
    
    def __init__(self):
        self.current_trace = None
        self.llm_start_time = None
        self.tool_start_time = None
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Start trace when chain begins."""
        self.current_trace = trace_scope(
            name=serialized.get("name", "langchain_chain"),
            input_query=str(inputs)[:500]
        )
        self.current_trace.__enter__()
    
    def on_chain_end(self, outputs, **kwargs):
        """End trace when chain completes."""
        if self.current_trace:
            self.current_trace.__exit__(None, None, None)
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Record LLM start time."""
        import time
        self.llm_start_time = time.time()
    
    def on_llm_end(self, response, **kwargs):
        """Record LLM completion."""
        import time
        latency = (time.time() - self.llm_start_time) * 1000
        
        add_llm_call(
            prompt=str(prompts)[:500],
            completion=response.generations[0][0].text[:500],
            latency_ms=latency,
        )
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Record tool start time."""
        import time
        self.tool_start_time = time.time()
        self.current_tool_name = serialized.get("name", "unknown")
    
    def on_tool_end(self, output, **kwargs):
        """Record tool completion."""
        import time
        latency = (time.time() - self.tool_start_time) * 1000
        
        add_tool_call(
            tool_name=self.current_tool_name,
            arguments={},
            result=str(output),
            latency_ms=latency,
        )

# Usage
from langchain import OpenAI, LLMChain

callback = AgentScopeCallback()
chain = LLMChain(
    llm=OpenAI(),
    prompt=prompt,
    callbacks=[callback]
)
```

---

## Production Deployment

### Sampling Strategy

Monitor only a percentage of traffic to reduce overhead:

```python
import random
import os

SAMPLE_RATE = float(os.getenv("AGENTSCOPE_SAMPLE_RATE", "1.0"))

async def process_request(user_input):
    if random.random() > SAMPLE_RATE:
        # Skip monitoring
        return await agent.run(user_input)
    
    # Monitor this request
    with trace_scope("monitored_request", ...):
        return await agent.run(user_input)
```

### Data Retention

Configure automatic cleanup:

```python
# In your backend configuration
TRACE_RETENTION_DAYS = 30

# Cron job to clean old traces
async def cleanup_old_traces():
    cutoff = datetime.now() - timedelta(days=TRACE_RETENTION_DAYS)
    # Delete traces older than cutoff
```

### Security Hardening

```python
# Sanitize sensitive data
def sanitize_arguments(args: dict) -> dict:
    sensitive_keys = ['password', 'token', 'api_key', 'secret', 'credit_card']
    return {
        k: '***REDACTED***' if any(s in k.lower() for s in sensitive_keys) else v
        for k, v in args.items()
    }

# Use in tool calls
add_tool_call(
    tool_name=tool_name,
    arguments=sanitize_arguments(arguments),
    result=result,
)
```

---

## Troubleshooting

### Issue: Traces not appearing in dashboard

**Checklist:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check `_AGENTSCOPE_AVAILABLE` is True
3. Verify `init_monitor()` was called with correct URL
4. Check browser console for WebSocket errors

### Issue: Steps not associating with trace

**Cause:** ContextVar not propagating through async calls.

**Solution:** Ensure all async calls use `await`, not `asyncio.create_task()`.

```python
# ✅ Correct: Context propagates
async with trace_scope(...):
    result = await async_operation()

# ❌ Incorrect: Context lost
async with trace_scope(...):
    asyncio.create_task(async_operation())  # Loses context
```

### Issue: High memory usage

**Cause:** Too many traces in memory.

**Solution:** Implement trace batching or sampling.

---

## Next Steps

- [Architecture Deep Dive](architecture.md)
- [API Reference](api-reference.md)
- [Examples](../examples/)

**Need help?** Open an issue on GitHub.
