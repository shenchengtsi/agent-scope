# AgentScope 框架集成指南

## 架构设计

### 核心原则

AgentScope 采用**核心通用 + 框架适配**的分层架构：

```
agent-scope/
├── agentscope/
│   ├── core/                    # 核心功能（完全通用）
│   │   ├── models.py           # 数据模型（Trace, Step, etc.）
│   │   ├── monitor.py          # 监控客户端
│   │   └── storage.py          # 数据存储
│   │
│   ├── instrumentation/         # 框架适配层
│   │   ├── base.py             # 适配器基类
│   │   ├── nanobot.py          # Nanobot 适配器 ✅ 已有
│   │   ├── langchain.py        # LangChain 适配器（待开发）
│   │   ├── autogen.py          # AutoGen 适配器（待开发）
│   │   └── ...                 # 其他框架
│   │
│   └── sdk/                     # 用户 SDK（完全通用）
│       ├── __init__.py
│       └── trace.py
│
└── docs/
    ├── FRAMEWORK_INTEGRATION_GUIDE.md  # 本文档
    └── adapters/
        ├── NANOBOT.md
        ├── LANGCHAIN.md
        └── AUTOGEN.md
```

### 为什么采用适配器模式？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **为每个框架做适配** | 用户体验好，开箱即用 | 维护成本高 |
| **完全通用** | 维护成本低 | 用户需要手动集成，门槛高 |
| **适配器模式（推荐）** | 平衡：核心通用 + 框架定制 | 适中 |

## 适配器开发流程

### Step 1: 分析目标框架

以 LangChain 为例：

```python
# 1. 研究框架的扩展点
# LangChain 提供：
# - Callbacks（回调系统）
# - Custom LLM wrappers
# - Tool decorators

# 2. 确定监控埋点位置
# - Chain.start() / Chain.end()
# - LLM.generate()
# - Tool.run()
```

### Step 2: 实现适配器

```python
# agentscope/instrumentation/langchain.py
"""LangChain adapter for AgentScope."""

from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult, AgentAction, AgentFinish

from ..core.monitor import trace_scope, add_llm_call, add_tool_call, add_thinking


class AgentScopeCallback(BaseCallbackHandler):
    """LangChain callback for AgentScope monitoring."""
    
    def __init__(self):
        self._current_trace = None
        self._llm_start_time = None
        self._tool_start_time = None
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Start trace when chain begins."""
        self._current_trace = trace_scope(
            name=serialized.get("name", "langchain_chain"),
            input_query=str(inputs)[:500],
            tags=["langchain"]
        ).__enter__()
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """End trace when chain finishes."""
        if self._current_trace:
            self._current_trace.__exit__(None, None, None)
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Record LLM start."""
        self._llm_start_time = time.time()
        add_thinking(f"LLM call: {len(prompts)} prompts")
    
    def on_llm_end(self, response: LLMResult, **kwargs):
        """Record LLM end."""
        latency = (time.time() - self._llm_start_time) * 1000
        
        for gen in response.generations:
            add_llm_call(
                prompt="",
                completion=gen[0].text[:500] if gen else "",
                tokens_input=response.llm_output.get('token_usage', {}).get('prompt_tokens', 0),
                tokens_output=response.llm_output.get('token_usage', {}).get('completion_tokens', 0),
                latency_ms=latency
            )
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Record tool start."""
        self._tool_start_time = time.time()
    
    def on_tool_end(self, output: str, **kwargs):
        """Record tool end."""
        latency = (time.time() - self._tool_start_time) * 1000
        add_tool_call(
            tool_name=kwargs.get('name', 'unknown'),
            arguments={},
            result=output[:500],
            latency_ms=latency
        )


def instrument_langchain():
    """Enable AgentScope monitoring for LangChain."""
    # 可以在这里自动注入全局配置
    # 或者返回 callback 让用户手动添加
    return AgentScopeCallback()
```

### Step 3: 编写用户使用文档

```markdown
# LangChain + AgentScope 使用指南

## 安装

```bash
pip install agentscope[langchain]
```

## 使用方式 A: 回调方式（推荐）

```python
from langchain import OpenAI, LLMChain, PromptTemplate
from agentscope.instrumentation.langchain import AgentScopeCallback

# 创建回调
agentscope_callback = AgentScopeCallback()

# 在 Chain 中使用
llm = OpenAI()
template = PromptTemplate(template="Hello {name}!")
chain = LLMChain(llm=llm, prompt=template, callbacks=[agentscope_callback])

# 运行（自动监控）
result = chain.run(name="World")
```

## 使用方式 B: 全局自动注入

```python
from agentscope.instrumentation.langchain import instrument_langchain

# 一行代码启用监控
instrument_langchain()

# 之后所有的 LangChain 操作都会被监控
```
```

### Step 4: 提供集成示例

```python
# examples/langchain_example.py
"""Example: LangChain + AgentScope integration."""

import os
from langchain import OpenAI, LLMChain, PromptTemplate
from agentscope.instrumentation.langchain import AgentScopeCallback

# Initialize AgentScope backend
# (Make sure backend is running on http://localhost:8000)

# Create LangChain components
llm = OpenAI(temperature=0.7)
prompt = PromptTemplate(
    input_variables=["topic"],
    template="Write a poem about {topic}."
)

# Create chain with AgentScope monitoring
callback = AgentScopeCallback()
chain = LLMChain(llm=llm, prompt=prompt, callbacks=[callback])

# Run chain (monitored automatically)
result = chain.run(topic="AI")
print(result)

# View traces at http://localhost:3000
```

## 框架适配矩阵

| 框架 | 适配难度 | 状态 | 扩展点 | 预估工作量 |
|------|---------|------|--------|-----------|
| **Nanobot** | ⭐ 低 | ✅ 已完成 | Direct class patching | 2 天 |
| **LangChain** | ⭐⭐ 中 | 📝 待开发 | Callback system | 3 天 |
| **AutoGen** | ⭐⭐ 中 | 📝 待开发 | Agent hooks | 3 天 |
| **LlamaIndex** | ⭐⭐ 中 | 📝 待开发 | Callbacks | 3 天 |
| **CrewAI** | ⭐⭐⭐ 高 | 📝 待开发 | Limited hooks | 5 天 |
| **Semantic Kernel** | ⭐⭐⭐ 高 | 📝 待开发 | .NET/Python diff | 5 天 |

## 适配器开发最佳实践

### 1. 统一接口设计

```python
# agentscope/instrumentation/base.py
"""Base adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseAdapter(ABC):
    """Base class for framework adapters."""
    
    framework_name: str = "unknown"
    
    @abstractmethod
    def instrument(self) -> None:
        """Enable monitoring for the framework."""
        pass
    
    @abstractmethod
    def uninstrument(self) -> None:
        """Disable monitoring for the framework."""
        pass
    
    def is_available(self) -> bool:
        """Check if the framework is installed."""
        try:
            __import__(self.framework_name)
            return True
        except ImportError:
            return False
```

### 2. 优雅降级

```python
def instrument_langchain():
    """Enable monitoring with graceful fallback."""
    try:
        import langchain
    except ImportError:
        logger.warning("LangChain not installed, skipping instrumentation")
        return None
    
    try:
        # Try to instrument
        return _do_instrument()
    except Exception as e:
        logger.error(f"Failed to instrument LangChain: {e}")
        # Don't break user's application
        return None
```

### 3. 版本兼容性

```python
# 检查框架版本
def check_langchain_version():
    import langchain
    version = langchain.__version__
    
    if version.startswith("0.1"):
        return "legacy"
    elif version.startswith("0.2"):
        return "current"
    else:
        logger.warning(f"Untested LangChain version: {version}")
        return "unknown"

# 根据版本使用不同的适配逻辑
def instrument():
    version_type = check_langchain_version()
    
    if version_type == "legacy":
        return LegacyAdapter()
    else:
        return CurrentAdapter()
```

## 社区贡献指南

### 如何贡献新的框架适配器

1. **Fork 仓库**
2. **创建适配器文件**
   ```bash
   touch agentscope/instrumentation/{framework_name}.py
   ```
3. **实现适配器**（参考现有模板）
4. **添加测试**
   ```bash
   touch tests/instrumentation/test_{framework_name}.py
   ```
5. **编写文档**
   ```bash
   touch docs/adapters/{FRAMEWORK_NAME}.md
   ```
6. **提交 PR**

### 适配器模板

```python
# agentscope/instrumentation/TEMPLATE.py
"""Template for new framework adapter.

Copy this file and replace:
- FRAMEWORK_NAME: Name of the framework
- Hook points: Where to inject monitoring
- Data mapping: How to convert framework data to AgentScope format
"""

import time
import functools
from typing import Any, Optional

from ..core.monitor import (
    trace_scope,
    add_llm_call,
    add_tool_call,
    add_thinking,
)
from ..utils.logger import logger


FRAMEWORK_NAME = "example_framework"


def _instrument_class(target_class, method_name, wrapper):
    """Helper to instrument a class method."""
    original = getattr(target_class, method_name)
    setattr(target_class, method_name, wrapper(original))


def instrument():
    """Enable AgentScope monitoring for FRAMEWORK_NAME."""
    try:
        import FRAMEWORK_NAME
    except ImportError:
        logger.warning(f"{FRAMEWORK_NAME} not installed")
        return False
    
    logger.info(f"Instrumenting {FRAMEWORK_NAME}")
    
    # TODO: Implement framework-specific instrumentation
    # Example:
    # _instrument_class(AgentClass, 'run', _wrap_agent_run)
    
    return True


def uninstrument():
    """Disable monitoring (if possible)."""
    logger.warning(f"Uninstrumenting {FRAMEWORK_NAME} requires restart")
    pass
```

## 长期策略

### 阶段 1: 核心框架覆盖（当前）
- ✅ Nanobot
- 📝 LangChain（计划 Q2）
- 📝 AutoGen（计划 Q2）

### 阶段 2: 主流框架覆盖（6个月内）
- LlamaIndex
- CrewAI
- Haystack
- Flowise

### 阶段 3: 社区驱动（长期）
- 提供完善的 Adapter SDK
- 社区贡献适配器
- 定期发布适配器市场

## 结论

**是的，为每个框架做适配是必要的**，但：

1. **核心代码复用**：80% 的代码在核心层，框架适配只占 20%
2. **渐进式开发**：优先支持主流框架，小众框架社区贡献
3. **标准化流程**：建立适配器模板和开发指南，降低门槛
4. **用户体验**：开箱即用，降低用户集成成本

这种模式类似于:
- **OpenTelemetry**：为核心库，各语言/框架有独立 SDK
- **Prometheus**：提供 client libraries 给各语言

AgentScope 定位为：
> "AI Agent 的 OpenTelemetry"
