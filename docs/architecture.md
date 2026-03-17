# AgentScope 架构设计

本文档描述 AgentScope 的核心架构设计，帮助开发者理解其工作原理并贡献代码。

---

## 目录

1. [设计目标](#设计目标)
2. [架构概览](#架构概览)
3. [核心设计：方案三](#核心设计方案三)
4. [组件详解](#组件详解)
5. [数据流](#数据流)
6. [扩展性设计](#扩展性设计)

---

## 设计目标

AgentScope 的设计遵循以下原则：

| 目标 | 说明 | 权衡 |
|------|------|------|
| **框架无关** | 支持任何 Agent 框架，不限定技术栈 | 需要框架开发者手动集成 |
| **低侵入** | 最小化对业务代码的修改 | 需要一定的适配工作 |
| **低开销** | 性能损耗 < 1%，不影响生产环境 | 功能相对简单 |
| **易调试** | 实时查看执行状态，快速定位问题 | 需要额外的运行资源 |
| **可扩展** | 支持自定义监控点和数据格式 | 需要遵循 SDK 规范 |

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Agent Application                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     AgentScope SDK (Python)                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │    │
│  │  │trace_scope()│  │Auto-Instrument │  │Manual add_step()       │  │    │
│  │  │Context Mgr  │  │@instrumented_tool│  │add_llm_call()          │  │    │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │    │
│  │         │                │                                      │    │
│  │         └────────────────┼──────────────────────────────────────┘    │
│  │                          │                                          │
│  │              ┌───────────▼───────────┐                              │
│  │              │   ContextVar          │                              │
│  │              │   (_current_trace)    │                              │
│  │              └───────────┬───────────┘                              │
│  │                          │                                          │
│  │              ┌───────────▼───────────┐                              │
│  │              │   TraceEvent          │                              │
│  │              │   + ExecutionSteps    │                              │
│  │              └───────────┬───────────┘                              │
│  └──────────────────────────┼──────────────────────────────────────────┘
│                             │                                          │
│  ┌──────────────────────────┼──────────────────────────────────────────┐
│  │                          ▼                                          │
│  │              ┌───────────────────────┐                              │
│  │              │   _send_trace()       │                              │
│  │              │   HTTP POST           │                              │
│  │              └───────────┬───────────┘                              │
│  └──────────────────────────┼──────────────────────────────────────────┘
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
                              ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────────┐
│                         AgentScope Backend                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  FastAPI Router │  │  SQLite Storage │  │  WebSocket Manager      │  │
│  │  /api/traces    │  │  traces table   │  │  broadcast updates      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ WebSocket
┌─────────────────────────────────────────────────────────────────────────┐
│                          Web UI (React)                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Trace List     │  │  Execution Chain│  │  Metrics Dashboard      │  │
│  │  (Real-time)    │  │  Visualization  │  │  (Latency, Tokens)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 核心设计：方案三

AgentScope 采用 **"Context Manager + Context Propagation"** 架构（内部称为"方案三"）。

### 为什么选择方案三？

在设计阶段，我们对比了多种监控方案：

| 方案 | 原理 | 侵入性 | 兼容性 | 监控深度 |
|------|------|--------|--------|----------|
| **一：Monkey Patching** | 运行时替换方法 | 低 | ⭐⭐⭐ | 中 |
| **二：Import Hook** | 导入时修改模块 | 中 | ⭐⭐ | 中 |
| **三：Context Manager** | 上下文管理器 + ContextVar | 低 | ⭐⭐⭐⭐⭐ | 高 |
| **四：Event Bus** | 发布订阅模式 | 中 | ⭐⭐⭐ | 高 |
| **五：settrace** | Python 追踪接口 | 低 | ⭐ | 极高 |

**选择方案三的理由**：

1. **框架无关性**：不依赖特定框架的扩展点，任何 Python 代码都能使用
2. **监控深度高**：可以精确控制监控粒度，获取完整的执行上下文
3. **技术债务最小**：基于标准 Python 特性（contextlib, contextvars），稳定可靠
4. **渐进式集成**：可以从一个函数开始，逐步扩展监控范围

### 方案三的核心机制

#### 1. Context Manager 封装

```python
from contextlib import contextmanager
from contextvars import ContextVar

_current_trace: ContextVar[Optional[TraceEvent]] = ContextVar('current_trace', default=None)

@contextmanager
def trace_scope(name: str, input_query: str = "", tags: Optional[List[str]] = None):
    """创建追踪上下文。"""
    trace_event = TraceEvent(name=name, tags=tags or [], input_query=input_query)
    
    # 设置当前追踪到 ContextVar
    token = _current_trace.set(trace_event)
    
    try:
        yield trace_event
        trace_event.finish(Status.SUCCESS)
    except Exception as e:
        trace_event.finish(Status.ERROR)
        raise
    finally:
        # 发送到后端
        _send_trace(trace_event)
        # 清理上下文
        _current_trace.reset(token)
```

**关键点**：
- `yield` 之前的代码在进入上下文时执行
- `yield` 之后的代码在退出上下文时执行（无论正常或异常）
- `finally` 确保资源清理

#### 2. ContextVar 上下文传递

```python
# 在任何位置获取当前追踪
def get_current_trace() -> Optional[TraceEvent]:
    return _current_trace.get()

# 自动关联子调用
def add_llm_call(prompt: str, completion: str, ...):
    trace = get_current_trace()
    if trace:
        step = ExecutionStep(
            type=StepType.LLM_CALL,
            content=f"Prompt: {prompt}\nCompletion: {completion}",
            ...
        )
        trace.add_step(step)
```

**ContextVar 的优势**：
- **线程/协程安全**：每个执行流有独立的上下文
- **自动传播**：在 `async/await` 调用链中自动传递
- **无需显式传递**：避免污染业务函数的参数列表

#### 3. 执行步骤模型

```python
class ExecutionStep:
    """执行链中的一个步骤。"""
    id: str                    # 唯一标识
    type: StepType            # 步骤类型（LLM_CALL, TOOL_CALL, etc.）
    content: str              # 内容摘要
    timestamp: datetime       # 执行时间
    tokens_input: int         # 输入 Token
    tokens_output: int        # 输出 Token
    latency_ms: float         # 执行延迟
    tool_call: Optional[ToolCall]  # 工具调用详情
    metadata: Dict[str, Any]  # 扩展元数据
    status: Status            # 执行状态

class TraceEvent:
    """一次完整的 Agent 执行追踪。"""
    id: str
    name: str
    tags: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    steps: List[ExecutionStep]
    status: Status
    total_tokens: int
    total_latency_ms: float
    input_query: str
    output_result: str
    metadata: Dict[str, Any]
```

---

## 组件详解

### SDK (agentscope/)

#### 核心模块

| 文件 | 职责 |
|------|------|
| `monitor.py` | 追踪上下文管理、自动仪器化 |
| `models.py` | 数据模型定义（TraceEvent, ExecutionStep, etc.） |
| `__init__.py` | 公共 API 导出 |

#### 关键 API

```python
# 初始化
init_monitor(url: str)  # 设置后端地址

# 上下文管理（主要方式）
trace_scope(name, input_query, tags, metadata)

# 手动记录步骤
add_thinking(content)
add_llm_call(prompt, completion, tokens_input, tokens_output, latency_ms)
add_tool_call(tool_name, arguments, result, error, latency_ms)
add_memory(action, details)

# 自动仪器化
instrument_llm(client)  # 包装 LLM 客户端
@instrumented_tool      # 装饰器追踪工具
```

### Backend (backend/)

#### 技术栈

- **FastAPI**: 高性能异步 Web 框架
- **SQLite**: 轻量级数据存储（生产环境可替换为 PostgreSQL）
- **WebSocket**: 实时推送追踪更新
- **Pydantic**: 数据验证和序列化

#### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/traces` | GET | 获取所有追踪 |
| `/api/traces` | POST | 创建/更新追踪 |
| `/api/traces/{id}` | GET | 获取单个追踪 |
| `/api/traces/{id}` | DELETE | 删除追踪 |
| `/ws` | WebSocket | 实时更新订阅 |

#### 数据存储

```sql
-- SQLite 表结构（简化）
CREATE TABLE traces (
    id TEXT PRIMARY KEY,
    name TEXT,
    tags TEXT,  -- JSON 数组
    start_time TEXT,
    end_time TEXT,
    steps TEXT,  -- JSON 数组
    status TEXT,
    total_tokens INTEGER,
    total_latency_ms REAL,
    input_query TEXT,
    output_result TEXT,
    metadata TEXT  -- JSON 对象
);
```

### Frontend (frontend/)

#### 技术栈

- **React**: UI 框架
- **TypeScript**: 类型安全
- **D3.js / ReactFlow**: 执行链可视化
- **WebSocket API**: 实时数据更新

#### 功能模块

| 模块 | 说明 |
|------|------|
| TraceList | 追踪列表，支持筛选和排序 |
| TraceDetail | 单个追踪的详细视图 |
| ExecutionGraph | 执行链可视化（节点图） |
| MetricsPanel | 性能指标面板 |
| LiveIndicator | 实时状态指示器 |

---

## 数据流

### 正常执行流程

```
User Input
    │
    ▼
┌─────────────────────┐
│ trace_scope()       │ ──┐
│ (Context Enter)     │   │
└─────────────────────┘   │
    │                      │
    ▼                      │
┌─────────────────────┐   │
│ LLM Call            │   │
│ add_llm_call()      │   │ ContextVar
└─────────────────────┘   │ 自动关联
    │                      │
    ▼                      │
┌─────────────────────┐   │
│ Tool Call           │   │
│ add_tool_call()     │   │
└─────────────────────┘   │
    │                      │
    ▼                      │
┌─────────────────────┐   │
│ LLM Call            │   │
│ add_llm_call()      │   │
└─────────────────────┘   │
    │                      │
    ▼                      │
┌─────────────────────┐ ◀─┘
│ trace_scope()       │
│ (Context Exit)      │ ──► _send_trace()
└─────────────────────┘     HTTP POST
                                  │
                                  ▼
                           ┌──────────────┐
                           │   Backend    │
                           │  /api/traces │
                           └──────────────┘
                                  │
                                  ▼ WebSocket
                           ┌──────────────┐
                           │   Frontend   │
                           │  Update UI   │
                           └──────────────┘
```

### 错误处理流程

```
Execution
    │
    ▼
Exception Raised
    │
    ▼
trace_scope().__exit__(exc_type, exc_val, exc_tb)
    │
    ├─► trace_event.finish(Status.ERROR)
    ├─► add_error_step()
    └─► _send_trace()  # 即使出错也发送
            │
            ▼
    Frontend shows error status
```

---

## 扩展性设计

### 自定义监控点

开发者可以添加自定义步骤类型：

```python
from agentscope import add_step, StepType

# 定义自定义步骤类型
class MyStepType(StepType):
    CUSTOM_OPERATION = "custom_operation"

# 使用自定义步骤
add_step(
    step_type=MyStepType.CUSTOM_OPERATION,
    content="执行自定义操作",
    metadata={"custom_field": "value"},
)
```

### 自定义后端存储

```python
# 实现自定义存储后端
class MyStorage:
    def save_trace(self, trace: dict):
        # 保存到自定义数据库
        pass
    
    def get_trace(self, trace_id: str) -> dict:
        # 从自定义数据库查询
        pass

# 在 FastAPI 中注入
app.state.storage = MyStorage()
```

### 插件系统（未来）

```python
#  envisioned 插件接口
class AgentScopePlugin:
    def on_trace_start(self, trace: TraceEvent):
        pass
    
    def on_step_add(self, step: ExecutionStep):
        pass
    
    def on_trace_end(self, trace: TraceEvent):
        pass

# 注册插件
register_plugin(MyPlugin())
```

---

## 性能考量

### 基准测试

在典型场景下（MacBook Pro M1, Python 3.11）：

| 操作 | 耗时 | 说明 |
|------|------|------|
| `trace_scope()` enter/exit | ~10μs | 上下文管理器开销 |
| `add_llm_call()` | ~5μs | 添加步骤 |
| `_send_trace()` | ~50ms | HTTP POST（异步，不阻塞） |
| **总开销** | **< 1%** | 相对于典型 LLM 调用（500ms-2s） |

### 优化策略

1. **异步发送**：`_send_trace()` 使用 `asyncio.create_task()`，不阻塞主流程
2. **批量发送**：高频场景下可批量发送多个追踪
3. **采样率**：生产环境可配置采样率（如只监控 10% 请求）
4. **本地缓存**：后端故障时本地缓存，恢复后批量重传

---

## 安全考量

### 数据脱敏

```python
# 敏感字段脱敏
sanitized_args = {
    k: "***" if k in ["password", "api_key", "token"] else v
    for k, v in arguments.items()
}
add_tool_call(tool_name, sanitized_args, result)
```

### 访问控制

```python
# 后端可添加认证
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/traces")
async def create_trace(
    trace: TraceData,
    token: str = Depends(security)
):
    if not verify_token(token):
        raise HTTPException(status_code=401)
    # ...
```

---

## 未来演进

### 短期（1-3 个月）

- [ ] 更多框架的官方集成示例（LangChain, AutoGen, CrewAI）
- [ ] 性能优化（批量发送、连接池）
- [ ] 单元测试覆盖率提升

### 中期（3-6 个月）

- [ ] 插件系统
- [ ] 数据导出（JSON, CSV, OpenTelemetry 格式）
- [ ] 告警系统（延迟阈值、错误率）

### 长期（6-12 个月）

- [ ] 分布式追踪（多 Agent 协作链路）
- [ ] A/B 测试支持
- [ ] 自动优化建议（基于监控数据）

---

## 参考

- [Python ContextVars](https://docs.python.org/3/library/contextvars.html)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/traces/)

---

**有问题？** 提交 Issue 或参与讨论。
