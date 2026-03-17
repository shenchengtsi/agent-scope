# AgentScope 框架集成指南

> **"让 Agent 的每一次思考，都清晰可见"**

本文档指导如何在各种 Agent 框架中集成 AgentScope，实现执行链的可观测性。

---

## 📖 目录

1. [架构概述](#架构概述)
2. [集成方式选择](#集成方式选择)
3. [侵入式埋点指南](#侵入式埋点指南)
4. [框架特定集成](#框架特定集成)
5. [最佳实践](#最佳实践)
6. [故障排除](#故障排除)

---

## 架构概述

### 方案三：Context Manager + Context Propagation

AgentScope 采用**深度集成但低侵入**的设计理念：

```
┌─────────────────────────────────────────────────────────┐
│  Agent 框架 (LangChain/AutoGen/nanobot/...)             │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Trace Scope (上下文管理器)                      │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │    │
│  │  │LLM Call │→ │Tool Call│→ │LLM Call │         │    │
│  │  └─────────┘  └─────────┘  └─────────┘         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  AgentScope Backend (FastAPI + WebSocket)               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Web UI (React + D3.js)                                │
└─────────────────────────────────────────────────────────┘
```

### 核心概念

| 概念 | 说明 | 代码示例 |
|------|------|---------|
| `trace_scope()` | 创建追踪上下文 | `with trace_scope("my_agent"):` |
| ContextVar | 隐式传递追踪状态 | 自动关联子调用 |
| 执行步骤 | LLM、工具、思考、错误 | `add_llm_call()`, `add_tool_call()` |

---

## 集成方式选择

### 方式一：侵入式埋点（推荐）

在框架源代码关键位置插入监控代码。

**优点**：
- 稳定可靠，与框架版本解耦
- 监控粒度精细，可获取内部状态
- 性能开销最小

**缺点**：
- 需要修改框架源码
- 升级框架时需重新应用补丁

### 方式二：Monkey Patching（备选）

运行时动态替换方法。

**优点**：
- 零侵入，不修改源码

**缺点**：
- 脆弱，易在框架升级后失效
- 难以获取内部状态

---

## 侵入式埋点指南

### 步骤 1：安装 AgentScope SDK

```bash
pip install agentscope
```

### 步骤 2：初始化监控

在框架启动时执行一次：

```python
from agentscope import init_monitor

# 启动时初始化
init_monitor("http://localhost:8000")  # AgentScope 后端地址
```

### 步骤 3：埋点位置详解

#### 3.1 消息/请求入口（必需）

在 Agent 接收用户输入的入口函数：

```python
from agentscope import trace_scope, add_thinking

async def process_message(user_input: str, session_id: str = None):
    """处理用户消息的入口函数。"""
    
    # 创建追踪上下文
    with trace_scope(
        name="agent_session",                    # 追踪名称
        input_query=user_input[:1000],           # 用户输入
        tags=["agent", "production"],            # 分类标签
        metadata={"session_id": session_id}      # 附加元数据
    ):
        add_thinking("开始构建上下文...")
        
        # 原有的业务逻辑
        context = await build_context(user_input)
        result = await agent.run(context)
        
        return result
```

**效果**：创建完整的追踪记录，所有子调用自动关联。

---

#### 3.2 LLM 调用点（推荐）

在调用大模型 API 的位置：

```python
from agentscope import add_llm_call, add_thinking
import time

async def call_llm(messages, tools=None, model=None):
    """包装 LLM 调用，添加监控。"""
    
    # 记录思考过程（可选）
    add_thinking(f"准备调用 {model}，消息数: {len(messages)}")
    
    start_time = time.time()
    
    try:
        # 原有的 LLM 调用
        response = await llm_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )
        
        # 计算延迟
        latency_ms = (time.time() - start_time) * 1000
        
        # 提取 Token 用量
        tokens_in = response.usage.prompt_tokens if response.usage else 0
        tokens_out = response.usage.completion_tokens if response.usage else 0
        
        # 提取响应内容
        content = response.choices[0].message.content if response.choices else ""
        
        # 记录 LLM 调用
        add_llm_call(
            prompt=str(messages)[:500],           # 输入提示词预览
            completion=content[:500],              # 输出内容预览
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=latency_ms,
        )
        
        return response
        
    except Exception as e:
        # 记录错误
        latency_ms = (time.time() - start_time) * 1000
        add_llm_call(
            prompt=str(messages)[:500],
            completion=f"Error: {str(e)}",
            latency_ms=latency_ms,
        )
        raise
```

**字段说明**：
- `tokens_input/output`: Token 用量，用于成本分析
- `latency_ms`: 延迟，用于性能优化
- `prompt/completion`: 内容预览，用于调试

---

#### 3.3 工具执行点（推荐）

在调用工具/函数的位置：

```python
from agentscope import add_tool_call
import time

async def execute_tool(tool_name: str, arguments: dict):
    """执行工具并记录。"""
    
    start_time = time.time()
    
    try:
        # 原有的工具执行
        result = await tool_registry.execute(tool_name, arguments)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # 记录工具调用
        add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            latency_ms=latency_ms,
        )
        
        return result
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=None,
            error=str(e),
            latency_ms=latency_ms,
        )
        raise
```

---

#### 3.4 Skill/技能触发点（可选）

```python
from agentscope import add_thinking

def trigger_skill(skill_name: str, context: dict):
    """触发技能时记录。"""
    
    add_thinking(f"Skill triggered: {skill_name}\nContext: {context}")
    
    # 原有的技能执行
    return skill_registry.run(skill_name, context)
```

---

#### 3.5 记忆操作点（可选）

```python
from agentscope import add_memory

def save_to_memory(key: str, value: any):
    """保存记忆时记录。"""
    
    add_memory("save", f"Key: {key}, Value: {str(value)[:100]}")
    
    # 原有的保存操作
    memory.store(key, value)

def load_from_memory(key: str):
    """加载记忆时记录。"""
    
    add_memory("load", f"Key: {key}")
    
    return memory.retrieve(key)
```

---

## 框架特定集成

### nanobot 集成（完整示例）

#### 修改文件：`nanobot/agent/loop.py`

```python
# 1. 导入 AgentScope
from nanobot.agent.monitoring import (
    init_monitor,
    trace_scope,
    add_thinking,
    add_llm_call,
    add_tool_call,
    _AGENTSCOPE_AVAILABLE,
)

# 2. 在 AgentLoop 类中修改 _run_agent_loop 方法
async def _run_agent_loop(self, initial_messages, ...):
    """运行 Agent 迭代循环，带 AgentScope 监控。"""
    
    messages = initial_messages
    iteration = 0
    
    while iteration < self.max_iterations:
        iteration += 1
        
        tool_defs = self.tools.get_definitions()
        
        # ===== AgentScope: 记录 LLM 调用 =====
        import time
        llm_start = time.time()
        
        response = await self.provider.chat_with_retry(
            messages=messages,
            tools=tool_defs,
            model=self.model,
        )
        
        llm_latency = (time.time() - llm_start) * 1000
        
        if _AGENTSCOPE_AVAILABLE:
            add_llm_call(
                prompt=f"Messages: {len(messages)}",
                completion=response.content[:200] if not response.has_tool_calls else "[Tool calls requested]",
                tokens_input=response.usage.prompt_tokens if response.usage else 0,
                tokens_output=response.usage.completion_tokens if response.usage else 0,
                latency_ms=llm_latency,
            )
        # ====================================
        
        if response.has_tool_calls:
            # 处理工具调用
            for tool_call in response.tool_calls:
                
                # ===== AgentScope: 记录工具执行 =====
                tool_start = time.time()
                
                try:
                    result = await self.tools.execute(
                        tool_call.name, 
                        tool_call.arguments
                    )
                    
                    tool_latency = (time.time() - tool_start) * 1000
                    
                    if _AGENTSCOPE_AVAILABLE:
                        add_tool_call(
                            tool_name=tool_call.name,
                            arguments=tool_call.arguments,
                            result=str(result)[:500],
                            latency_ms=tool_latency,
                        )
                        
                except Exception as e:
                    tool_latency = (time.time() - tool_start) * 1000
                    
                    if _AGENTSCOPE_AVAILABLE:
                        add_tool_call(
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
            # 最终回复
            return response.content
```

#### 修改文件：`nanobot/agent/monitoring.py`

```python
"""AgentScope monitoring integration for nanobot."""

from agentscope import (
    init_monitor,
    trace_scope,
    get_current_trace,
    add_step,
    add_llm_call,
    add_tool_call,
    add_thinking,
    add_memory,
)
from agentscope.models import StepType, Status

def add_llm_call_step(model, messages_count, tools_count, 
                      response_content, tool_calls, 
                      tokens_in=0, tokens_out=0, latency_ms=0):
    """Record LLM call step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    content = f"Model: {model}\n"
    content += f"Messages: {messages_count}, Tools: {tools_count}\n"
    
    if tool_calls:
        content += f"Tool calls: {len(tool_calls)}\n"
        for tc in tool_calls:
            content += f"  - {tc.get('name', 'unknown')}\n"
    
    if response_content:
        content += f"Response: {response_content[:200]}..."
    
    add_llm_call(
        prompt=f"Messages: {messages_count}",
        completion=content,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=latency_ms,
    )

def add_tool_execution_step(tool_name, arguments, result, 
                           error=None, latency_ms=0):
    """Record tool execution step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    add_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        error=error,
        latency_ms=latency_ms,
    )
```

---

### LangChain 集成思路

```python
from langchain.callbacks.base import BaseCallbackHandler
from agentscope import trace_scope, add_llm_call, add_tool_call

class AgentScopeCallback(BaseCallbackHandler):
    """LangChain 回调集成。"""
    
    def __init__(self):
        self.trace = None
        
    def on_chain_start(self, serialized, inputs, **kwargs):
        """链开始时创建追踪。"""
        self.trace = trace_scope(
            name="langchain_run",
            input_query=str(inputs)[:500]
        )
        self.trace.__enter__()
    
    def on_chain_end(self, outputs, **kwargs):
        """链结束时关闭追踪。"""
        if self.trace:
            self.trace.__exit__(None, None, None)
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.llm_start = time.time()
    
    def on_llm_end(self, response, **kwargs):
        latency = (time.time() - self.llm_start) * 1000
        add_llm_call(
            prompt=str(prompts),
            completion=response.generations[0][0].text,
            latency_ms=latency,
        )
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tool_start = time.time()
        self.tool_name = serialized.get("name", "unknown")
    
    def on_tool_end(self, output, **kwargs):
        latency = (time.time() - self.tool_start) * 1000
        add_tool_call(
            tool_name=self.tool_name,
            arguments={},
            result=str(output),
            latency_ms=latency,
        )

# 使用
from langchain import OpenAI, LLMChain

llm = OpenAI()
chain = LLMChain(llm=llm, prompt=prompt, callbacks=[AgentScopeCallback()])
```

---

### AutoGen 集成思路

```python
from autogen import ConversableAgent
from agentscope import trace_scope, add_llm_call, add_tool_call

class AgentScopeAgent(ConversableAgent):
    """带 AgentScope 监控的 AutoGen Agent。"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_trace = None
    
    def initiate_chat(self, recipient, message, ...):
        """重写以添加追踪。"""
        with trace_scope(
            name=f"autogen_{self.name}_to_{recipient.name}",
            input_query=message
        ):
            return super().initiate_chat(recipient, message, ...)
    
    def _generate_reply(self, messages, ...):
        """重写以监控 LLM 调用。"""
        start = time.time()
        
        reply = super()._generate_reply(messages, ...)
        
        latency = (time.time() - start) * 1000
        add_llm_call(
            prompt=str(messages),
            completion=str(reply),
            latency_ms=latency,
        )
        
        return reply
```

---

## 最佳实践

### 1. 渐进式集成

不要一次性添加所有监控点：

```
Phase 1: 只埋入口点（trace_scope）
    └── 可看到基本输入输出

Phase 2: 增加 LLM 调用监控
    └── 可看到模型选择和延迟

Phase 3: 增加工具执行监控
    └── 可看到完整执行链

Phase 4: 增加 Skill/Memory 监控
    └── 可看到完整 Agent 思考过程
```

### 2. 防御式编程

监控代码不应影响主流程：

```python
# ✅ 正确：try-except 包裹
if _AGENTSCOPE_AVAILABLE:
    try:
        add_llm_call(...)
    except Exception:
        pass  # 静默失败

# ❌ 错误：未处理异常
add_llm_call(...)  # 如果失败会影响主流程
```

### 3. 采样率控制（生产环境）

```python
import random

SAMPLE_RATE = 0.1  # 只监控 10% 的请求

async def process_message(user_input):
    if random.random() > SAMPLE_RATE:
        # 不监控，直接执行
        return await agent.run(user_input)
    
    # 监控执行
    with trace_scope(...):
        return await agent.run(user_input)
```

### 4. 敏感信息脱敏

```python
# ✅ 正确：截断和脱敏
add_llm_call(
    prompt=user_input[:200] + "...",  # 截断
    completion=result[:200] + "...",
)

# 脱敏敏感字段
sanitized_args = {k: "***" if k in ["password", "token"] else v 
                  for k, v in arguments.items()}
```

### 5. 性能优化

```python
# 异步发送，不阻塞主流程
async def send_trace_async(trace):
    asyncio.create_task(async_send(trace))

# 批量发送（高频场景）
batch_traces = []
if len(batch_traces) >= 10:
    send_batch(batch_traces)
    batch_traces = []
```

---

## 故障排除

### 问题 1：追踪数据未发送到后端

**检查清单**：
```python
# 1. 检查初始化
init_monitor("http://localhost:8000")

# 2. 检查后端健康
curl http://localhost:8000/api/health

# 3. 检查网络连通
python -c "import requests; requests.post('http://localhost:8000/api/traces', json={...})"
```

### 问题 2：执行步骤未关联到追踪

**原因**：ContextVar 未正确传递。

**解决**：确保所有异步调用在同一个上下文：
```python
# ✅ 正确：使用 await 保持上下文
async with trace_scope(...):
    result = await async_operation()  # 上下文保持

# ❌ 错误：创建新任务丢失上下文
async with trace_scope(...):
    asyncio.create_task(async_operation())  # 上下文丢失
```

### 问题 3：延迟数据不准确

**原因**：异步 I/O 的 time.time() 包含等待时间。

**解决**：使用 asyncio 的专用计时：
```python
import asyncio

start = asyncio.get_event_loop().time()
result = await operation()
latency = (asyncio.get_event_loop().time() - start) * 1000
```

---

## 参考

- [AgentScope 架构设计](./architecture.md)
- [SDK API 文档](./api-reference.md)
- [示例代码](../examples/)

---

**有问题？** 提交 Issue 或加入讨论：
- GitHub Issues: https://github.com/yourname/agentscope/issues
- Discussions: https://github.com/yourname/agentscope/discussions
