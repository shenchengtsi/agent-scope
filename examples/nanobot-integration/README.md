# nanobot + AgentScope 集成示例

本示例展示如何在 nanobot 框架中集成 AgentScope，实现完整的执行链监控。

## 前置条件

- Python 3.8+
- 已安装 nanobot
- 已启动 AgentScope 后端 (localhost:8000)
- 已启动 AgentScope 前端 (localhost:3001)

## 集成步骤

### 步骤 1：修改 nanobot/agent/monitoring.py

```python
"""AgentScope monitoring integration for nanobot."""

import time
import json
from typing import Any, Optional, Dict, List
from contextvars import ContextVar

from loguru import logger

# AgentScope integration
try:
    from agentscope import (
        init_monitor,
        trace_scope,
        get_current_trace,
        add_step,
        add_llm_call,
        add_tool_call,
        add_thinking,
        add_memory,
        instrument_llm,
        instrumented_tool,
    )
    from agentscope.models import TraceEvent, ExecutionStep, StepType, Status, ToolCall
    from agentscope.monitor import set_current_trace as _set_trace, _send_trace
    _AGENTSCOPE_AVAILABLE = True
    _SCHEME3_AVAILABLE = True
    logger.info("AgentScope Scheme 3 monitoring available")
except ImportError as e:
    _AGENTSCOPE_AVAILABLE = False
    _SCHEME3_AVAILABLE = False
    logger.warning(f"AgentScope not available: {e}")
    # Define stubs
    TraceEvent = None
    ExecutionStep = None
    StepType = None
    Status = None
    ToolCall = None
    
    def init_monitor(*args, **kwargs): pass
    def get_current_trace(): return None
    def _set_trace(trace): pass
    def _send_trace(trace): pass
    def trace_scope(*args, **kwargs):
        from contextlib import nullcontext
        return nullcontext()
    def add_step(*args, **kwargs): pass
    def add_llm_call(*args, **kwargs): pass
    def add_tool_call(*args, **kwargs): pass
    def add_thinking(*args, **kwargs): pass
    def add_memory(*args, **kwargs): pass
    def instrument_llm(client): return client
    def instrumented_tool(func=None, **kwargs):
        if func: return func
        def decorator(f): return f
        return decorator

# Context management
_current_trace: ContextVar[Optional[TraceEvent]] = ContextVar('nanobot_trace', default=None)


def get_trace() -> Optional[TraceEvent]:
    """Get current trace from context."""
    if not _AGENTSCOPE_AVAILABLE:
        return None
    return get_current_trace()


def start_trace(name: str, tags: List[str], input_query: str) -> Optional[TraceEvent]:
    """Start a new trace (legacy API)."""
    if not _AGENTSCOPE_AVAILABLE:
        return None
    
    try:
        trace = TraceEvent(name=name, tags=tags)
        trace.input_query = input_query[:1000]
        _set_trace(trace)
        
        add_step(StepType.INPUT, input_query[:500])
        logger.debug(f"AgentScope: Started trace {trace.id} for {name}")
        return trace
    except Exception as e:
        logger.warning(f"AgentScope: Failed to start trace: {e}")
        return None


def finish_trace(trace: Optional[TraceEvent], output: Optional[str], error: Optional[Exception] = None):
    """Finish and send trace (legacy API)."""
    if not trace or not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        if error:
            add_step(StepType.ERROR, str(error)[:500], status=Status.ERROR)
            trace.finish(Status.ERROR)
        else:
            output_str = output[:1000] if output else ""
            trace.output_result = output_str
            add_step(StepType.OUTPUT, output_str[:500])
            trace.finish(Status.SUCCESS)
        
        _send_trace(trace)
    except Exception as e:
        logger.warning(f"AgentScope: Failed to finish trace: {e}")


def add_context_building_step(session_key: str, history_count: int, skills_used: List[str]):
    """Record context building step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        content = f"Building context for session {session_key[:20]}...\n"
        content += f"- History messages: {history_count}\n"
        content += f"- Skills loaded: {', '.join(skills_used) if skills_used else 'None'}"
        add_thinking(content)
    except Exception as e:
        logger.debug(f"AgentScope: Failed to add context step: {e}")


def add_llm_call_step(
    model: str,
    messages_count: int,
    tools_count: int,
    response_content: Optional[str],
    tool_calls: List[Dict],
    tokens_in: int = 0,
    tokens_out: int = 0,
    latency_ms: float = 0
):
    """Record LLM call step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        content = f"Model: {model}\n"
        content += f"Messages: {messages_count}, Tools: {tools_count}\n"
        
        if tool_calls:
            content += f"Tool calls requested: {len(tool_calls)}\n"
            for tc in tool_calls:
                content += f"  - {tc.get('name', 'unknown')}\n"
        
        if response_content:
            content += f"Response preview: {response_content[:200]}..."
        
        add_llm_call(
            prompt=f"Messages: {messages_count}",
            completion=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.debug(f"AgentScope: Failed to add LLM step: {e}")


def add_tool_execution_step(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any,
    error: Optional[str] = None,
    latency_ms: float = 0
):
    """Record tool execution step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            error=error,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.debug(f"AgentScope: Failed to add tool step: {e}")


def add_skill_trigger_step(skill_name: str, trigger_reason: str):
    """Record skill triggering."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        add_thinking(f"Skill triggered: {skill_name}\nReason: {trigger_reason}")
    except Exception as e:
        logger.debug(f"AgentScope: Failed to add skill step: {e}")


def add_memory_step(action: str, details: str):
    """Record memory operation."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    try:
        add_memory(action, details)
    except Exception as e:
        logger.debug(f"AgentScope: Failed to add memory step: {e}")


class TraceContext:
    """Context manager for tracing (wraps trace_scope for Scheme 3)."""
    
    def __init__(self, name: str, tags: List[str], input_query: str):
        self.name = name
        self.tags = tags
        self.input_query = input_query
        self.trace: Optional[TraceEvent] = None
        self._context_manager = None
    
    def __enter__(self):
        if _SCHEME3_AVAILABLE:
            self._context_manager = trace_scope(
                name=self.name,
                input_query=self.input_query,
                tags=self.tags
            )
            self.trace = self._context_manager.__enter__()
        else:
            self.trace = start_trace(self.name, self.tags, self.input_query)
        return self.trace
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context_manager:
            return self._context_manager.__exit__(exc_type, exc_val, exc_tb)
        else:
            finish_trace(self.trace, None, exc_val)
            return False
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


__all__ = [
    'init_monitor',
    'trace_scope',
    'get_trace',
    'start_trace',
    'finish_trace',
    'add_context_building_step',
    'add_llm_call_step',
    'add_tool_execution_step',
    'add_skill_trigger_step',
    'add_memory_step',
    'TraceContext',
    'instrument_llm',
    'instrumented_tool',
    '_AGENTSCOPE_AVAILABLE',
    '_SCHEME3_AVAILABLE',
]
```

### 步骤 2：修改 nanobot/agent/loop.py

在 `_run_agent_loop` 方法中添加监控点：

```python
# 在文件顶部添加导入
from nanobot.agent.monitoring import (
    init_monitor,
    start_trace,
    finish_trace,
    add_context_building_step,
    add_llm_call_step,
    add_tool_execution_step,
    add_skill_trigger_step,
    add_memory_step,
    get_trace,
    _AGENTSCOPE_AVAILABLE,
)

# 在 AgentLoop.__init__ 中添加初始化
# 在 __init__ 方法末尾添加：
if _AGENTSCOPE_AVAILABLE:
    init_monitor("http://localhost:8000")  # 或从配置读取

# 修改 _run_agent_loop 方法
async def _run_agent_loop(self, initial_messages, on_progress=None):
    """Run the agent iteration loop with monitoring."""
    messages = initial_messages
    iteration = 0
    final_content = None
    tools_used = []

    while iteration < self.max_iterations:
        iteration += 1

        tool_defs = self.tools.get_definitions()

        # AgentScope: Record LLM call
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
                tool_calls=[{"name": tc.name, "args": tc.arguments} for tc in response.tool_calls] if response.has_tool_calls else [],
                tokens_in=response.usage.prompt_tokens if response.usage else 0,
                tokens_out=response.usage.completion_tokens if response.usage else 0,
                latency_ms=llm_latency,
            )

        if response.has_tool_calls:
            # Process tool calls
            if on_progress:
                thought = self._strip_think(response.content)
                if thought:
                    await on_progress(thought)
                tool_hint = self._tool_hint(response.tool_calls)
                tool_hint = self._strip_think(tool_hint)
                await on_progress(tool_hint, tool_hint=True)

            tool_call_dicts = [
                tc.to_openai_tool_call()
                for tc in response.tool_calls
            ]
            messages = self.context.add_assistant_message(
                messages, response.content, tool_call_dicts,
                reasoning_content=response.reasoning_content,
                thinking_blocks=response.thinking_blocks,
            )

            for tool_call in response.tool_calls:
                tools_used.append(tool_call.name)
                args_str = json.dumps(tool_call.arguments, ensure_ascii=False)
                logger.info("Tool call: {}({})", tool_call.name, args_str[:200])
                
                # AgentScope: Record tool execution
                tool_start = time.time()
                try:
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
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
                
                messages = self.context.add_tool_result(
                    messages, tool_call.id, tool_call.name, result
                )
        else:
            clean = self._strip_think(response.content)
            if response.finish_reason == "error":
                logger.error("LLM returned error: {}", (clean or "")[:200])
                final_content = clean or "Sorry, I encountered an error calling the AI model."
                break
            messages = self.context.add_assistant_message(
                messages, clean, reasoning_content=response.reasoning_content,
                thinking_blocks=response.thinking_blocks,
            )
            final_content = clean
            break

    if final_content is None and iteration >= self.max_iterations:
        logger.warning("Max iterations ({}) reached", self.max_iterations)
        final_content = (
            f"I reached the maximum number of tool call iterations ({self.max_iterations}) "
            f"without completing the task. You can try breaking the task into smaller steps."
        )

    return final_content, tools_used, messages
```

### 步骤 3：重启 nanobot

```bash
# 重启 nanobot 实例
~/.nanobot/manage-zhuzaihou.sh restart
```

### 步骤 4：验证

1. 发送一条测试消息给 nanobot
2. 打开 http://localhost:3001
3. 查看追踪记录，应包含：
   - `input`: 用户输入
   - `thinking`: 构建上下文
   - `llm_call`: LLM 调用详情
   - `tool_call`: 工具执行详情
   - `output`: 最终输出

## 预期输出

在 AgentScope UI 中，你应该看到类似以下的执行链：

```
Trace: nanobot_message (abc123)
Status: success
Duration: 2.5s
Total Tokens: 1,234

Steps:
1. [input] "查询北京天气"
2. [thinking] 构建上下文，历史消息: 0，加载 Skills: weather
3. [llm_call] Model: kimi-for-coding, Messages: 10, Tools: 15
   Tokens: 150/80, Latency: 850ms
4. [tool_call] Tool: weather, Args: {"city": "北京"}
   Result: {"temp": 25, "weather": "sunny"}, Latency: 120ms
5. [llm_call] Model: kimi-for-coding, Messages: 12
   Tokens: 200/150, Latency: 920ms
6. [output] "北京今天晴天，25°C，适合外出。"
```

## 故障排除

### 问题：追踪数据未显示

1. 检查 AgentScope 后端是否运行：
   ```bash
   curl http://localhost:8000/api/health
   ```

2. 检查 nanobot 日志是否有 AgentScope 相关错误

3. 确保 `_AGENTSCOPE_AVAILABLE` 为 True

### 问题：只有 input/output，没有中间步骤

确保 `add_llm_call_step` 和 `add_tool_execution_step` 被正确调用，检查：
- 导入是否正确
- `_AGENTSCOPE_AVAILABLE` 是否为 True
- 方法调用是否在正确的位置

## 参考

- [完整集成指南](../../docs/integration-guide.md)
- [AgentScope 架构设计](../../docs/architecture.md)
