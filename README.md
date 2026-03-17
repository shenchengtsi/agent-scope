# AgentScope 🔭

> **"让 Agent 的每一次思考，都清晰可见"**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)

AgentScope 是一个**轻量级、框架无关**的 Agent 可观测性平台，帮助开发者调试和优化 AI Agent 系统。

![AgentScope Demo](./docs/images/demo.png)

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔍 **执行链可视化** | 清晰展示 LLM 调用、工具执行、思考过程的完整链路 |
| 📊 **性能监控** | Token 用量、延迟、成功率等关键指标 |
| 🔧 **框架无关** | 支持 LangChain、AutoGen、CrewAI、自研框架等 |
| ⚡ **低开销** | 基于 ContextVar 的上下文传递，性能损耗 < 1% |
| 🛡️ **故障隔离** | 监控失败不影响主业务流程 |
| 💻 **实时调试** | WebSocket 实时推送执行状态 |

---

## 🚀 快速开始

### 1. 启动后端

```bash
# 克隆仓库
git clone https://github.com/yourname/agentscope.git
cd agentscope

# 安装依赖
pip install -r backend/requirements.txt

# 启动后端
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm start
```

打开 http://localhost:3001 查看监控界面。

### 3. 集成到 Agent 项目

```bash
pip install agentscope
```

```python
from agentscope import init_monitor, trace_scope, add_llm_call, add_tool_call
import time

# 初始化
init_monitor("http://localhost:8000")

# 包装 Agent 执行
async def my_agent(user_input):
    with trace_scope("my_agent", input_query=user_input):
        
        # LLM 调用
        start = time.time()
        response = await llm.chat.completions.create(...)
        add_llm_call(
            prompt=user_input,
            completion=response.choices[0].message.content,
            tokens_input=response.usage.prompt_tokens,
            tokens_output=response.usage.completion_tokens,
            latency_ms=(time.time() - start) * 1000,
        )
        
        # 工具调用
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

---

## 📖 文档

- [架构设计](./docs/architecture.md) - AgentScope 的核心设计思想
- [集成指南](./docs/integration-guide.md) - 详细集成教程
- [API 参考](./docs/api-reference.md) - SDK API 文档
- [示例代码](./examples/) - 各框架集成示例

---

## 🏗️ 架构设计

### 方案三：Context Manager + Context Propagation

AgentScope 采用**深度集成但低侵入**的设计理念：

```
┌─────────────────────────────────────────────────────────┐
│  Agent Framework (LangChain/AutoGen/nanobot/...)        │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Trace Scope (Context Manager)                   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │    │
│  │  │LLM Call │→ │Tool Call│→ │LLM Call │         │    │
│  │  └─────────┘  └─────────┘  └─────────┘         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  AgentScope Backend (FastAPI + WebSocket)               │
│  - REST API for trace collection                        │
│  - WebSocket for real-time updates                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Web UI (React + D3.js)                                │
│  - Execution chain visualization                        │
│  - Performance metrics dashboard                        │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| **SDK** | Python 3.8+ | 追踪数据收集和发送 |
| **Backend** | FastAPI, SQLite | 数据存储和查询 |
| **Frontend** | React, D3.js | 可视化和交互 |

---

## 🔌 框架支持

| 框架 | 集成方式 | 状态 |
|------|---------|------|
| **nanobot** | 侵入式埋点 | ✅ 已验证 |
| **LangChain** | Callback Handler | 📝 文档待补充 |
| **AutoGen** | 继承 Agent 类 | 📝 文档待补充 |
| **CrewAI** | 装饰器模式 | 📝 文档待补充 |
| **OpenAI Agents SDK** | 自动包装 | 📝 文档待补充 |
| **自研框架** | SDK 直接调用 | ✅ 支持 |

---

## 📊 监控能力

### 执行链追踪

```
Trace: agent_session (abc123)
├── Step 1: [input] "查询北京天气"
├── Step 2: [thinking] "用户需要天气信息"
├── Step 3: [llm_call] Model: gpt-4, Tokens: 150/80, Latency: 850ms
├── Step 4: [tool_call] Tool: weather_api, Args: {"city": "北京"}, Latency: 120ms
├── Step 5: [llm_call] Model: gpt-4, Tokens: 200/150, Latency: 920ms
└── Step 6: [output] "北京今天晴天，25°C"
```

### 性能指标

- **Token 用量**：输入/输出 Token 数、总成本估算
- **延迟分析**：LLM 调用延迟、工具执行延迟、端到端延迟
- **成功率**：LLM 调用成功率、工具执行成功率
- **迭代次数**：Agent 循环迭代次数

---

## 🛠️ 高级用法

### 自动仪器化

```python
from agentscope import instrument_llm, instrumented_tool
import openai

# 自动包装 OpenAI 客户端
client = instrument_llm(openai.OpenAI())

# 所有调用自动追踪
with trace_scope("auto_traced"):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )

# 装饰器方式追踪工具
@instrumented_tool
def search(query: str) -> str:
    return requests.get(f"https://api.example.com?q={query}").text

with trace_scope("agent"):
    result = search("python")  # 自动追踪
```

### 采样率控制

```python
import random

# 生产环境只监控 10% 请求
SAMPLE_RATE = 0.1

async def process_message(user_input):
    if random.random() <= SAMPLE_RATE:
        with trace_scope("sampled_trace", ...):
            return await agent.run(user_input)
    else:
        return await agent.run(user_input)
```

### 自定义元数据

```python
with trace_scope(
    name="customer_support",
    input_query=user_question,
    tags=["production", "support"],
    metadata={
        "user_id": user_id,
        "session_id": session_id,
        "version": "1.2.3",
    }
):
    result = await agent.handle(user_question)
```

---

## 🧪 开发

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm start
```

### 运行测试

```bash
cd sdk
pip install -e ".[dev]"
pytest tests/
```

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 🙏 致谢

- 架构设计灵感来自 [OpenTelemetry](https://opentelemetry.io/) 和 [LangSmith](https://smith.langchain.com/)
- 前端可视化参考 [Jaeger UI](https://www.jaegertracing.io/)

---

<div align="center">

**[Documentation](https://agentscope.readthedocs.io/)** •
**[Examples](./examples)** •
**[Report Bug](https://github.com/yourname/agentscope/issues)** •
**[Request Feature](https://github.com/yourname/agentscope/issues)**

</div>
