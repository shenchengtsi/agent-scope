# Nanobot AgentScope 监控启动要求

本文档说明如何配置 nanobot 实例以支持 AgentScope 监控。

## 核心要求

### 1. SDK 安装

确保 ai-agent-scope SDK 安装在 nanobot 的虚拟环境中：

```bash
cd ~/agent-scope/sdk
~/AI_Workspace2/nanobot/.venv/bin/pip install -e .
```

验证安装：
```bash
~/AI_Workspace2/nanobot/.venv/bin/python3 -c "import agentscope; print(agentscope.__file__)"
```

### 2. 启动方式选择

有两种方式启用 AgentScope 监控：

#### 方式 A: 包装器脚本 (推荐用于 main 实例)

使用 `agentscope_runner.py` 作为入口点：

```xml
<!-- com.nanobot.main.plist -->
<key>ProgramArguments</key>
<array>
    <string>/Users/samsonchoi/AI_Workspace2/nanobot/.venv/bin/python3</string>
    <string>/Users/samsonchoi/.nanobot/agentscope_runner.py</string>
    <string>--config</string>
    <string>/Users/samsonchoi/.nanobot/config.json</string>
</array>
```

包装器脚本特点：
- 自动添加 SDK 路径到 `sys.path`
- 显式调用 `instrument()` 启用监控
- 支持 `AGENTSCOPE_AUTO_INSTRUMENT` 环境变量

#### 方式 B: sitecustomize.py (推荐用于其他实例)

在工作目录创建 `sitecustomize.py`：

```python
"""Auto-load AgentScope instrumentation for nanobot."""
import sys
import os

agentscope_path = "/Users/samsonchoi/agent-scope/sdk"
if agentscope_path not in sys.path:
    sys.path.insert(0, agentscope_path)

os.environ["AGENTSCOPE_AUTO_INSTRUMENT"] = "true"

try:
    from agentscope.instrumentation.nanobot_instrumentor import instrument
    instrument()
    print("✅ AgentScope: Instrumentation loaded via sitecustomize", file=sys.stderr)
except Exception as e:
    print(f"⚠️ AgentScope: Failed to load instrumentation: {e}", file=sys.stderr)
```

将此文件放入实例工作目录：
- `~/.nanobot-zhangjuzheng/sitecustomize.py`
- `~/.nanobot-lvfang/sitecustomize.py`
- 等等

### 3. Plist 配置要点

对于使用 sitecustomize.py 的实例：

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/samsonchoi/AI_Workspace2/nanobot/.venv/bin/python3</string>
    <string>-c</string>
    <string>import sys; sys.path.insert(0, '/Users/samsonchoi/.nanobot-{instance}'); exec(open('/Users/samsonchoi/.nanobot-{instance}/sitecustomize.py').read()); import nanobot.cli.commands; nanobot.cli.commands.app(['gateway', '--config', '/Users/samsonchoi/.nanobot-{instance}/config.json'])</string>
</array>

<key>WorkingDirectory</key>
<string>/Users/samsonchoi/.nanobot-{instance}</string>

<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/Users/samsonchoi/AI_Workspace2/nanobot/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONPATH</key>
    <string>/Users/samsonchoi/agent-scope/sdk:/Users/samsonchoi/.nanobot-{instance}</string>
</dict>
```

关键配置：
- `WorkingDirectory` 必须指向包含 `sitecustomize.py` 的目录
- `PYTHONPATH` 确保 SDK 可被导入
- **重要**：使用 `-c` 选项显式执行 `sitecustomize.py`，解决 Python 加载系统 sitecustomize 而非工作目录 sitecustomize 的问题
- 参考模板：`examples/plist-templates/com.nanobot.instance.plist`

### 4. 监控范围

启用后，以下操作会被自动记录：

| 步骤类型 | 说明 | 数据来源 |
|---------|------|----------|
| `input` | 用户输入 | AgentLoop._process_message |
| `thinking` | 思考过程 | nanobot monitoring |
| `skill_loading` | Skills 加载 | nanobot monitoring (显示具体名称) |
| `prompt_build` | Prompt 构建 | instrumentor (带 call_sequence) |
| `tool_selection` | 工具选择 | instrumentor |
| `llm_call` | LLM 调用 | instrumentor |
| `tool_call` | 工具调用 | instrumentor |
| `output` | 输出结果 | AgentLoop._process_message |

### 5. 验证监控是否工作

发送测试消息后检查：

```bash
# 检查 traces
curl -s http://localhost:8000/api/traces | python3 -m json.tool

# 预期看到:
# - thinking: "Skills: X loaded... (skill_name1, skill_name2)"
# - prompt_build: 带 call_sequence 的 prompt 构建记录
# - llm_call, tool_call 等步骤
```

## 故障排除

### 问题: 没有 trace 记录

检查：
1. SDK 是否正确安装: `pip list | grep agentscope`
2. 进程是否使用正确 Python: `ps aux | grep nanobot`
3. 环境变量是否设置: `cat /proc/[pid]/environ 2>/dev/null | tr '\0' '\n' | grep -i agentscope`

### 问题: skills 显示 17 个而不是实际数量

这是旧的实现方式。确保：
1. instrumentor.py 不记录 skill_loading（由 nanobot monitoring 记录）
2. monitoring.py 已修改显示具体名称

### 问题: 重复的 trace

确保：
1. 不要同时启用 `agentscope_runner.py` 和 `sitecustomize.py`
2. 检查 `AGENTSCOPE_AUTO_INSTRUMENT` 不要重复设置

### 问题: sitecustomize.py 没有加载（AgentScope 未启动）

**症状**：stderr 日志中没有 "AgentScope: Instrumentation loaded" 信息

**原因**：Python 加载了系统的 sitecustomize.py，而非工作目录下的 sitecustomize.py

**解决**：使用 `-c` 选项显式执行 sitecustomize.py：

```xml
<key>ProgramArguments</key>
<array>
    <string>/path/to/python3</string>
    <string>-c</string>
    <string>import sys; sys.path.insert(0, '/path/to/workdir'); exec(open('/path/to/workdir/sitecustomize.py').read()); import nanobot.cli.commands; nanobot.cli.commands.app(['gateway', '--config', '/path/to/workdir/config.json'])</string>
</array>
```

**验证**：
```bash
# 检查 stderr 日志
tail ~/.nanobot-{instance}/logs/stderr.log | grep AgentScope

# 预期输出：
# ✅ AgentScope: Instrumentation loaded
```

## 当前配置状态

| 实例 | 启动方式 | 状态 |
|------|----------|------|
| 徐阶 (main) | agentscope_runner.py | ✅ 工作中 |
| 张居正 | 待配置 | - |
| 吕芳 | 待配置 | - |
| 其他 | 待配置 | - |
