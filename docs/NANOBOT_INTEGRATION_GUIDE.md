# AgentScope + Nanobot 集成指南

## 快速开始（推荐方案）

### 1. 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Nanobot 实例 (多实例支持)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐      ┌─────────────────────────────┐  │
│  │  agentscope_    │─────▶│  nanobot/agent/monitoring.py │  │
│  │  runner.py      │      │  (88行 stub，委托到 SDK)      │  │
│  └─────────────────┘      └─────────────────────────────┘  │
│           │                          │                      │
│           ▼                          ▼                      │
│  ┌─────────────────────────────────────────────┐           │
│  │   AgentScope Instrumentation               │           │
│  │   (nanobot_instrumentor.py)                │           │
│  │   - Wraps AgentLoop._process_message       │           │
│  │   - Automatic trace context creation       │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  AgentScope Backend  │
              │    localhost:8000    │
              └──────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  AgentScope Frontend │
              │    localhost:3000    │
              └──────────────────────┘
```

### 2. 文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `nanobot_instrumentor.py` | `agentscope/instrumentation/` | 非侵入式 instrumentation |
| `monitoring.py` | `nanobot/agent/` | 88行 stub，委托到 SDK |
| `agentscope_runner.py` | `~/.nanobot/` | 启动包装脚本 |

### 3. 配置步骤

#### 步骤 1: 准备 nanobot 的 monitoring.py

创建/更新 `nanobot/agent/monitoring.py`:

```python
"""AgentScope monitoring - minimal stub that delegates to AgentScope SDK."""

import sys
sys.path.insert(0, '/path/to/agent-scope')

try:
    from agentscope.monitor import add_llm_call, add_tool_call, add_thinking
    _AGENTSCOPE_AVAILABLE = True
except ImportError:
    _AGENTSCOPE_AVAILABLE = False
    def add_llm_call(*args, **kwargs): pass
    def add_tool_call(*args, **kwargs): pass
    def add_thinking(*args, **kwargs): pass


def add_llm_call_step(model: str, messages_count: int, tools_count: int,
                      response_content, tool_calls,
                      tokens_input: int = 0, tokens_output: int = 0, latency_ms: float = 0):
    """Record LLM call."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    content = f"Model: {model}, Messages: {messages_count}, Tools: {tools_count}"
    if response_content:
        content += f"\nResponse: {response_content[:200]}"
    
    add_llm_call(
        prompt=f"Messages: {messages_count}",
        completion=content,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        latency_ms=latency_ms,
    )


def add_tool_execution_step(tool_name: str, arguments: dict, result,
                            latency_ms: float = 0, error: str = None):
    """Record tool execution."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    
    is_error = error is not None or (isinstance(result, str) and result.startswith("Error"))
    
    add_tool_call(
        tool_name=tool_name,
        arguments=arguments,
        result=str(result)[:500] if result and not is_error else None,
        error=error if error else (str(result)[:500] if is_error else None),
        latency_ms=latency_ms,
    )


def add_thinking_step(content: str):
    """Record thinking/reasoning step."""
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(content)


# 兼容函数（可选）
def add_prompt_building_step(system_prompt: str, history_count: int, context_length: int, max_context: int):
    if not _AGENTSCOPE_AVAILABLE:
        return
    usage = (context_length / max_context * 100) if max_context > 0 else 0
    add_thinking(f"Prompt: {len(system_prompt)} chars, History: {history_count}, Context: {context_length}/{max_context} ({usage:.1f}%)")

def add_skill_loading_step(skills: list, loaded_count: int, failed_count: int, total_time_ms: float):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Skills: {loaded_count} loaded, {failed_count} failed in {total_time_ms:.1f}ms")

def add_session_lifecycle_step(event: str, session_key: str, details: str = ""):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Session {event}: {session_key}")

def add_skill_trigger_step(skill_name: str, trigger_reason: str):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Skill: {skill_name} - {trigger_reason}")

def add_retry_step(attempt: int, max_attempts: int, error_type: str, delay: float, will_retry: bool):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Retry {attempt}/{max_attempts}: {error_type}, delay={delay}s")

def add_rate_limit_step(limit_type: str, current_usage: int, limit: int, wait_time: float = 0):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Rate limit {limit_type}: {current_usage}/{limit}")

def add_context_window_step(operation: str, original_count: int, new_count: int, reason: str):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Context {operation}: {original_count} -> {new_count}")

def add_memory_step(action: str, details: str):
    if not _AGENTSCOPE_AVAILABLE:
        return
    add_thinking(f"Memory {action}: {details}")


# Legacy trace functions (not used in non-intrusive mode)
def start_trace(*args, **kwargs):
    return None

def finish_trace(*args, **kwargs):
    pass

def get_trace():
    return None
```

#### 步骤 2: 创建启动包装脚本

创建 `~/.nanobot/agentscope_runner.py`:

```python
#!/usr/bin/env python3
"""
Nanobot runner with AgentScope monitoring (non-intrusive).

Usage: python agentscope_runner.py --config /path/to/config.json
"""

import sys
import os

# Parse --config argument
config_path = None
if '--config' in sys.argv:
    idx = sys.argv.index('--config')
    if idx + 1 < len(sys.argv):
        config_path = sys.argv[idx + 1]

# Add AgentScope to path
sys.path.insert(0, os.path.expanduser('~/agent-scope'))

# Import and enable AgentScope instrumentation
try:
    from agentscope.instrumentation.nanobot_instrumentor import instrument
    instrument()
    print("✅ AgentScope instrumentation enabled", file=sys.stderr)
except Exception as e:
    print(f"⚠️  AgentScope instrumentation failed: {e}", file=sys.stderr)

# Change to nanobot directory
os.chdir(os.path.expanduser('~/AI_Workspace2/nanobot'))

# Build gateway command args
gateway_args = ['gateway']
if config_path:
    gateway_args.extend(['-c', config_path])

# Run nanobot normally
from nanobot.cli.commands import app
app(gateway_args)
```

#### 步骤 3: 启动 nanobot 实例

```bash
# 安装 pm2 (如果未安装)
npm install -g pm2

# 启动所有实例
cd ~/AI_Workspace2/nanobot
source .venv/bin/activate

for name in gaogong yanshifan lvfang zhangjuzheng zhuzaihou yansong; do
  pm2 start ~/.nanobot/agentscope_runner.py \
    --name nanobot-$name \
    --interpreter python \
    -- --config ~/.nanobot-$name/config.json
done

# 查看状态
pm2 list
pm2 logs nanobot-yanshifan
```

#### 步骤 4: 验证集成

```bash
# 检查 AgentScope 是否收到数据
curl -s http://localhost:8000/api/traces | jq '.traces | length'

# 查看最新 trace
curl -s http://localhost:8000/api/traces | jq '.traces[-1] | {id, name, status, steps: (.steps | length)}'
```

---

## 架构演变

### 方案对比

| 方案 | 侵入性 | 维护难度 | 升级影响 | 推荐度 |
|------|--------|----------|----------|--------|
| **非侵入式 (当前)** | ⭐ 零侵入 | ⭐ 简单 | 无影响 | ⭐⭐⭐⭐⭐ |
| **侵入式 (旧)** | ⭐⭐⭐ 高 | ⭐⭐⭐ 困难 | 需同步修改 | ❌ 不推荐 |

### 侵入式 vs 非侵入式

#### 侵入式架构（已废弃）
```
nanobot/
├── agent/
│   ├── loop.py          ← 修改（添加监控调用）
│   ├── monitoring.py    ← 538行代码
│   └── tools/
│       └── registry.py  ← 修改（添加监控调用）
```

**问题**:
- nanobot 升级时需要同步修改
- 代码冲突风险
- 难以维护

#### 非侵入式架构（推荐）
```
agent-scope/                ← 独立项目
├── agentscope/
│   └── instrumentation/
│       └── nanobot_instrumentor.py  ← 运行时注入
└── examples/
    └── nanobot_wrapper.py

nanobot/                    ← 无需修改
├── agent/
│   ├── loop.py             ← 原封不动
│   └── tools/
│       └── registry.py     ← 原封不动
```

**优势**:
- nanobot 升级不影响 AgentScope
- 零代码冲突
- 易于维护
- 支持多实例同时监控

---

## 数据流

```
Feishu Message
      ↓
AgentLoop._process_message (wrapped by instrumentation)
      ↓
┌─────────────────────────────────────────────────────┐
│              trace_scope 上下文                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ build_msgs  │  │  LLM chat   │  │ tool exec   │ │
│  │             │  │             │  │             │ │
│  │ add_prompt  │  │ add_llm_call│  │add_tool_call│ │
│  │ _building   │  │    _step    │  │    _step    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
      ↓
AgentScope Backend (localhost:8000)
      ↓
AgentScope Frontend (localhost:3000)
```

---

## 故障排除

### Q: 监控数据没有显示？

**检查清单**:
```bash
# 1. 检查 AgentScope backend 是否运行
curl http://localhost:8000/api/traces

# 2. 检查 nanobot 实例是否使用 wrapper 启动
pm2 describe nanobot-yanshifan | grep "script path"

# 3. 检查日志中是否有 instrumentation 成功消息
pm2 logs nanobot-yanshifan --lines 20 | grep -i "agentscope"

# 4. 手动测试监控功能
cd ~/AI_Workspace2/nanobot
source .venv/bin/activate
python -c "
import sys
sys.path.insert(0, '~/agent-scope')
from agentscope.monitor import init_monitor, trace_scope, add_thinking
init_monitor('http://localhost:8000')
with trace_scope(name='test', input_query='test'):
    add_thinking('test message')
print('Test completed')
"
```

### Q: Tool execution 显示 error 状态？

**原因**: `add_tool_execution_step` 参数顺序错误

**修复**: 确保使用修复后的参数顺序
```python
# 正确
def add_tool_execution_step(tool_name, arguments, result, latency_ms=0, error=None):

# 错误（旧版本）
def add_tool_execution_step(tool_name, arguments, result, error=None, latency_ms=0):
```

### Q: 如何临时禁用监控？

```bash
# 方法1: 使用原始 nanobot 启动
pm2 stop nanobot-yanshifan
pm2 start nanobot-yanshifan --interpreter python -- nanobot/main.py --config ~/.nanobot-yanshifan/config.json

# 方法2: 环境变量控制
export AGENTSCOPE_ENABLED=false
pm2 restart nanobot-yanshifan
```

---

## 生产环境最佳实践

### PM2 配置

创建 `~/.nanobot/ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'nanobot-yanshifan',
      script: '/Users/samsonchoi/.nanobot/agentscope_runner.py',
      interpreter: 'python',
      args: '--config /Users/samsonchoi/.nanobot-yanshifan/config.json',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        AGENTSCOPE_BACKEND_URL: 'http://localhost:8000',
      },
      log_file: '/Users/samsonchoi/.pm2/logs/nanobot-yanshifan-combined.log',
      out_file: '/Users/samsonchoi/.pm2/logs/nanobot-yanshifan-out.log',
      error_file: '/Users/samsonchoi/.pm2/logs/nanobot-yanshifan-error.log',
    },
    // ... 其他实例
  ],
};
```

启动:
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 参考链接

- [AgentScope GitHub](https://github.com/shenchengtsi/agent-scope)
- [nanobot 仓库](https://github.com/your-org/nanobot)
