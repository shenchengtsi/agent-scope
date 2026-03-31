# AgentScope 完整体验指南

## 🌐 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| **前端页面** | http://localhost:3000 | AgentScope 监控面板 |
| **Backend API** | http://localhost:8000 | REST API |
| **健康检查** | http://localhost:8000/api/health | 服务状态 |

## 🚀 快速开始

### 步骤 1: 打开前端页面

在浏览器中打开: **http://localhost:3000**

你应该能看到 AgentScope 的监控面板，显示 traces 列表。

### 步骤 2: 给 Nanobot 发送指令

由于 nanobot 已经在后台运行，你可以通过以下几种方式发送指令：

#### 方式 A: 使用 curl 发送请求

```bash
# 发送一个简单的查询
curl -X POST http://localhost:8000/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "id": "nanobot-test-'$(date +%s)'",
    "name": "Nanobot Task",
    "start_time": "'$(date -Iseconds)'",
    "status": "success",
    "input_query": "帮我分析这段代码",
    "output_result": "代码分析完成",
    "steps": [
      {"id": "s1", "type": "input", "content": "接收代码", "timestamp": "'$(date -Iseconds)'"}
    ]
  }'
```

#### 方式 B: 使用体验脚本

运行交互式脚本：
```bash
cd /Users/samsonchoi/AI_Workspace/agent-scope
python demo_v2.py
```

选择选项 2 创建示例数据，然后在前端页面查看。

#### 方式 C: 直接与 nanobot 交互

如果 nanobot 提供了 HTTP 接口，可以通过它的端口发送请求。

### 步骤 3: 在前端查看追踪数据

1. 打开 http://localhost:3000
2. 你应该能看到 traces 列表
3. 点击任意 trace 查看详情
4. 查看执行步骤、延迟、token 使用等信息

## 📊 体验流程

### 1. 基础监控

访问 http://localhost:3000 查看：
- Traces 列表
- 执行状态（成功/失败）
- 基本统计信息

### 2. 创建测试数据

运行：
```bash
cd /Users/samsonchoi/AI_Workspace/agent-scope
python demo_v2.py
```

选择：
- 2: 创建示例数据
- 3: 查询 traces
- 4: 查看父子关系

### 3. 查看 API 文档

```bash
curl http://localhost:8000/api/info | python -m json.tool
```

### 4. 实时指标

```bash
# 实时指标
curl http://localhost:8000/api/metrics/realtime | python -m json.tool

# 存储统计
curl http://localhost:8000/api/stats | python -m json.tool
```

## 🧪 真实场景体验

### 场景 1: 模拟 Nanobot 工作流

```bash
# 创建父 trace（主 Agent）
curl -X POST http://localhost:8000/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "id": "nanobot-main-001",
    "name": "Code Review Agent",
    "tags": ["nanobot", "code-review"],
    "start_time": "'$(date -Iseconds)'",
    "status": "success",
    "input_query": "Review pull request #42",
    "output_result": "Approved with minor comments",
    "steps": [
      {"id": "s1", "type": "input", "content": "Fetching PR data", "timestamp": "'$(date -Iseconds)'", "latency_ms": 100},
      {"id": "s2", "type": "llm_call", "content": "Analyzing changes", "timestamp": "'$(date -Iseconds)'", "tokens_input": 500, "tokens_output": 200, "latency_ms": 1500}
    ],
    "total_latency_ms": 2000,
    "total_tokens": 700,
    "cost_estimate": 0.015,
    "child_trace_ids": ["nanobot-git-001", "nanobot-llm-001"]
  }'

# 创建子 trace 1（Git 操作）
curl -X POST http://localhost:8000/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "id": "nanobot-git-001",
    "name": "Git Operations",
    "tags": ["nanobot", "git"],
    "start_time": "'$(date -Iseconds)'",
    "status": "success",
    "input_query": "Fetch PR #42",
    "output_result": "PR data retrieved",
    "parent_trace_id": "nanobot-main-001",
    "steps": [
      {"id": "s1", "type": "tool_call", "content": "git fetch", "timestamp": "'$(date -Iseconds)'", "latency_ms": 500}
    ],
    "total_latency_ms": 500
  }'

# 创建子 trace 2（LLM 分析）
curl -X POST http://localhost:8000/api/traces \
  -H "Content-Type: application/json" \
  -d '{
    "id": "nanobot-llm-001",
    "name": "LLM Analysis",
    "tags": ["nanobot", "llm"],
    "start_time": "'$(date -Iseconds)'",
    "status": "success",
    "input_query": "Analyze code quality",
    "output_result": "Quality score: 8.5/10",
    "parent_trace_id": "nanobot-main-001",
    "steps": [
      {"id": "s1", "type": "llm_call", "content": "Code analysis", "timestamp": "'$(date -Iseconds)'", "tokens_input": 500, "tokens_output": 200, "latency_ms": 1500}
    ],
    "total_latency_ms": 1500,
    "total_tokens": 700,
    "cost_estimate": 0.012
  }'
```

然后访问 http://localhost:3000 查看完整的追踪链条。

### 场景 2: 查看对比分析

```bash
# 对比两个 traces
curl -X POST http://localhost:8000/api/traces/compare \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id_1": "nanobot-git-001",
    "trace_id_2": "nanobot-llm-001"
  }' | python -m json.tool
```

### 场景 3: 查看时间线

```bash
# 获取 trace 的时间线
curl http://localhost:8000/api/traces/nanobot-main-001/timeline | python -m json.tool
```

## 🔍 故障排查

### 前端无法访问

```bash
# 检查前端是否在运行
lsof -i :3000

# 如果没有，启动前端
cd /Users/samsonchoi/AI_Workspace/agent-scope/frontend
npm start
```

### Backend 无法访问

```bash
# 检查 Backend v2
curl http://localhost:8000/api/health

# 如果没有运行，启动它
cd /Users/samsonchoi/AI_Workspace/agent-scope/backend
export AGENTSCOPE_STORAGE_BACKEND=sqlite
export AGENTSCOPE_DB_PATH=../data/agentscope.db
python main_v2.py
```

### Nanobot 未发送数据

确保 nanobot 正在运行：
```bash
ps aux | grep nanobot
```

如果已运行但未发送数据，可能是配置问题。检查 `~/.nanobot/agentscope_runner.py` 是否存在。

## 📈 预期效果

当你完成上述步骤后，在 http://localhost:3000 应该能看到：

1. **Traces 列表** - 显示所有执行记录
2. **Trace 详情** - 点击可查看步骤详情
3. **执行链** - 父子 trace 关系可视化
4. **性能指标** - 延迟、token、成本统计
5. **实时更新** - WebSocket 推送新数据

## 🎉 恭喜！

你现在正在体验完整的 AgentScope v2！
