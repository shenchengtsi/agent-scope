# Analytics 问题根因分析

## 问题确认

### 1. SQLite 表结构缺失字段

**文件**: `sdk/agentscope/storage/sqlite.py`

**当前表结构** (第 35-50 行):
```sql
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_ms REAL,
    input_query TEXT,
    tags TEXT,  -- JSON array
    metadata TEXT,  -- JSON object
    steps TEXT,  -- JSON array
    child_trace_ids TEXT,  -- JSON array
    parent_trace_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**缺失字段**:
- `total_tokens` - Token 统计
- `cost_estimate` - Cost 统计
- `llm_call_count` - LLM 调用次数
- `tool_call_count` - Tool 调用次数

### 2. Save 方法未保存这些字段

**文件**: `sdk/agentscope/storage/sqlite.py` (第 74-111 行)

`save_trace` 方法只保存了表结构中的字段，没有保存 `total_tokens` 和 `cost_estimate`。

### 3. 后端 API 读取这些字段

**文件**: `backend/main_v2.py` (第 725-726 行)
```python
tokens = [t.get("total_tokens", 0) for t in recent_traces]
costs = [t.get("cost_estimate", 0) for t in recent_traces]
```

但由于存储层没有保存，读取时总是得到默认值 0。

## 修复方案

### Sprint 1: SQLite 存储修复
1. 修改表结构，添加缺失字段
2. 修改 `save_trace` 方法，保存统计数据
3. 添加数据库迁移逻辑

### Sprint 2: 内存存储修复
1. 同样修复内存存储实现

### Sprint 3: 验证测试
1. 创建新 trace 验证统计正确
2. 检查 Analytics API 返回

## 影响范围

| 模块 | 影响 | 修复优先级 |
|------|------|-----------|
| SQLiteStorage | 高 | P0 |
| MemoryStorage | 中 | P1 |
| Analytics API | 高 | 依赖存储修复 |
| Dashboard | 高 | 依赖存储修复 |
