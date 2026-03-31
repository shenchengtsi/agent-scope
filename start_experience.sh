#!/bin/bash
# AgentScope 完整体验启动脚本

set -e

echo "🚀 AgentScope 完整体验启动器"
echo "=============================="
echo ""

# 检查服务状态
echo "📋 检查服务状态..."

# 检查 Backend
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend v2: 运行中 (端口 8000)"
else
    echo "❌ Backend v2: 未运行"
    echo "   正在启动..."
    cd /Users/samsonchoi/AI_Workspace/agent-scope/backend
    export AGENTSCOPE_STORAGE_BACKEND=sqlite
    export AGENTSCOPE_DB_PATH=../data/agentscope.db
    python main_v2.py > /tmp/agentscope_v2.log 2>&1 &
    sleep 3
    echo "✅ Backend v2 已启动"
fi

# 检查 Frontend
if lsof -i :3000 > /dev/null 2>&1; then
    echo "✅ Frontend: 运行中 (端口 3000)"
else
    echo "⚠️  Frontend: 未运行"
    echo "   建议手动启动: cd frontend && npm start"
fi

# 检查 Nanobot
if pgrep -f nanobot > /dev/null; then
    echo "✅ Nanobot: 运行中"
else
    echo "⚠️  Nanobot: 未运行"
fi

echo ""
echo "=============================="
echo ""

# 创建示例数据
echo "📊 创建示例数据..."
cd /Users/samsonchoi/AI_Workspace/agent-scope

python3 << 'PYTHON'
import requests
import json
from datetime import datetime

BASE = "http://localhost:8000"
now = datetime.now().isoformat()

# 创建父 trace
trace1 = {
    "id": "demo-main-001",
    "name": "代码审查助手",
    "tags": ["demo", "code-review"],
    "start_time": now,
    "status": "success",
    "input_query": "审查 PR #123",
    "output_result": "审查完成，建议修改",
    "steps": [
        {"id": "s1", "type": "input", "content": "获取 PR 数据", "timestamp": now, "latency_ms": 100},
        {"id": "s2", "type": "llm_call", "content": "分析代码变更", "timestamp": now, "tokens_input": 800, "tokens_output": 300, "latency_ms": 2000},
    ],
    "total_latency_ms": 2500,
    "total_tokens": 1100,
    "cost_estimate": 0.02,
    "child_trace_ids": ["demo-git-001", "demo-llm-001"],
}
requests.post(f"{BASE}/api/traces", json=trace1)

# 创建子 trace 1
trace2 = {
    "id": "demo-git-001",
    "name": "Git 操作",
    "tags": ["demo", "git"],
    "start_time": now,
    "status": "success",
    "input_query": "获取 PR 数据",
    "output_result": "PR 数据获取成功",
    "parent_trace_id": "demo-main-001",
    "steps": [{"id": "s1", "type": "tool_call", "content": "git fetch", "timestamp": now, "latency_ms": 500}],
    "total_latency_ms": 500,
}
requests.post(f"{BASE}/api/traces", json=trace2)

# 创建子 trace 2
trace3 = {
    "id": "demo-llm-001",
    "name": "LLM 分析",
    "tags": ["demo", "llm"],
    "start_time": now,
    "status": "success",
    "input_query": "分析代码质量",
    "output_result": "代码质量评分: 8/10",
    "parent_trace_id": "demo-main-001",
    "steps": [{"id": "s1", "type": "llm_call", "content": "代码分析", "timestamp": now, "tokens_input": 800, "tokens_output": 300, "latency_ms": 2000}],
    "total_latency_ms": 2000,
    "total_tokens": 1100,
    "cost_estimate": 0.018,
}
requests.post(f"{BASE}/api/traces", json=trace3)

print("✅ 示例数据已创建 (3 个 traces)")
PYTHON

echo ""
echo "=============================="
echo ""
echo "🌐 访问地址:"
echo "   前端页面: http://localhost:3000"
echo "   API 文档: http://localhost:8000/api/info"
echo ""
echo "📊 创建的示例数据:"
echo "   - demo-main-001: 代码审查助手 (父)"
echo "   - demo-git-001:  Git 操作 (子)"
echo "   - demo-llm-001:  LLM 分析 (子)"
echo ""
echo "🔍 查看命令:"
echo "   curl http://localhost:8000/api/traces"
echo "   curl http://localhost:8000/api/metrics/realtime"
echo ""
echo "🎉 体验指南:"
echo "   1. 打开浏览器访问 http://localhost:3000"
echo "   2. 查看 traces 列表"
echo "   3. 点击 trace 查看详情和父子关系"
echo "   4. 查看实时指标"
echo ""
echo "=============================="
echo ""

# 尝试打开浏览器
if command -v open &> /dev/null; then
    echo "🌍 正在打开浏览器..."
    open "http://localhost:3000" &
fi

echo "✨ AgentScope 已准备就绪！"
