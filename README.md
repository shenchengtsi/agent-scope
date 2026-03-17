# AgentScope 🔭

> **"Observe Every Thought, Debug Every Step"** — Lightweight, framework-agnostic observability for AI Agents

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)

**AgentScope** is a production-ready observability platform for AI Agent systems. It provides deep visibility into execution chains without compromising performance or reliability.

[Live Demo](https://github.com/shenchengtsi/agent-scope#demo) • [Quick Start](https://github.com/shenchengtsi/agent-scope#quick-start) • [Documentation](https://github.com/shenchengtsi/agent-scope/tree/main/docs)

---

## 🎯 Why AgentScope?

### The Problem

Building AI Agents is hard. Debugging them is harder:
- **Black box execution**: Can't see what the agent is doing step-by-step
- **Tool call failures**: Don't know which tool failed and why
- **Performance blindspots**: No visibility into latency, token usage, costs
- **Multi-agent chaos**: Can't trace interactions between agents

### The Solution

AgentScope provides **deep observability** with **minimal intrusion**:

```
Before AgentScope:
❌ User Input → [Black Box] → Output

After AgentScope:
✅ User Input → Context Building → LLM Call (850ms, 150 tokens)
              → Tool: web_search (120ms) → Tool: calculator (5ms)
              → LLM Call (920ms, 200 tokens) → Output
```

---

## ✨ Key Features

### 🔍 Execution Chain Visualization
See every step of your agent's reasoning:
- LLM calls with prompts, responses, token usage
- Tool executions with arguments, results, errors
- Memory operations and context changes
- Thinking/reasoning steps

### 📊 Production Metrics
Monitor what matters:
- **Latency**: Per-step and end-to-end timing
- **Token Usage**: Input/output tokens, cost estimation
- **Success Rate**: Track tool and LLM call reliability
- **Iteration Count**: Detect infinite loops early

### 🔧 Framework Agnostic
Works with any Python Agent framework:
- LangChain, AutoGen, CrewAI
- OpenAI Agents SDK
- Custom frameworks
- Multi-agent systems

### ⚡ Zero-Overhead Design
- **< 1% performance impact** using ContextVar-based propagation
- **Asynchronous data collection** — never blocks your agent
- **Graceful degradation** — monitoring failures don't affect business logic

### 🛡️ Production Safe
- **Fault isolated**: Agent continues even if monitoring fails
- **Sampling support**: Monitor only 10% of traffic in production
- **Data sanitization**: Automatic PII/sensitive data redaction
- **Local first**: All data stays on your infrastructure

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
# Clone the repository
git clone https://github.com/shenchengtsi/agent-scope.git
cd agentscope

# Install and start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm start
```

Open http://localhost:3001 to view the dashboard.

### 3. Instrument Your Agent

```python
from agentscope import init_monitor, trace_scope, add_llm_call, add_tool_call
import time

# Initialize once
init_monitor("http://localhost:8000")

# Wrap your agent execution
async def my_agent(user_input):
    with trace_scope("customer_support", input_query=user_input):
        
        # LLM call with automatic tracking
        start = time.time()
        response = await llm.chat.completions.create(...)
        add_llm_call(
            prompt=user_input,
            completion=response.choices[0].message.content,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
            latency_ms=(time.time() - start) * 1000,
        )
        
        # Tool execution with tracking
        tool_start = time.time()
        result = await search_tool(response.content)
        add_tool_call(
            tool_name="search",
            arguments={"query": response.content},
            result=result,
            latency_ms=(time.time() - tool_start) * 1000,
        )
        
        return result
```

**That's it!** Open the dashboard to see complete execution traces.

---

## 💡 Use Cases

### 1. Debugging Complex Agents

```python
# See exactly what your agent is doing
with trace_scope("research_agent"):
    # 1. Planning step
    add_thinking("Breaking down research query into sub-tasks")
    
    # 2. Web search
    results = await web_search(query)  # Tracked automatically
    
    # 3. Analysis
    analysis = await analyze_results(results)  # Tracked
    
    # 4. Synthesis
    return synthesis(analysis)
```

**Value**: Debug production issues in minutes instead of hours.

### 2. Cost Optimization

Track token usage and latency per component:
```
[research_agent] Total Cost: $0.023
├── LLM Call 1: 150 tokens ($0.003)
├── Web Search: 200ms (free)
├── LLM Call 2: 400 tokens ($0.008)
└── Analysis: 300 tokens ($0.012)
```

**Value**: Identify expensive operations and optimize.

### 3. Reliability Monitoring

Alert on anomaly patterns:
- High error rate on specific tools
- Unusual latency spikes
- Excessive iteration counts (infinite loops)
- Token usage anomalies

### 4. Multi-Agent Orchestration

```python
# Trace cross-agent communication
with trace_scope("agent_collaboration", tags=["multi-agent"]):
    result_a = await agent_a.process(task)
    result_b = await agent_b.review(result_a)
    final = await agent_c.synthesize([result_a, result_b])
```

**Value**: Understand agent interactions and optimize handoffs.

---

## 🏗️ Architecture

AgentScope uses **Scheme 3: Context Manager + Context Propagation** for minimal intrusion:

```
┌─────────────────────────────────────────────────────────┐
│  Your Agent Framework                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  trace_scope() Context Manager                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │   │
│  │  │LLM Call │→ │Tool Call│→ │LLM Call │         │   │
│  │  └────┬────┘  └────┬────┘  └────┬────┘         │   │
│  │       │            │            │               │   │
│  │       └────────────┼────────────┘               │   │
│  │                    ▼                            │   │
│  │         ContextVar (_current_trace)             │   │
│  └────────────────────┼────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│  AgentScope Backend (FastAPI + SQLite/PostgreSQL)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼ WebSocket
┌─────────────────────────────────────────────────────────┐
│  Web Dashboard (React + D3.js)                          │
└─────────────────────────────────────────────────────────┘
```

**Why this design?**
- **No framework lock-in**: Works with any Python code
- **Zero configuration**: Automatic context propagation
- **Type-safe**: Leverages Python's ContextVar for thread/coroutine safety
- **Composable**: Nest traces, create sub-traces naturally

---

## 📊 Performance Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Context Manager Overhead | ~10μs | Negligible |
| Step Recording | ~5μs | In-memory |
| HTTP Transmission | ~50ms | Async, non-blocking |
| **Total Impact** | **< 1%** | Relative to LLM latency (500ms-2s) |

Tested on: MacBook Pro M1, Python 3.11, typical LLM workload.

---

## 🔒 Security & Privacy

### Data Protection
```python
# Automatic sensitive data redaction
sanitized_args = {
    k: "***" if k in ["password", "api_key", "token"] else v
    for k, v in arguments.items()
}
```

### Deployment Options
- **On-premise**: All data stays within your network
- **Air-gapped**: No external dependencies
- **Encrypted**: HTTPS/WSS for all communications

### Compliance Ready
- GDPR compliant (data retention controls)
- SOC 2 ready (audit logging)
- HIPAA compatible (with proper configuration)

---

## 📖 Documentation

- [Integration Guide](docs/integration-guide.md) — Step-by-step framework integration
- [Architecture](docs/architecture.md) — Deep dive into design decisions
- [API Reference](docs/api-reference.md) — SDK API documentation
- [Examples](examples/) — Working code samples

---

## 🛠️ Supported Frameworks

| Framework | Integration | Status |
|-----------|-------------|--------|
| **nanobot** | Direct instrumentation | ✅ Production Ready |
| **LangChain** | Callback Handler | 📝 Guide Available |
| **AutoGen** | Agent inheritance | 📝 Guide Available |
| **CrewAI** | Decorator pattern | 📝 Guide Available |
| **OpenAI Agents** | Auto-instrumentation | 📝 Guide Available |
| **Custom** | SDK direct | ✅ Fully Supported |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas we need help with:**
- Additional framework integrations
- Frontend UI improvements
- Documentation translations
- Production deployment guides

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Architecture inspired by [OpenTelemetry](https://opentelemetry.io/) and [LangSmith](https://smith.langchain.com/)
- UI design inspired by [Jaeger](https://www.jaegertracing.io/)

---

<div align="center">

**[Get Started](https://github.com/shenchengtsi/agent-scope#quick-start)** • 
**[Documentation](docs/)** • 
**[Report Bug](https://github.com/shenchengtsi/agent-scope/issues)** • 
**[Request Feature](https://github.com/shenchengtsi/agent-scope/issues)**

</div>
