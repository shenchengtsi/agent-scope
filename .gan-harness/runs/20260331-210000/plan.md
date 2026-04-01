# GAN Harness Plan: Agent 评测系统 (v0.6.0)

## 背景

当前 AgentScope 记录了 traces 和 steps，但缺乏 Agent 性能评测维度。需要增加评测指标来评估 Agent 的工作效率和质量。

## 需求分析

### 需要记录的评测数据

| 指标 | 定义 | 来源 |
|------|------|------|
| **任务完成状态** | success / failed / timeout | trace.status |
| **决策步数** | LLM 迭代次数 | llm_call 步骤数 |
| **工具调用总数** | 调用了多少次工具 | tool_call 步骤数 |
| **工具调用成功数** | 成功执行的工具调用 | tool_call 结果判断 |
| **工具调用失败数** | 失败/错误的工具调用 | tool_call 结果判断 |
| **任务耗时** | 总执行时间 | trace.duration_ms |
| **token 效率** | 完成任务所需 token 数 | trace.total_tokens |

### 需要计算的统计指标

| 统计指标 | 计算公式 |
|----------|----------|
| **任务完成率** | success_count / total_count |
| **平均决策步数** | sum(iteration_count) / total_count |
| **工具调用成功率** | success_tool_calls / total_tool_calls |
| **平均任务耗时** | sum(duration_ms) / total_count |
| **平均 token 消耗** | sum(total_tokens) / total_count |

## 技术方案

### Phase 1: 数据模型扩展

1. **Trace 模型新增字段**
   - `iteration_count`: 决策迭代次数
   - `successful_tool_calls`: 成功工具调用数
   - `failed_tool_calls`: 失败工具调用数
   - `completion_status`: 详细完成状态

2. **ToolCall 模型增强**
   - `execution_status`: success / failed / timeout
   - `error_message`: 失败原因
   - `execution_duration_ms`: 执行耗时

### Phase 2: Instrumentor 增强

修改 `nanobot_instrumentor.py`：
- 记录每次迭代（iteration）
- 记录工具执行结果
- 计算统计指标

### Phase 3: 统计 API

新增 `/api/analytics/agent-evaluation`：
```json
{
  "time_range": "24h",
  "metrics": {
    "task_completion_rate": 0.95,
    "avg_iteration_count": 2.3,
    "tool_success_rate": 0.88,
    "avg_duration_ms": 15000,
    "avg_token_count": 5000
  },
  "breakdown_by_name": [...],
  "trend_over_time": [...]
}
```

### Phase 4: 前端展示

新增 "Agent Evaluation" 页面：
- 核心指标卡片
- 成功率趋势图
- 工具调用成功率分布
- 按 Agent 名称分组统计

## 验收标准

1. [ ] 每个 trace 自动记录评测数据
2. [ ] 统计 API 返回正确指标
3. [ ] 前端页面展示评测结果
4. [ ] 支持时间范围筛选
5. [ ] 支持按 Agent 名称分组

## 评估维度

| 维度 | 权重 | 标准 |
|------|------|------|
| 数据完整性 | 30% | 所有指标正确记录 |
| 统计准确性 | 30% | 计算公式正确 |
| 代码质量 | 20% | 扩展性强，不破坏现有功能 |
| 用户体验 | 20% | 前端展示清晰直观 |
