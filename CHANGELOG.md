# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-31

### 🎯 Enterprise Analytics & Observability Enhancement / 企业级可观测性增强

This release introduces comprehensive enterprise-grade analytics capabilities, focusing on scalability, performance monitoring, and cost analysis.

本次发布引入全面的企业级分析能力，专注于可扩展性、性能监控和成本分析。

#### Added / 新增功能

- **📊 Analytics Dashboard / 分析仪表板**
  - New Analytics page with tabbed interface (Trends / Cost Report) / 新增分析页面，支持标签切换（趋势/成本报表）
  - Historical trend charts with multiple visualization types / 历史趋势图表，支持多种可视化类型
    - Traces over time (Area chart) / Traces 数量趋势（面积图）
    - Success/Error rate trends (Line chart) / 成功率/错误率趋势（折线图）
    - Latency trends (Area chart) / 延迟趋势（面积图）
    - Token usage (Bar chart) / Token 使用量（柱状图）
    - Cost trends (Area chart) / 成本趋势（面积图）
    - Status distribution (Pie chart) / 状态分布（饼图）
  - Time range selection: 6h/12h/24h/48h/72h/7d / 时间范围选择：6小时/12小时/24小时/48小时/72小时/7天
  - Interval grouping: Hour/Day / 时间粒度：小时/天

- **💰 Cost Report / 成本报表**
  - Comprehensive cost analysis by trace name and tags / 按 Trace 名称和标签的全面成本分析
  - Cost trend visualization with bar charts / 成本趋势柱状图可视化
  - Efficiency metrics (tokens per dollar) / 效率指标（每美元 Token 数）
  - Projected monthly cost estimation / 月度成本预估
  - Cost distribution pie charts / 成本分布饼图
  - Efficiency tier classification (High/Good/Avg/Low) / 效率分层（高/良好/平均/低）
  - Detailed cost breakdown table / 详细成本分解表格

- **🔍 Enhanced Trace Comparison / 增强版 Trace 对比**
  - Radar chart for performance profile comparison / 雷达图展示性能轮廓对比
  - Side-by-side bar chart comparison / 并排条形图对比
  - Step type distribution analysis / 步骤类型分布分析
  - Efficiency metrics (tokens/$) / 效率指标（Token/美元）
  - Timestamp display for each trace / 显示每个 Trace 的时间戳
  - Improved diff visualization with color-coded badges / 改进的差异可视化，带颜色标记

- **🏗️ Backend v2 API / 后端 v2 API**
  - Pluggable storage architecture (SQLite + InMemory) / 可插拔存储架构（SQLite + 内存）
  - `/api/metrics/historical` - Historical metrics with time aggregation / 历史指标，支持时间聚合
  - `/api/metrics/realtime` - Real-time performance metrics / 实时性能指标
  - `/api/traces/compare` - Trace comparison endpoint / Trace 对比端点
  - Enhanced filtering with time range support / 增强过滤，支持时间范围
  - Timezone-aware data grouping (UTC → Asia/Shanghai) / 时区感知的数据分组（UTC → 北京时间）

- **🗄️ Storage Layer Refactoring / 存储层重构**
  - Abstract BaseStorage interface / 抽象 BaseStorage 接口
  - SQLiteStorage with persistent storage and indexing / SQLiteStorage 持久化存储和索引
  - InMemoryStorage with LRU eviction / InMemoryStorage 带 LRU 淘汰
  - Parent-child trace relationship support / 父子 Trace 关系支持
  - 45/45 tests passing (100% coverage) / 45/45 测试通过（100% 覆盖率）
  - Performance validated: Save < 0.4ms, Get < 0.1ms / 性能验证：保存 < 0.4ms，查询 < 0.1ms

#### Changed / 变更

- **Navigation / 导航**
  - Added top navigation bar with Dashboard/Analytics tabs / 添加顶部导航栏，支持 Dashboard/Analytics 标签切换
  - Moved header from Dashboard to App level / 将 Header 从 Dashboard 移到 App 级别

- **Dependencies / 依赖**
  - Added `recharts` for data visualization / 添加 `recharts` 用于数据可视化
  - Added `pytz` for timezone handling / 添加 `pytz` 用于时区处理

#### Fixed / 修复

- **Timezone Issues / 时区问题**
  - Fixed incorrect time display (showing UTC as local time) / 修复时间显示错误（将 UTC 显示为本地时间）
  - All timestamps now properly converted to Asia/Shanghai (UTC+8) / 所有时间戳正确转换为北京时间（东八区）

- **Type Safety / 类型安全**
  - Fixed `traces.filter is not a function` error in CostReport / 修复 CostReport 中 `traces.filter is not a function` 错误
  - Added proper array type checking / 添加正确的数组类型检查

---

## [0.4.0] - 2026-03-19

### Added

- **CLI Tool** (`agentscope` command)
  - `agentscope setup nanobot --workspace <path>`: Automated configuration for nanobot
  - `agentscope status`: Check AgentScope backend and SDK status
  - `agentscope uninstall nanobot --workspace <path>`: Remove configuration
  - Auto-generates `sitecustomize.py` with proper SDK path
  - Generates `AGENTSCOPE_SETUP.md` with configuration instructions

- **One-Click Installation Script** (`install.sh`)
  - Automated SDK + Backend + Frontend installation
  - Detects existing nanobot workspaces
  - Creates startup scripts (`start-backend.sh`, `start-frontend.sh`, `start-all.sh`)

- **Enhanced Nanobot Instrumentation**
  - `call_sequence` tracking for prompt_build steps
  - Skill name display in monitoring (e.g., "Skills: 1 loaded (memory)")
  - Removed duplicate skill loading records
  - Environment variable support for backend URL

- **Environment Variable Configuration**
  - `AGENTSCOPE_BACKEND_URL`: Configure backend endpoint
  - `AGENTSCOPE_AUTO_INSTRUMENT`: Control auto-instrumentation
  - No more hardcoded paths in configuration

- **Documentation**
  - `INSTALL.md`: Comprehensive installation guide for end users
  - `NANOBOT_SETUP.md`: Nanobot-specific configuration guide
  - Updated `README.md` with quick start instructions

### Changed

- **Improved Setup Experience**
  - From manual plist editing to CLI automation
  - From hardcoded paths to environment variables
  - From complex manual steps to `install.sh` one-liner

- **Backend URL Configuration**
  - SDK now reads from `AGENTSCOPE_BACKEND_URL` environment variable
  - Falls back to `http://localhost:8000` if not set
  - Supports remote backend deployment

### Fixed

- **Skill Loading Accuracy**
  - Fixed showing all 17 available skills instead of actually loaded skills
  - Now correctly displays only the skills used in current request
  - Skill names are now visible in trace (e.g., "weather", "memory")

- **Duplicate Step Recording**
  - Removed duplicate `skill_loading` and `prompt_build` steps
  - Each step now correctly tagged with `call_sequence` number

## [0.3.0] - 2026-03-19

### Added

- **Non-intrusive Instrumentation Architecture** (Major)
  - New `agentscope/instrumentation/` module for runtime framework injection
  - `nanobot_instrumentor.py`: Zero-code-change integration with nanobot
    - Monkey-patches `AgentLoop.run()` for automatic initialization
    - Wraps `AgentLoop._process_message()` for trace context management
    - Automatic input/output capture
  - Supports multiple instance monitoring (6+ nanobot bots simultaneously)

- **Framework Integration Guide**
  - Complete migration guide from intrusive to non-intrusive approach
  - Production deployment best practices
  - PM2 integration examples

### Changed

- **Monitoring Architecture Overhaul**
  - Reduced nanobot `monitoring.py` from 600+ lines to 88 lines
  - Changed from intrusive code injection to delegation pattern
  - All monitoring functions now delegate to AgentScope SDK
  - Maintained backward compatibility with existing nanobot API

### Fixed

- **Tool Call Status Bug**
  - Fixed incorrect parameter mapping in `add_tool_execution_step()`
  - Tool calls now correctly show `success` status instead of `error`
  - Added intelligent error detection (checks if result starts with "Error")

### Deprecated

- **Intrusive Integration Pattern**
  - Direct modification of nanobot source files is deprecated
  - Migration to non-intrusive instrumentation recommended

## [0.2.0] - 2026-03-17

### Added

- **Comprehensive Monitoring Coverage**: 11 monitoring categories for nanobot integration
  - Prompt building monitoring (`add_prompt_building_step`)
  - Context window management (`add_context_window_step`)
  - Retry logic tracking (`add_retry_step`)
  - Rate limit monitoring (`add_rate_limit_step`)
  - Session lifecycle tracking (`add_session_lifecycle_step`)
  - Skill loading monitoring (`add_skill_loading_step`)
- **Enhanced Error Handling**: Detailed validation error reporting in backend
- **Debug Endpoint**: `/api/traces/raw` for raw trace debugging
- **Documentation**: Complete monitoring coverage guide (`docs/monitoring-coverage.md`)

### Fixed

- **Backend**: Relaxed Pydantic model constraints for `ToolCallData` and `ExecutionStepData`
  - `result` and `error` fields now accept `Any` type instead of strict `str`
  - `content` field now accepts `Any` type for flexible data
- **SDK**: Enhanced error logging in `_send_trace` with response details

### Changed

- **Backend**: Added exception handler for `RequestValidationError` with detailed output
- **Backend**: Wrapped `create_trace` in try-except for better error tracking

## [0.1.0] - 2026-03-17

### Added

- Initial release of AgentScope
- **SDK**: Core monitoring functionality with Scheme 3 (Context Manager + ContextVar)
  - `trace_scope()` context manager for creating trace contexts
  - `add_llm_call()` for recording LLM invocations
  - `add_tool_call()` for recording tool executions
  - `add_thinking()` for recording reasoning steps
  - `add_memory()` for recording memory operations
  - `instrument_llm()` for auto-instrumenting LLM clients
  - `@instrumented_tool` decorator for auto-tracing tools
- **Backend**: FastAPI-based server
  - REST API for trace collection
  - WebSocket for real-time updates
  - SQLite storage (configurable for production)
- **Frontend**: React-based web UI
  - Trace list with filtering
  - Execution chain visualization
  - Performance metrics dashboard
- **Documentation**:
  - Comprehensive integration guide
  - Architecture design document
  - nanobot integration example
- **Tests**: Edge case tests and Scheme 3 validation tests

### Features

- Framework-agnostic design supporting LangChain, AutoGen, CrewAI, and custom frameworks
- Low overhead (< 1% performance impact)
- Fault isolation (monitoring failures don't affect main business logic)
- Real-time debugging via WebSocket

[Unreleased]: https://github.com/shenchengtsi/agent-scope/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.5.0
[0.4.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.4.0
[0.3.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.3.0
[0.2.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.2.0
[0.1.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.1.0
