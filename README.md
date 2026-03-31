<div align="center">

# AgentScope

**"Observe Every Thought, Debug Every Step"**

<p align="center">
  <b>English</b> | <a href="README_CN.md">简体中文</a>
</p>

Distributed AI Agent Tracing and Monitoring System

[![PyPI version](https://badge.fury.io/py/agentscope-monitor.svg)](https://pypi.org/project/agentscope-monitor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

</div>

---

## 🌟 Features

- 🔍 **Real-time Tracing**: Monitor agent execution flow with visual call chains
- 📊 **Analytics Dashboard**: Historical trends, performance metrics, and cost analysis with 6+ chart types
- 💰 **Cost Report**: Track costs by trace name/tags, efficiency metrics (tokens/$), monthly projections
- 🔬 **Enhanced Trace Comparison**: Side-by-side comparison with radar charts and step analysis
- 🛠️ **Tool Tracking**: Record tool call arguments, results, and errors
- 🧠 **Prompt Analysis**: View complete prompt building process
- 📈 **Multi-instance Support**: Monitor multiple agent instances simultaneously
- 🔌 **Non-intrusive**: Auto-injection via monkey-patching, no business code changes
- 🗄️ **Pluggable Storage**: SQLite (persistent) or InMemory (ephemeral) storage backends

## 📸 Screenshots

### Dashboard - Real-time Monitoring
<img width="1679" alt="AgentScope Dashboard" src="https://github.com/user-attachments/assets/e33c47b3-37cb-48d4-9937-c527ee3812bb" />

### Analytics - Historical Trends
<img width="1679" alt="AgentScope Analytics" src="https://github.com/user-attachments/assets/analytics-screenshot.png" />

### Trace Comparison
<img width="1679" alt="AgentScope Trace Compare" src="https://github.com/user-attachments/assets/compare-screenshot.png" />

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/shenchengtsi/agent-scope.git
cd agentscope

# One-click installation
./install.sh

# Or manual installation
pip install -e ./sdk
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### Start Services

```bash
# Start backend v2 (with SQLite storage)
./start-backend.sh

# Or start with specific storage backend
STORAGE_TYPE=sqlite ./start-backend.sh  # Persistent storage (default)
STORAGE_TYPE=memory ./start-backend.sh  # In-memory storage

# Start frontend (in another terminal)
./start-frontend.sh

# Or start both
./start-all.sh
```

### Access the Application

- **Dashboard**: http://localhost:3001
- **Analytics**: http://localhost:3001 (click "Analytics" tab)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Configure Nanobot

```bash
# Automatic configuration
agentscope setup nanobot --workspace ~/.nanobot

# Restart nanobot
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist
```

## 🎯 What's New in v0.5.0

### 📊 Analytics Dashboard
- **6 Chart Types**: Traces trend, success/error rates, latency, token usage, cost trends, status distribution
- **Time Ranges**: 6h, 12h, 24h, 48h, 72h, 7d
- **Interval Grouping**: Hour or day granularity
- **Timezone Aware**: Automatic UTC to local time conversion

### 💰 Cost Report
- **Cost Breakdown**: By trace name and tags
- **Efficiency Metrics**: Tokens per dollar analysis
- **Monthly Projection**: Cost forecasting based on current usage
- **Efficiency Tiers**: High/Good/Average/Low classification

### 🔬 Enhanced Trace Comparison
- **Radar Charts**: Performance profile visualization
- **Side-by-Side Metrics**: Latency, tokens, cost, LLM/tool calls
- **Step Distribution**: Visual comparison of execution steps

### 🗄️ Backend v2
- **Pluggable Storage**: Choose between SQLite (persistent) or InMemory (fast)
- **Improved Performance**: <0.4ms save latency, <0.1ms query latency
- **Timezone Support**: Proper handling of UTC/local time conversion

## Supported Frameworks

| Framework | Status | Setup Command |
|-----------|--------|---------------|
| Nanobot | ✅ Fully Supported | `agentscope setup nanobot --workspace ~/.nanobot` |
| LangChain | 🚧 In Development | Coming soon |
| LlamaIndex | 🚧 In Development | Coming soon |
| Custom | ✅ Supported | Use SDK API directly |

## Project Structure

```
agentscope/
├── sdk/                    # Python SDK
│   ├── agentscope/
│   │   ├── monitor.py     # Core monitoring API
│   │   ├── models.py      # Data models
│   │   ├── storage/       # Storage backends (v0.5.0+)
│   │   │   ├── base.py
│   │   │   ├── memory.py
│   │   │   └── sqlite.py
│   │   └── instrumentation/
│   │       └── nanobot_instrumentor.py
│   └── setup.py
├── backend/               # FastAPI backend
│   ├── main_v2.py        # Backend v2 (v0.5.0+)
│   ├── storage_manager.py
│   └── requirements.txt
├── frontend/              # React frontend
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.js
│       │   └── Analytics.js    # New in v0.5.0
│       └── components/
│           ├── CostReport.js   # New in v0.5.0
│           └── TraceCompare.js # Enhanced in v0.5.0
├── install.sh             # One-click install script
└── README.md
```

## CLI Tools

```bash
# Configure nanobot
agentscope setup nanobot --workspace ~/.nanobot

# Check status
agentscope status

# Uninstall
agentscope uninstall nanobot --workspace ~/.nanobot

# Help
agentscope --help
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTSCOPE_BACKEND_URL` | Backend service URL | `http://localhost:8000` |
| `AGENTSCOPE_AUTO_INSTRUMENT` | Enable auto-instrumentation | `true` |
| `AGENTSCOPE_STORAGE_BACKEND` | Storage type (sqlite/memory) | `memory` |
| `AGENTSCOPE_DB_PATH` | SQLite database path | `./data/agentscope.db` |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v                    # SDK tests
pytest backend/tests/ -v            # Backend tests
pytest tests/storage/ -v            # Storage tests

# Code formatting
black sdk/agentscope backend/
```

## API Endpoints

### Core Endpoints
- `GET /api/traces` - List traces with filtering
- `GET /api/traces/{id}` - Get trace details
- `POST /api/traces` - Create new trace
- `DELETE /api/traces/{id}` - Delete trace

### Analytics Endpoints (v0.5.0+)
- `GET /api/metrics/historical` - Historical metrics with time aggregation
- `GET /api/metrics/realtime` - Real-time performance metrics
- `POST /api/traces/compare` - Compare two traces
- `GET /api/stats` - Storage statistics

### WebSocket
- `WS /ws` - Real-time trace updates

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Nanobot](https://github.com/clawrenceks/nanobot) - AI agent framework
