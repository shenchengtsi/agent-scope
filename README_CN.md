<div align="center">

# AgentScope

**"Observe Every Thought, Debug Every Step"**
**"洞察每一次思考，调试每一步执行"**

<p align="center">
  <a href="README.md">English</a> | <b>简体中文</b>
</p>

分布式 AI Agent 追踪与监控系统

[![PyPI version](https://badge.fury.io/py/agentscope-monitor.svg)](https://pypi.org/project/agentscope-monitor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

</div>

---

## 🌟 特性

- 🔍 **实时追踪**: 监控 agent 执行流程，可视化调用链
- 📊 **分析仪表板**: 历史趋势、性能指标和成本分析，支持6种以上图表
- 💰 **成本报表**: 按 Trace 名称/标签追踪成本，效率指标（Token/美元），月度预估
- 🔬 **增强版 Trace 对比**: 并排对比，支持雷达图和步骤分析
- 🛠️ **工具追踪**: 记录工具调用参数和结果
- 🧠 **Prompt 分析**: 查看完整的 prompt 构建过程
- 📈 **多实例支持**: 同时监控多个 agent 实例
- 🔌 **非侵入式**: 通过 monkey-patching 自动注入，无需修改业务代码
- 🗄️ **可插拔存储**: 支持 SQLite（持久化）或 InMemory（内存）存储后端

## 📸 截图

### 仪表板 - 实时监控
<img width="1679" alt="AgentScope 仪表板" src="https://github.com/user-attachments/assets/e33c47b3-37cb-48d4-9937-c527ee3812bb" />

### 分析 - 历史趋势
<img width="1679" alt="AgentScope 分析" src="https://github.com/user-attachments/assets/analytics-screenshot.png" />

### Trace 对比
<img width="1679" alt="AgentScope Trace 对比" src="https://github.com/user-attachments/assets/compare-screenshot.png" />

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/shenchengtsi/agent-scope.git
cd agentscope

# 一键安装
./install.sh

# 或手动安装
pip install -e ./sdk
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 启动服务

```bash
# 启动后端 v2（使用 SQLite 存储）
./start-backend.sh

# 或使用指定存储后端
STORAGE_TYPE=sqlite ./start-backend.sh  # 持久化存储（默认）
STORAGE_TYPE=memory ./start-backend.sh  # 内存存储

# 启动前端（另一个终端）
./start-frontend.sh

# 或同时启动
./start-all.sh
```

### 访问应用

- **仪表板**: http://localhost:3001
- **分析**: http://localhost:3001（点击"Analytics"标签）
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 配置 Nanobot

```bash
# 自动配置
agentscope setup nanobot --workspace ~/.nanobot

# 重启 nanobot
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist
```

## 🎯 v0.5.0 新功能

### 📊 分析仪表板
- **6种图表类型**: Traces 趋势、成功率/错误率、延迟、Token 使用、成本趋势、状态分布
- **时间范围**: 6小时、12小时、24小时、48小时、72小时、7天
- **时间粒度**: 小时或天
- **时区感知**: 自动 UTC 转换为本地时间

### 💰 成本报表
- **成本分解**: 按 Trace 名称和标签
- **效率指标**: 每美元 Token 数分析
- **月度预估**: 基于当前使用量的成本预测
- **效率分层**: 高/良好/平均/低 分类

### 🔬 增强版 Trace 对比
- **雷达图**: 性能轮廓可视化
- **并排指标**: 延迟、Token、成本、LLM/工具调用
- **步骤分布**: 执行步骤可视化对比

### 🗄️ 后端 v2
- **可插拔存储**: 选择 SQLite（持久化）或 InMemory（高速）
- **性能提升**: 保存 <0.4ms，查询 <0.1ms
- **时区支持**: 正确处理 UTC/本地时间转换

## 支持的框架

| 框架 | 状态 | 说明 |
|------|------|------|
| Nanobot | ✅ 完全支持 | 使用 `agentscope setup nanobot --workspace ~/.nanobot` |
| LangChain | 🚧 开发中 | 即将支持 |
| LlamaIndex | 🚧 开发中 | 即将支持 |
| 自定义 | ✅ 支持 | 使用 SDK API 直接集成 |

## 项目结构

```
agentscope/
├── sdk/                    # Python SDK
│   ├── agentscope/
│   │   ├── monitor.py     # 核心监控 API
│   │   ├── models.py      # 数据模型
│   │   ├── storage/       # 存储后端 (v0.5.0+)
│   │   │   ├── base.py
│   │   │   ├── memory.py
│   │   │   └── sqlite.py
│   │   └── instrumentation/
│   │       └── nanobot_instrumentor.py
│   └── setup.py
├── backend/               # FastAPI 后端
│   ├── main_v2.py        # 后端 v2 (v0.5.0+)
│   ├── storage_manager.py
│   └── requirements.txt
├── frontend/              # React 前端
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.js
│       │   └── Analytics.js    # v0.5.0 新增
│       └── components/
│           ├── CostReport.js   # v0.5.0 新增
│           └── TraceCompare.js # v0.5.0 增强
├── install.sh             # 一键安装脚本
└── README.md
```

## CLI 工具

```bash
# 配置 nanobot
agentscope setup nanobot --workspace ~/.nanobot

# 检查状态
agentscope status

# 卸载
agentscope uninstall nanobot --workspace ~/.nanobot

# 帮助
agentscope --help
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AGENTSCOPE_BACKEND_URL` | 后端服务地址 | `http://localhost:8000` |
| `AGENTSCOPE_AUTO_INSTRUMENT` | 自动启用监控 | `true` |
| `AGENTSCOPE_STORAGE_BACKEND` | 存储类型 (sqlite/memory) | `memory` |
| `AGENTSCOPE_DB_PATH` | SQLite 数据库路径 | `./data/agentscope.db` |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v                    # SDK 测试
pytest backend/tests/ -v            # 后端测试
pytest tests/storage/ -v            # 存储测试

# 代码格式化
black sdk/agentscope backend/
```

## API 端点

### 核心端点
- `GET /api/traces` - 列出 Traces（支持过滤）
- `GET /api/traces/{id}` - 获取 Trace 详情
- `POST /api/traces` - 创建新 Trace
- `DELETE /api/traces/{id}` - 删除 Trace

### 分析端点 (v0.5.0+)
- `GET /api/metrics/historical` - 历史指标，支持时间聚合
- `GET /api/metrics/realtime` - 实时性能指标
- `POST /api/traces/compare` - 对比两个 Traces
- `GET /api/stats` - 存储统计

### WebSocket
- `WS /ws` - 实时 Trace 更新

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史和发布说明。

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

## 相关项目

- [Nanobot](https://github.com/clawrenceks/nanobot) - AI agent 框架
