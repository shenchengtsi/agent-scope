# AgentScope 安装指南

## 快速开始

### 1. 安装 AgentScope

```bash
# 安装 SDK
pip install agentscope-monitor

# 如果使用 nanobot，安装额外依赖
pip install agentscope-monitor[nanobot]
```

### 2. 启动后端服务

```bash
# 克隆仓库
git clone https://github.com/yourusername/agentscope.git
cd agentscope

# 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 启动前端 (可选)
cd ../frontend
npm install
npm start
```

### 3. 配置 Nanobot

```bash
# 自动配置
agentscope setup nanobot --workspace ~/.nanobot

# 或者为特定实例配置
agentscope setup nanobot --workspace ~/.nanobot-zhangjuzheng --name zhangjuzheng
```

### 4. 重启 Nanobot

```bash
# 如果使用 launchctl
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist

# 或者直接重启
pkill -f nanobot
# 重新启动你的 nanobot 实例
```

### 5. 验证安装

```bash
# 检查状态
agentscope status

# 发送测试消息，然后检查
open http://localhost:3000
```

## 详细配置

### 方式一: CLI 自动配置 (推荐)

```bash
# 基础配置
agentscope setup nanobot --workspace ~/.nanobot

# 完整配置
agentscope setup nanobot \
  --workspace ~/.nanobot \
  --name xuejie \
  --backend http://localhost:8000 \
  --force
```

### 方式二: 手动配置

#### Step 1: 创建 sitecustomize.py

在你的 nanobot 工作目录创建 `sitecustomize.py`:

```python
"""Auto-load AgentScope instrumentation for nanobot."""
import sys
import os

# 如果 agentscope 不在 PYTHONPATH 中，添加它
# 替换为你的实际路径，或者使用 pip 安装后不需要这行
# sys.path.insert(0, "/path/to/agentscope/sdk")

os.environ["AGENTSCOPE_AUTO_INSTRUMENT"] = "true"
os.environ["AGENTSCOPE_BACKEND_URL"] = "http://localhost:8000"

try:
    from agentscope.instrumentation.nanobot_instrumentor import instrument
    instrument()
    print("✅ AgentScope: Instrumentation loaded", file=sys.stderr)
except Exception as e:
    print(f"⚠️ AgentScope: Failed to load: {e}", file=sys.stderr)
```

#### Step 2: 修改启动方式

**如果使用 launchd (macOS):**

编辑 `~/Library/LaunchAgents/com.nanobot.main.plist`:

```xml
<key>WorkingDirectory</key>
<string>/Users/YOUR_USERNAME/.nanobot</string>

<key>EnvironmentVariables</key>
<dict>
    <key>AGENTSCOPE_BACKEND_URL</key>
    <string>http://localhost:8000</string>
</dict>
```

**如果使用 systemd (Linux):**

编辑 service 文件:

```ini
[Service]
WorkingDirectory=/home/YOUR_USERNAME/.nanobot
Environment="AGENTSCOPE_BACKEND_URL=http://localhost:8000"
```

**如果使用 Docker:**

```dockerfile
ENV AGENTSCOPE_BACKEND_URL=http://host.docker.internal:8000
COPY sitecustomize.py /app/.nanobot/
```

#### Step 3: 重启服务

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist

# Linux
sudo systemctl restart nanobot

# Docker
docker restart nanobot-container
```

## 多实例配置

为多个 nanobot 实例配置监控:

```bash
# 徐阶 (主实例)
agentscope setup nanobot --workspace ~/.nanobot --name xuejie

# 张居正
agentscope setup nanobot --workspace ~/.nanobot-zhangjuzheng --name zhangjuzheng

# 吕芳
agentscope setup nanobot --workspace ~/.nanobot-lvfang --name lvfang

# 启动所有实例
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist
launchctl load ~/Library/LaunchAgents/com.nanobot.lvfang.plist
```

## 故障排除

### 问题: "AgentScope: Failed to load instrumentation"

**原因**: SDK 未正确安装或路径问题

**解决**:
```bash
# 验证安装
python3 -c "import agentscope; print(agentscope.__file__)"

# 重新安装
pip install --force-reinstall agentscope-monitor

# 如果使用 venv，确保安装在正确的 venv 中
/path/to/venv/bin/pip install agentscope-monitor
```

### 问题: 没有 trace 数据

**检查列表**:
1. 后端是否运行: `curl http://localhost:8000/api/health`
2. 检查 agentscope 状态: `agentscope status`
3. 查看 nanobot 日志是否有 AgentScope 相关输出
4. 确认 sitecustomize.py 在工作目录

### 问题: Backend 连接失败

**如果使用 Docker 部署 backend**:
```python
# 修改 sitecustomize.py 中的 backend URL
os.environ["AGENTSCOPE_BACKEND_URL"] = "http://host.docker.internal:8000"
```

**如果 backend 在不同机器**:
```python
os.environ["AGENTSCOPE_BACKEND_URL"] = "http://192.168.1.100:8000"
```

## 卸载

```bash
# 自动卸载
agentscope uninstall nanobot --workspace ~/.nanobot

# 手动卸载只需删除 sitecustomize.py
rm ~/.nanobot/sitecustomize.py
```

## 高级配置

### 自定义 Backend URL

```bash
agentscope setup nanobot \
  --workspace ~/.nanobot \
  --backend http://custom-server:8080
```

### 禁用自动 Instrumentation

临时禁用 (不删除配置):
```bash
export AGENTSCOPE_AUTO_INSTRUMENT=false
nanobot gateway
```

### 使用包装器脚本 (替代 sitecustomize)

创建 `run_with_monitoring.py`:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, "/path/to/agentscope/sdk")

from agentscope.instrumentation.nanobot_instrumentor import instrument
instrument()

# 启动 nanobot
import subprocess
subprocess.run(["nanobot", "gateway", "-c", "~/.nanobot/config.json"])
```

## 系统要求

- Python 3.9+
- macOS 10.15+ 或 Linux
- Nanobot 0.1.4+ (如果使用 nanobot)

## 支持的平台

| 平台 | 支持状态 | 说明 |
|------|---------|------|
| macOS | ✅ 完全支持 | 使用 launchd |
| Linux | ✅ 完全支持 | 使用 systemd |
| Windows | ⚠️ 实验性 | 使用 WSL 推荐 |
| Docker | ✅ 支持 | 需正确配置网络 |

## 获取帮助

```bash
# CLI 帮助
agentscope --help
agentscope setup --help

# 查看状态
agentscope status

# GitHub Issues
https://github.com/yourusername/agentscope/issues
```
