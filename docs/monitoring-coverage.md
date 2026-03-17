# AgentScope Monitoring Coverage Guide

Complete guide to all monitoring capabilities available in AgentScope.

---

## Overview

AgentScope provides comprehensive observability for AI Agent systems across 11 major categories:

| Category | Purpose | Business Value |
|----------|---------|----------------|
| **LLM Calls** | Track model invocations | Cost optimization, latency analysis |
| **Tools** | Monitor tool executions | Debug failures, track performance |
| **Skills** | Track skill loading | Understand capability usage |
| **Memory** | Record memory operations | Optimize context management |
| **Prompt Building** | Monitor prompt assembly | Context window optimization |
| **Context Window** | Track context management | Prevent token overflow |
| **Retry Logic** | Record retry attempts | Reliability analysis |
| **Rate Limit** | Monitor API throttling | Capacity planning |
| **Session Lifecycle** | Track session events | User behavior analysis |
| **Inter-Agent** | Monitor cross-agent calls | Multi-agent debugging |

---

## Quick Reference

### 1. LLM Call Monitoring

```python
from agentscope import add_llm_call

add_llm_call(
    prompt="User query here",
    completion="Model response",
    tokens_input=150,
    tokens_output=80,
    latency_ms=850.5,
)
```

**Records:**
- Model name and version
- Input/output token counts
- Latency (request to response)
- Prompt and completion preview (truncated)

---

### 2. Tool Execution Monitoring

```python
from agentscope import add_tool_call

add_tool_call(
    tool_name="web_search",
    arguments={"query": "python tutorial"},
    result="Search results...",
    latency_ms=120.0,
)
```

**Records:**
- Tool name and arguments
- Execution result or error
- Latency
- Success/failure status

---

### 3. Skill Loading Monitoring

```python
from nanobot.agent.monitoring import add_skill_loading_step

add_skill_loading_step(
    skills=["github", "weather", "web_search"],
    loaded_count=3,
    failed_count=0,
    total_time_ms=45.2,
)
```

**Records:**
- Requested skills list
- Success/failure counts
- Loading time

---

### 4. Memory Operation Monitoring

```python
from agentscope import add_memory

add_memory("consolidate", "Session: abc123, Tokens: 15000 -> 8000")
```

**Records:**
- Memory action type
- Details and metrics

---

### 5. Prompt Building Monitoring

```python
from nanobot.agent.monitoring import add_prompt_building_step

add_prompt_building_step(
    system_prompt="You are a helpful assistant...",
    history_count=10,
    context_length=5000,
    max_context=128000,
)
```

**Records:**
- System prompt size
- History message count
- Context usage percentage
- Warnings for high usage (>80%)

---

### 6. Context Window Management

```python
from nanobot.agent.monitoring import add_context_window_step

add_context_window_step(
    operation="consolidate",
    original_count=50,
    new_count=30,
    reason="Token limit: 15000/16000",
)
```

**Records:**
- Operation type (truncate, consolidate, archive)
- Message count before/after
- Reason for operation

---

### 7. Retry Logic Monitoring

```python
from nanobot.agent.monitoring import add_retry_step

add_retry_step(
    attempt=2,
    max_attempts=3,
    error_type="rate_limit",
    delay=1.5,
    will_retry=True,
)
```

**Records:**
- Current attempt number
- Error type
- Delay before retry
- Whether retry will occur

---

### 8. Rate Limit Monitoring

```python
from nanobot.agent.monitoring import add_rate_limit_step

add_rate_limit_step(
    limit_type="requests",
    current_usage=95,
    limit=100,
    wait_time=2.5,
)
```

**Records:**
- Limit type (requests, tokens, etc.)
- Usage percentage
- Throttle wait time

---

### 9. Session Lifecycle

```python
from nanobot.agent.monitoring import add_session_lifecycle_step

add_session_lifecycle_step(
    event="created",  # created, loaded, saved, archived
    session_key="feishu:ou_123",
    details="New conversation started",
)
```

**Records:**
- Session key
- Event type
- Message count
- Metadata

---

### 10. Inter-Agent Communication

```python
from nanobot.agent.monitoring import traced_call

# Automatically monitored via traced_call wrapper
result = traced_call(
    url="http://localhost:18806",
    json_data={"message": "Hello", "from_instance": "zhuzaihou"},
)
```

**Records:**
- Source and target instances
- Message content
- Response time
- Success/failure

---

## Integration Examples

### Complete Agent Instrumentation

```python
from agentscope import trace_scope, add_thinking
from nanobot.agent.monitoring import (
    add_llm_call_step,
    add_tool_execution_step,
    add_prompt_building_step,
    add_context_window_step,
)

async def process_request(user_input):
    with trace_scope("agent_execution", input_query=user_input):
        # 1. Session lifecycle (automatic)
        
        # 2. Skill loading (in skills.py)
        skills = load_skills(["github", "weather"])
        
        # 3. Prompt building (in context.py)
        messages = build_messages(history, user_input, skills)
        
        # 4. Context window check (in memory.py)
        if token_count > threshold:
            consolidate_messages(session)
        
        # 5. LLM call (in providers/base.py)
        response = await llm.chat.completions.create(...)
        
        # 6. Tool execution (in loop.py)
        for tool_call in response.tool_calls:
            result = await execute_tool(tool_call)
        
        # 7. Final response
        return response.content
```

---

## Dashboard Views

### Execution Chain View

```
Trace: customer_support_session
├── [00:00:00] Session created: feishu:ou_123
├── [00:00:05] Skills loaded: github, weather (3ms)
├── [00:00:05] Prompt built: 1500/128000 chars (1.2%)
├── [00:00:06] LLM Call: gpt-4 (850ms, 150/80 tokens)
├── [00:00:07] Tool: weather_api (120ms) ✅
├── [00:00:08] LLM Call: gpt-4 (920ms, 200/150 tokens)
└── [00:00:10] Session saved: 12 messages
```

### Metrics Dashboard

| Metric | Current | Average | Peak |
|--------|---------|---------|------|
| LLM Latency (p95) | 920ms | 850ms | 2500ms |
| Tool Success Rate | 98.5% | 97.2% | - |
| Context Usage | 12% | 25% | 89% |
| Retry Rate | 0.5% | 1.2% | 5% |

---

## Best Practices

### 1. Gradual Rollout

```python
# Phase 1: Core (LLM + Tools)
# Phase 2: Context (Prompt + Window)
# Phase 3: Reliability (Retry + Rate Limit)
# Phase 4: Analytics (Session + Skills)
```

### 2. Sampling in Production

```python
import random

SAMPLE_RATE = 0.1  # 10% of requests

if random.random() < SAMPLE_RATE:
    with trace_scope("monitored"):
        return await agent.process(input)
else:
    return await agent.process(input)
```

### 3. Sensitive Data Redaction

```python
def sanitize(args: dict) -> dict:
    return {
        k: "***" if k in ["password", "token"] else v
        for k, v in args.items()
    }

add_tool_call(tool_name, sanitize(arguments), result)
```

---

## Troubleshooting

### Missing Monitoring Data

1. Check `_AGENTSCOPE_AVAILABLE` is True
2. Verify `init_monitor()` called
3. Ensure backend running on correct port
4. Check for exceptions in logs

### High Memory Usage

- Enable sampling
- Reduce trace retention
- Use external database (PostgreSQL)

---

## API Reference

See [SDK API Documentation](./api-reference.md) for complete function signatures.

---

**Questions?** Open an issue on GitHub.
