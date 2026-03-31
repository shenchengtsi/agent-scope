# GAN Harness Plan: Analytics 功能修复

## 问题描述

用户反馈 Analytics 功能存在以下问题：
1. 计算数据很多是错的
2. Cost 数据没有统计出来

## 现状分析

### 涉及模块

| 模块 | 文件 | 功能 |
|------|------|------|
| Frontend | Analytics 页面组件 | 展示统计数据 |
| Backend | `/api/traces` 接口 | 提供 trace 数据 |
| Backend | `/api/analytics` 接口 | 提供聚合统计数据 |
| SDK | `monitor.py` | 记录 LLM 调用和 cost |
| SDK | `pricing.py` | 计算 cost |

### 已知问题

1. **Cost 计算**
   - `add_llm_call()` 中调用 `calculate_cost()`
   - 但前端 Analytics 页面可能未正确读取 `llm_call.cost` 字段
   - 或者聚合计算时遗漏了 cost

2. **统计数据错误**
   - Token 统计可能不准确
   - 时间范围过滤可能有问题
   - 聚合计算逻辑可能有 bug

## 验收标准

1. **Cost 统计**
   - [ ] Dashboard 显示总 cost
   - [ ] Analytics 页面显示各模型 cost  breakdown
   - [ ] 每个 trace 显示其 cost
   - [ ] Cost 计算与 tokens * pricing 一致

2. **数据准确性**
   - [ ] Token 统计准确（input/output）
   - [ ] Latency 统计准确
   - [ ] Trace 计数准确
   - [ ] 时间范围过滤正确

3. **聚合统计**
   - [ ] 按模型聚合正确
   - [ ] 按时间聚合正确
   - [ ] 按状态聚合正确

## 技术方案

### Sprint 1: Backend API 修复
- 检查 `/api/analytics` 接口实现
- 修复 cost 聚合计算
- 修复 token 统计

### Sprint 2: Frontend 展示修复
- 检查 Analytics 页面组件
- 修复 cost 展示
- 修复数据绑定

### Sprint 3: 验证测试
- 创建测试 traces
- 验证统计数据
- 对比计算结果

## 评估维度

| 维度 | 权重 | 标准 |
|------|------|------|
| 功能完整性 | 40% | Cost 统计正确显示 |
| 数据准确性 | 30% | Token/latency/cost 计算正确 |
| 代码质量 | 20% | 修复代码清晰、健壮 |
| 兼容性 | 10% | 不影响现有功能 |
