# 🎯 AgentScope

> *"让 Agent 的每一次思考，都清晰可见"*

AgentScope 是一个轻量级、框架无关的 **Agent 调试与可观测性平台**。只需一个 `@trace` 装饰器，即可让你的 Agent 执行过程完全可视化。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)

## ✨ 特性

- **🔍 执行链可视化** - 完整的 Agent 执行流程，每一步都清晰可见
- **🛠️ 工具调用追踪** - 自动捕获工具调用、参数、返回值和错误
- **📊 性能监控** - Token 消耗、延迟指标实时展示
- **🔌 框架无关** - 支持任意 Python Agent，LangChain/AutoGen/CrewAI 等
- **⚡ 零侵入** - 一个装饰器即可接入，无需改造代码
- **🚀 实时更新** - WebSocket 推送，执行过程即时可见

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/shenchengtsi/agent-scope.git
cd agent-scope

# 2. 一键启动
docker-compose up -d

# 3. 打开浏览器
open http://localhost:8080
```

### 方式二：手动安装

**1. 安装后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**2. 安装前端**
```bash
cd frontend
npm install
npm start
```

**3. 安装 Python SDK**
```bash
cd sdk
pip install -e .
```

## 📖 使用示例

```python
from agentscope import trace, init_monitor
from openai import OpenAI

# 初始化监控
init_monitor("http://localhost:8000")

client = OpenAI()

@trace(name="my_agent", tags=["production"])
def my_agent(query: str):
    """你的 Agent 逻辑"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query}]
    )
    return response.choices[0].message.content

# 运行 Agent，自动在 Web UI 中可见
result = my_agent("什么是量子计算？")
```

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Web UI)                    │
│         React + TypeScript + D3.js / ReactFlow          │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Backend (API Server)                 │
│              FastAPI + WebSocket + SQLite               │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                 Agent Instrumentation SDK               │
│              Python / TypeScript / Go                   │
│    无侵入式装饰器/SDK，支持 LangChain、AutoGen、          │
│    CrewAI、OpenAI Agents SDK 等主流框架                  │
└─────────────────────────────────────────────────────────┘
```

## 🛣️ Roadmap

- [x] 核心执行链可视化
- [x] Python SDK (@trace 装饰器)
- [x] FastAPI 后端 + WebSocket
- [x] React 前端 MVP
- [ ] 工具调用沙盒
- [ ] 记忆透视仪 (Memory Inspector)
- [ ] 多 Agent 协作地图
- [ ] 性能基准测试
- [ ] 团队协作功能

## 🤝 贡献

欢迎 Issue 和 PR！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 📄 License

[MIT License](./LICENSE)