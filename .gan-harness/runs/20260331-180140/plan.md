# GAN Harness Plan: nanobot Instrumentor 重写验证

## 任务概述
重写 `nanobot_instrumentor.py` 以捕获完整的 ReAct 循环链条。

## 核心需求

### 1. 功能完整性
- [ ] 捕获 ContextBuilder.build_messages (系统提示词构建)
- [ ] 捕获 AgentRunner 每次迭代的 prompt_build
- [ ] 捕获每次 LLM 调用 (chat_with_retry / chat_stream_with_retry)
- [ ] 捕获工具调用 (tool_call)
- [ ] 保持原有功能不破坏

### 2. 数据准确性
- [ ] Token 统计正确
- [ ] Latency 计算正确
- [ ] 步骤顺序正确
- [ ] 迭代编号正确

### 3. 代码质量
- [ ] 异常处理完善
- [ ] 不污染原对象状态
- [ ] 资源正确释放 (finally 恢复)
- [ ] 日志信息完整

### 4. 兼容性
- [ ] 支持 streaming 模式
- [ ] 支持非 streaming 模式
- [ ] 与原 AgentLoop 兼容

## 验收标准
1. 新 trace 应显示完整的迭代链条
2. 每个 iteration 都有对应的 prompt_build + llm_call
3. 工具调用记录在正确的位置
4. 无异常抛出

## 评估维度
| 维度 | 权重 | 标准 |
|------|------|------|
| 功能完整性 | 40% | 所有步骤类型都正确记录 |
| 功能正确性 | 30% | 异步调用正确，无资源泄漏 |
| 代码质量 | 20% | 清晰、健壮、可维护 |
| 兼容性 | 10% | streaming/non-streaming 都支持 |
