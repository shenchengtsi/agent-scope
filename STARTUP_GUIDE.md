# Nanobot + AgentScope 启动指南

## 快速启动（推荐）

### 1. 一键启动所有实例

```bash
cd ~/agent-scope
./scripts/start-all-nanobots.sh
```

### 2. 启动单个实例

```bash
# 徐阶 (main)
launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist

# 其他实例（张居正、吕芳等）
launchctl load ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist
```

## 标准启动流程

### 步骤 1: 检查现有进程（避免重复启动）

```bash
# 查看当前运行的 nanobot 实例
ps aux | grep -E "agentscope_runner|nanobot gateway" | grep -v grep

# 或按名称查看
launchctl list | grep nanobot
```

**⚠️ 重要**: 如果实例已在运行，不要重复启动！

### 步骤 2: 停止旧实例（如有必要）

```bash
# 停止特定实例
launchctl stop com.nanobot.zhangjuzheng
launchctl unload ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist

# 确认已停止
ps aux | grep zhangjuzheng | grep -v grep  # 应该无输出
```

### 步骤 3: 清空日志（便于验证）

```bash
# 清空 stderr 日志
> ~/.nanobot-zhangjuzheng/logs/stderr.log
```

### 步骤 4: 启动实例

```bash
launchctl load ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist
```

### 步骤 5: 验证启动（30秒内完成）

```bash
# 1. 检查进程
launchctl list | grep zhangjuzheng

# 2. 检查端口
lsof -Pi :18801 -sTCP:LISTEN

# 3. 检查 AgentScope 是否加载
grep "AgentScope" ~/.nanobot-zhangjuzheng/logs/stderr.log
```

**预期输出**:
```
99372	0	com.nanobot.zhangjuzheng
Python  99372 ... TCP *:18801 (LISTEN)
AgentScope: ContextBuilder instrumented
AgentScope: AgentLoop._run_agent_loop instrumented
AgentScope: AgentLoop instrumented
```

## 验证监控生效

### 方法 1: 查看日志

```bash
# 实时查看日志
tail -f ~/.nanobot-zhangjuzheng/logs/stderr.log | grep -i "agentscope\|skill\|prompt"
```

### 方法 2: 查看 AgentScope 面板

1. 打开 http://localhost:3000
2. 发送测试消息给实例
3. 检查 trace 是否出现

### 方法 3: API 检查

```bash
# 检查 traces 数量
curl -s http://localhost:8000/api/traces | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total traces: {len(data.get(\"traces\", []))}')
for t in data.get('traces', [])[:3]:
    print(f'  - {t.get(\"name\")}: {len(t.get(\"steps\", []))} steps')
"
```

## 各实例启动命令速查

| 实例 | 启动命令 | 端口 | 验证命令 |
|------|---------|------|---------|
| 徐阶 (main) | `launchctl load ~/Library/LaunchAgents/com.nanobot.main.plist` | 18800 | `lsof -Pi :18800 -sTCP:LISTEN` |
| 张居正 | `launchctl load ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist` | 18801 | `lsof -Pi :18801 -sTCP:LISTEN` |
| 吕芳 | `launchctl load ~/Library/LaunchAgents/com.nanobot.lvfang.plist` | 18802 | `lsof -Pi :18802 -sTCP:LISTEN` |
| 朱载垕 | `launchctl load ~/Library/LaunchAgents/com.nanobot.zhuzaihou.plist` | 18803 | `lsof -Pi :18803 -sTCP:LISTEN` |
| 严世蕃 | `launchctl load ~/Library/LaunchAgents/com.nanobot.yanshifan.plist` | 18804 | `lsof -Pi :18804 -sTCP:LISTEN` |
| 严嵩 | `launchctl load ~/Library/LaunchAgents/com.nanobot.yansong.plist` | 18805 | `lsof -Pi :18805 -sTCP:LISTEN` |
| 高拱 | `launchctl load ~/Library/LaunchAgents/com.nanobot.gaogong.plist` | 18806 | `lsof -Pi :18806 -sTCP:LISTEN` |

## 停止实例

```bash
# 停止单个实例
launchctl stop com.nanobot.zhangjuzheng
launchctl unload ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist

# 停止所有实例
for name in main zhangjuzheng lvfang gaogong zhuzaihou yansong yanshifan; do
    launchctl stop com.nanobot.$name 2>/dev/null
    launchctl unload ~/Library/LaunchAgents/com.nanobot.$name.plist 2>/dev/null
done
```

## 故障排除

### 问题: AgentScope 未加载

**症状**: stderr 日志中没有 AgentScope 相关信息

**解决**:
1. 检查 plist 配置是否为 sitecustomize.py 方式
2. 确认 sitecustomize.py 存在且内容正确
3. 重启实例

### 问题: 重复实例

**症状**: 同一实例有多个进程

**解决**:
```bash
# 强制停止所有相关进程
pkill -9 -f "nanobot.*zhangjuzheng"
# 然后重新启动
launchctl load ~/Library/LaunchAgents/com.nanobot.zhangjuzheng.plist
```

### 问题: 端口被占用

**症状**: 端口已在监听但实例无法启动

**解决**:
```bash
# 查找占用端口的进程
lsof -Pi :18801 -sTCP:LISTEN

# 杀死占用进程
kill -9 <PID>
```

## 自动化脚本

### 创建启动脚本

```bash
#!/bin/bash
# start-nanobot.sh

INSTANCE=$1

if [ -z "$INSTANCE" ]; then
    echo "Usage: ./start-nanobot.sh <instance-name>"
    echo "Examples: main, zhangjuzheng, lvfang, ..."
    exit 1
fi

PLIST="~/Library/LaunchAgents/com.nanobot.$INSTANCE.plist"

# 检查是否已在运行
if launchctl list | grep -q "com.nanobot.$INSTANCE"; then
    echo "⚠️ $INSTANCE is already running!"
    echo "To restart, run: ./restart-nanobot.sh $INSTANCE"
    exit 1
fi

# 清空日志
> ~/.nanobot-$INSTANCE/logs/stderr.log 2>/dev/null

# 启动
launchctl load $PLIST

echo "Starting $INSTANCE..."
sleep 3

# 验证
if launchctl list | grep -q "com.nanobot.$INSTANCE"; then
    echo "✅ $INSTANCE started successfully"
    if grep -q "AgentScope" ~/.nanobot-$INSTANCE/logs/stderr.log 2>/dev/null; then
        echo "✅ AgentScope monitoring enabled"
    else
        echo "⚠️ AgentScope may not be loaded, check logs"
    fi
else
    echo "❌ Failed to start $INSTANCE"
fi
```

## 总结

启动前 → 检查是否已运行 → 清空日志 → 启动 → 验证 AgentScope

记住口诀：**一查二清三启四验**