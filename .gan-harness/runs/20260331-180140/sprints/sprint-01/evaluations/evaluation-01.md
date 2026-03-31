# Evaluator 评估报告 - Sprint 01

**评估文件**: `sdk/agentscope/instrumentation/nanobot_instrumentor.py`
**评估时间**: 2026-03-31
**评估模式**: 轻量模式（Generator 自测后 Evaluator 评估）

---

## 评分摘要

| 维度 | 权重 | 得分 | 加权得分 |
|------|------|------|----------|
| 功能完整性 | 40% | 85 | 34.0 |
| 功能正确性 | 30% | 75 | 22.5 |
| 代码质量 | 20% | 70 | 14.0 |
| 兼容性 | 10% | 90 | 9.0 |
| **总分** | **100%** | - | **79.5** |

**结果**: ⚠️ **CONDITIONAL PASS** (需要修订)

---

## 详细评估

### 1. 功能完整性 (85/100)

**✅ 已实现功能**:
- ✅ `_instrument_context_builder`: 正确捕获系统提示词构建
- ✅ `_instrument_agent_loop`: 创建 trace 上下文
- ✅ `_instrument_agent_runner`: 包装 AgentRunner.run()
- ✅ 每次迭代的 `prompt_build` 记录
- ✅ 每次迭代的 `llm_call` 记录
- ✅ `tool_call` 记录（LLM 请求时）
- ✅ Token 统计和 Latency 计算
- ✅ Streaming 和非 streaming 模式都支持

**❌ 缺失功能**:
- ❌ **Tool 执行结果未记录**: 当前只在 LLM 返回时记录 tool_call，但没有记录工具实际执行的结果
- ❌ **Tool 执行耗时未记录**: 工具执行时间未被捕获
- ❌ **迭代间消息变更未明确展示**: 虽然记录了 prompt，但没有清晰展示消息列表的变化

**改进建议**:
```python
# 需要补充工具执行结果的记录
# 可以通过 instrument ToolRegistry.execute 或类似方法实现
```

---

### 2. 功能正确性 (75/100)

**✅ 正确实现**:
- ✅ 使用 `nonlocal` 正确管理迭代计数
- ✅ `finally` 块确保 provider 方法被恢复
- ✅ 异步函数正确处理
- ✅ 使用 `getattr` 安全访问属性

**⚠️ 潜在问题**:

#### 问题 2.1: Tool Call 记录时机过早
**严重程度**: 中
**描述**: Tool call 在 LLM 返回时记录，此时工具还未执行
```python
# 当前代码 (line 265-281)
tool_calls = getattr(response, 'tool_calls', None)
if tool_calls:
    for tc in tool_calls:
        add_tool_call(
            tool_name=tool_name,
            arguments=tool_args,
            result="[Tool call requested by LLM]",  # ← 不是实际结果
            latency_ms=0  # ← 未计算实际耗时
        )
```
**建议**: 补充工具执行后的结果更新，或在工具执行完成时单独记录

#### 问题 2.2: Token 估算不准确
**严重程度**: 低
**描述**: 使用 `len(content) // 4` 作为 token 估算 fallback
```python
# line 250, 318
tokens_in = usage.get('prompt_tokens', 0) or sum(len(str(m.get('content', ''))) // 4 for m in messages)
```
**建议**: 考虑使用更准确的 tokenizer，或标记为估算值

#### 问题 2.3: 异常静默处理
**严重程度**: 中
**描述**: 多处使用 `except Exception as e` 然后只记录 debug 日志
```python
# 例如 line 283-284
except Exception as e:
    logger.debug(f"AgentScope: Failed to record LLM call: {e}")
```
**风险**: 可能导致问题难以发现，特别是在生产环境
**建议**: 考虑使用 `logger.warning` 或 `logger.error`，或添加 metrics 上报

---

### 3. 代码质量 (70/100)

**✅ 优点**:
- ✅ 代码结构清晰，三个 instrument 函数职责分明
- ✅ 使用 `functools.wraps` 保留原函数元数据
- ✅ 日志信息完整，便于调试
- ✅ 非侵入式设计，不破坏原功能

**❌ 代码异味**:

#### 问题 3.1: 严重代码重复
**严重程度**: 高
**描述**: `monitored_chat_with_retry` 和 `monitored_chat_stream_with_retry` 几乎完全相同
```python
# 两个函数各 ~65 行，重复度 ~90%
# 只在 model_config 中多了一个 "streaming": True
```
**建议**: 提取公共函数
```python
async def _monitored_llm_call(original_func, iteration_count, is_streaming, **kwargs):
    # 公共逻辑
    pass

async def monitored_chat_with_retry(**kwargs):
    return await _monitored_llm_call(
        original_chat_with_retry, iteration_count, False, **kwargs
    )
```

#### 问题 3.2: 嵌套函数过长
**严重程度**: 中
**描述**: `monitored_run` 函数内嵌套了两个大函数，共 150+ 行
**建议**: 将嵌套函数提取为模块级函数，通过参数传递必要上下文

#### 问题 3.3: 魔术字符串
**严重程度**: 低
**描述**: 多处硬编码字符串如 `"[Tool call requested by LLM]"`
**建议**: 定义为常量

---

### 4. 兼容性 (90/100)

**✅ 兼容性良好**:
- ✅ 同时支持 streaming 和非 streaming 模式
- ✅ 与原 AgentLoop 兼容
- ✅ 环境变量控制是否启用

**⚠️ 注意事项**:
- 依赖 nanobot 的内部 API (`AgentRunner`, `AgentLoop` 等)，nanobot 版本升级时可能需要调整

---

## 必须修复项 (Blockers)

1. **提取公共函数**: `monitored_chat_with_retry` 和 `monitored_chat_stream_with_retry` 需要重构
2. **补充工具执行结果记录**: 当前只记录了 tool call 请求，需要记录实际执行结果

## 建议修复项 (Nice to have)

3. 改善异常处理，使用更合适的日志级别
4. 将嵌套函数提取为模块级函数
5. 魔术字符串定义为常量

---

## 修订建议

```python
# 建议的重构结构

async def _record_llm_call(original_func, iteration_count, is_streaming, **kwargs):
    """公共的 LLM 调用记录逻辑"""
    # ... 公共逻辑
    pass

async def _record_tool_calls(response, all_tools_used):
    """记录工具调用请求"""
    # ... 工具调用记录
    pass

async def _monitored_chat_wrapper(original_func, is_streaming):
    """创建包装函数"""
    async def wrapper(**kwargs):
        # ... 使用 _record_llm_call
        pass
    return wrapper
```

---

## 最终判定

**评分**: 79.5/100  
**结果**: ⚠️ **CONDITIONAL PASS**  
**建议**: 修复两个 blocker 后可通过

**下一步**: Generator 根据本评估进行修订，然后重新评估。
