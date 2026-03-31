# Sprint 合同：代码优化与测试覆盖

## Sprint 1：存储层重构与抽象

### 合同双方
- **Generator**: 实现存储层重构
- **Evaluator**: 评估代码质量和设计合理性

### 交付物

1. **存储抽象接口** (`sdk/agentscope/storage/`)
   - `BaseStorage` 抽象基类
   - `InMemoryStorage` 实现（当前行为）
   - `SQLiteStorage` 实现（持久化）

2. **重构 Backend 存储逻辑**
   - 替换内存 Dict 为 Storage 接口
   - 支持存储后端切换（环境变量配置）

3. **数据模型优化**
   - Pydantic v2 兼容性检查
   - 添加缺失的字段验证

### 验收标准

| 标准 | 检查方法 |
|------|---------|
| 存储接口可切换 | 设置 `AGENTSCOPE_STORAGE=sqlite` 后数据持久化 |
| 单元测试覆盖 | `pytest tests/storage/` 通过率 100% |
| 向后兼容 | 现有代码无需修改即可工作 |
| 性能 | SQLite 写入延迟 < 100ms |

### 技术规范

```python
# 抽象接口设计
class BaseStorage(ABC):
    @abstractmethod
    def save_trace(self, trace: dict) -> str: ...
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[dict]: ...
    
    @abstractmethod
    def list_traces(self, filters: dict) -> List[dict]: ...
```

### 评分权重
- 功能完整性：高
- 代码质量：高
- 测试覆盖：高
- 设计合理性：中

## Sprint 2：测试基础设施

### 交付物

1. **测试框架搭建**
   - `pytest` 配置
   - `pytest-asyncio` 支持
   - `pytest-cov` 覆盖率

2. **单元测试**
   - SDK 核心功能测试
   - Storage 层测试
   - Models 数据模型测试

3. **集成测试**
   - End-to-end 追踪流程
   - Backend API 测试

### 验收标准
- 单元测试覆盖率 > 80%
- 集成测试覆盖主要用户流程
- CI 流程可运行全部测试

## Sprint 3：错误处理与日志优化

### 交付物

1. **统一错误处理**
   - 自定义异常层次结构
   - 错误码规范
   - 用户友好错误消息

2. **日志系统**
   - 结构化日志（JSON）
   - 日志级别配置
   - 上下文追踪 ID

3. **重试机制**
   - 指数退避重试
   - 可配置重试策略

### 验收标准
- 所有网络调用有重试机制
- 日志可查询追踪 ID
- 错误消息对终端用户友好
