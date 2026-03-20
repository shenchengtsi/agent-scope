# Token 定价配置指南

AgentScope 支持为不同模型配置 token 单价，自动计算 LLM 调用成本。

## 快速开始

### 1. 查看默认定价

```python
from agentscope import get_token_pricing

# 获取默认定价
pricing = get_token_pricing("default")
print(f"Input: ${pricing['input']}/1K tokens")
print(f"Output: ${pricing['output']}/1K tokens")
```

### 2. 设置自定义定价

```python
from agentscope import set_token_pricing

# 为特定模型设置定价
set_token_pricing("gpt-4", input_price=0.03, output_price=0.06)
set_token_pricing("kimi-for-coding", input_price=0.001, output_price=0.001)
set_token_pricing("my-custom-model", input_price=0.0005, output_price=0.001)
```

### 3. 在 LLM 调用中使用

```python
from agentscope import add_llm_call

# 自动计算成本
add_llm_call(
    prompt="Hello, how are you?",
    completion="I'm doing well, thank you!",
    tokens_input=10,
    tokens_output=20,
    latency_ms=500,
    model="gpt-4"  # 指定模型以使用对应定价
)
```

## 预置模型定价

| 模型 | Input ($/1K) | Output ($/1K) |
|------|--------------|---------------|
| default | 0.0015 | 0.002 |
| gpt-4 | 0.03 | 0.06 |
| gpt-4-turbo | 0.01 | 0.03 |
| gpt-3.5-turbo | 0.0005 | 0.0015 |
| kimi-for-coding | 0.001 | 0.001 |
| kimi | 0.001 | 0.001 |

## 完整示例

```python
import time
from agentscope import (
    init_monitor,
    trace_scope,
    add_llm_call,
    set_token_pricing,
    calculate_cost
)

# 初始化监控
init_monitor("http://localhost:8000")

# 配置自定义模型定价
set_token_pricing("my-llm", input_price=0.002, output_price=0.004)

# 在 trace 中使用
with trace_scope("customer_service", input_query="Hello"):
    # 模拟 LLM 调用
    tokens_in = 100
    tokens_out = 200
    
    add_llm_call(
        prompt="Hello",
        completion="Hi there! How can I help you today?",
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        latency_ms=800,
        model="my-llm"  # 使用自定义定价
    )
    
    # 成本会自动计算并累加到 trace.cost_estimate
    print(f"This call cost: ${calculate_cost(tokens_in, tokens_out, 'my-llm')}")

# trace.cost_estimate 现在包含总成本
```

## 成本计算说明

成本计算公式：
```
总成本 = (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price
```

例如：
- Input: 1000 tokens, $0.0015/1K
- Output: 500 tokens, $0.002/1K
- 成本 = (1000/1000) * 0.0015 + (500/1000) * 0.002 = $0.0015 + $0.001 = $0.0025

## 在 Dashboard 中查看

成本信息会显示在 AgentScope Dashboard 中：
- 每个 Trace 的 `cost_estimate` 字段
- 前端界面会显示总成本

## 注意事项

1. 价格单位是 USD/1K tokens
2. 如果不指定 model 参数，使用 "default" 定价
3. 成本会自动累加到当前 trace 的 `cost_estimate`
4. 可以在运行时动态修改定价配置
