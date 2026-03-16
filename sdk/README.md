# AgentScope SDK

Python SDK for AgentScope - Agent debugging and observability platform.

## Installation

```bash
pip install agentscope
```

## Quick Start

```python
from agentscope import trace, init_monitor

# Initialize monitoring
init_monitor("http://localhost:8000")

@trace(name="my_agent")
def my_agent(query: str):
    # Your agent logic here
    return f"Result for: {query}"

# Run your agent
result = my_agent("What is AI?")
```

## Features

- **Zero-intrusion**: Just add `@trace` decorator
- **Real-time monitoring**: WebSocket-based live updates
- **Execution tracing**: Full chain of thought visualization
- **Tool call tracking**: Debug function calling issues
- **Token & latency metrics**: Performance monitoring