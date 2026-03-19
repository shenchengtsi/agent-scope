<div align="center">

# AgentScope

**"Observe Every Thought, Debug Every Step"**

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
- 📊 **性能分析**: LLM 调用耗时、token 使用、成本估算
- 🛠️ **工具追踪**: 记录工具调用参数和结果
- 🧠 **Prompt 分析**: 查看完整的 prompt 构建过程
- 📈 **多实例支持**: 同时监控多个 agent 实例
- 🔌 **非侵入式**: 通过 monkey-patching 自动注入，无需修改业务代码

## 📸 截图

<img width="1679" alt="AgentScope 截图 1" src="https://github.com/user-attachments/assets/e33c47b3-37cb-48d4-9937-c527ee3812bb" />

<img width="1677" alt="AgentScope 截图 2" src="https://github.com/user-attachments/assets/7bc9a7da-aa2e-4c8b-a0dc-d57f84c87545" />

<img width="1693" alt="AgentScope 截图 3" src="https://github.com/user-attachments/assets/d803142b-b0b4-4153-8539-7617aa736357" />

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
# 启动后端
./start-backend.sh

# 启动前端 (另一个终端)
./start-frontend.sh

# 或同时启动
./start-all.sh
```

### 配置 Nanobot

```bash
# 自动配置
agentscope setup nanobot --workspace ~/.nanobot

# 重启 nanobot
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist
```

访问 http://localhost:3000 查看监控面板。

## 支持的框架

| 框架 | 状态 | 说明 |
|------|------|------|
| Nanobot | ✅ 完全支持 | 使用 `agentscope setup nanobot` |
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
│   │   └── instrumentation/
│   │       └── nanobot_instrumentor.py
│   └── setup.py
├── backend/               # FastAPI 后端
│   ├── main.py
│   └── requirements.txt
├── frontend/              # React 前端
│   └── src/
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

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black sdk/agentscope
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

## 相关项目

- [Nanobot](https://github.com/clawrenceks/nanobot) - AI agent 框架
