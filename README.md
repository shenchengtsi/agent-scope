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
- 📊 **Performance Analysis**: LLM latency, token usage, cost estimation
- 🛠️ **Tool Tracking**: Record tool call arguments, results, and errors
- 🧠 **Prompt Analysis**: View complete prompt building process
- 📈 **Multi-instance Support**: Monitor multiple agent instances simultaneously
- 🔌 **Non-intrusive**: Auto-injection via monkey-patching, no business code changes

## 📸 Screenshots

<img width="1679" alt="AgentScope Screenshot 1" src="https://github.com/user-attachments/assets/e33c47b3-37cb-48d4-9937-c527ee3812bb" />

<img width="1677" alt="AgentScope Screenshot 2" src="https://github.com/user-attachments/assets/7bc9a7da-aa2e-4c8b-a0dc-d57f84c87545" />

<img width="1693" alt="AgentScope Screenshot 3" src="https://github.com/user-attachments/assets/d803142b-b0b4-4153-8539-7617aa736357" />

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
# Start backend
./start-backend.sh

# Start frontend (in another terminal)
./start-frontend.sh

# Or start both
./start-all.sh
```

### Configure Nanobot

```bash
# Automatic configuration
agentscope setup nanobot --workspace ~/.nanobot

# Restart nanobot
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist
```

Visit http://localhost:3000 to view the dashboard.

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
│   │   └── instrumentation/
│   │       └── nanobot_instrumentor.py
│   └── setup.py
├── backend/               # FastAPI backend
│   ├── main.py
│   └── requirements.txt
├── frontend/              # React frontend
│   └── src/
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

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black sdk/agentscope
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Nanobot](https://github.com/clawrenceks/nanobot) - AI agent framework
