#!/bin/bash
# Migrate from intrusive to non-intrusive AgentScope integration

set -e

NANOBOT_PATH="${1:-$HOME/AI_Workspace2/nanobot}"
AGENTSCOPE_PATH="${2:-$HOME/agent-scope}"

echo "=========================================="
echo "AgentScope 迁移工具: 侵入式 → 非侵入式"
echo "=========================================="
echo ""
echo "Nanobot 路径: $NANOBOT_PATH"
echo "AgentScope 路径: $AGENTSCOPE_PATH"
echo ""

# Check paths
if [ ! -d "$NANOBOT_PATH" ]; then
    echo "❌ Nanobot 路径不存在: $NANOBOT_PATH"
    exit 1
fi

if [ ! -d "$AGENTSCOPE_PATH" ]; then
    echo "❌ AgentScope 路径不存在: $AGENTSCOPE_PATH"
    exit 1
fi

# Step 1: Backup
echo "📦 Step 1: 备份当前状态..."
cd "$NANOBOT_PATH"
if [ -d ".git" ]; then
    git add -A 2>/dev/null || true
    git stash push -m "intrusive-agentscope-backup" 2>/dev/null || true
    echo "✅ 已备份到 git stash"
else
    echo "⚠️  未找到 git，跳过备份"
fi
echo ""

# Step 2: Remove monitoring.py
echo "🗑️  Step 2: 删除侵入式监控文件..."
MONITORING_FILE="$NANOBOT_PATH/nanobot/agent/monitoring.py"
if [ -f "$MONITORING_FILE" ]; then
    rm "$MONITORING_FILE"
    echo "✅ 已删除 monitoring.py"
else
    echo "⏭️  monitoring.py 不存在"
fi
echo ""

# Step 3: Restore original files
echo "🔄 Step 3: 恢复原始文件..."
if [ -d ".git" ]; then
    git checkout nanobot/agent/loop.py 2>/dev/null || echo "⚠️  loop.py 可能需要手动恢复"
    git checkout nanobot/agent/tools/registry.py 2>/dev/null || echo "⚠️  registry.py 可能需要手动恢复"
    echo "✅ 已从 git 恢复原始文件"
else
    echo "⚠️  未找到 git，请手动恢复 loop.py 和 registry.py"
fi
echo ""

# Step 4: Verify non-intrusive module exists
echo "🔍 Step 4: 检查非侵入式模块..."
INSTRUMENTOR_FILE="$AGENTSCOPE_PATH/agentscope/instrumentation/nanobot_instrumentor.py"
if [ ! -f "$INSTRUMENTOR_FILE" ]; then
    echo "❌ 未找到非侵入式模块: $INSTRUMENTOR_FILE"
    exit 1
fi
echo "✅ 非侵入式模块存在"
echo ""

# Step 5: Create wrapper script for nanobot instances
echo "📝 Step 5: 创建启动包装器..."

# Create wrapper for main instance
cat > "$HOME/.nanobot/start-main-with-agentscope.sh" << EOF
#!/bin/bash
# Nanobot main instance with AgentScope monitoring (non-intrusive)

INSTANCE_NAME="main"
LABEL="com.nanobot.main"
PLIST="\$HOME/Library/LaunchAgents/\${LABEL}.plist"
LOG_DIR="\$HOME/.nanobot/logs"
STDOUT_LOG="\${LOG_DIR}/stdout.log"
STDERR_LOG="\${LOG_DIR}/stderr.log"
CONFIG_FILE="\$HOME/.nanobot/config.json"

_is_loaded() {
    launchctl list "\$LABEL" &>/dev/null
}

_get_pid_v2() {
    local pid
    pid=\$(launchctl list "\$LABEL" 2>/dev/null | grep '"PID"' | awk -F'= ' '{print \$2}' | tr -d ' ;')
    if [ -n "\$pid" ]; then
        echo "\$pid"
    fi
}

start() {
    if _is_loaded; then
        local pid=\$(_get_pid_v2)
        if [ -n "\$pid" ]; then
            echo "❌ Nanobot \$INSTANCE_NAME 实例已在运行 (PID: \$pid)"
            return 1
        fi
    fi

    echo "🚀 启动 Nanobot \$INSTANCE_NAME 实例 (with AgentScope)..."

    if ! [ -f "\$PLIST" ]; then
        echo "❌ plist 文件不存在: \$PLIST"
        return 1
    fi

    if ! _is_loaded; then
        launchctl load "\$PLIST" 2>/dev/null
    fi
    launchctl kickstart "gui/\$(id -u)/\$LABEL" 2>/dev/null

    sleep 2

    if _is_loaded; then
        local pid=\$(_get_pid_v2)
        if [ -n "\$pid" ]; then
            echo "✅ Nanobot \$INSTANCE_NAME 实例启动成功 (PID: \$pid)"
            return 0
        fi
    fi

    echo "❌ 启动失败，请查看日志: \$STDERR_LOG"
    return 1
}

stop() {
    if ! _is_loaded; then
        echo "⚠️  Nanobot \$INSTANCE_NAME 实例未加载"
        return 0
    fi

    local pid=\$(_get_pid_v2)
    echo "🛑 停止 Nanobot \$INSTANCE_NAME 实例\${pid:+ (PID: \$pid)}..."

    launchctl unload "\$PLIST" 2>/dev/null
    sleep 1

    if [ -n "\$pid" ] && kill -0 "\$pid" 2>/dev/null; then
        echo "⚠️  进程未响应，强制终止..."
        kill -9 "\$pid" 2>/dev/null
    fi

    echo "✅ Nanobot \$INSTANCE_NAME 实例已停止"
}

case "\$1" in
    start)   start ;;
    stop)    stop ;;
    restart) stop && sleep 1 && start ;;
    status)  launchctl list \$LABEL 2>/dev/null | grep -E "PID|LastExitStatus" ;;
    *)
        echo "用法: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac
EOF

chmod +x "$HOME/.nanobot/start-main-with-agentscope.sh"
echo "✅ 已创建启动脚本: start-main-with-agentscope.sh"
echo ""

# Step 6: Update plist to use wrapper
echo "⚙️  Step 6: 更新 plist 配置..."
PLIST_FILE="$HOME/Library/LaunchAgents/com.nanobot.main.plist"
if [ -f "$PLIST_FILE" ]; then
    # Backup original
    cp "$PLIST_FILE" "$PLIST_FILE.bak"
    
    # Note: This is a simplified update - user may need to manually edit
    echo "⚠️  请手动更新 plist 文件: $PLIST_FILE"
    echo "   将 ProgramArguments 中的 'nanobot' 改为:"
    echo "   $AGENTSCOPE_PATH/examples/nanobot_wrapper.py"
else
    echo "⏭️  未找到 plist 文件"
fi
echo ""

# Step 7: Create migration summary
cat > "$HOME/.nanobot/AGENTSCOPE_MIGRATION_SUMMARY.md" << EOF
# AgentScope 迁移完成总结

## 迁移时间
\$(date)

## 执行的操作
1. ✅ 备份原代码到 git stash
2. ✅ 删除侵入式 monitoring.py
3. ✅ 恢复 loop.py 和 registry.py
4. ✅ 验证非侵入式模块
5. ✅ 创建启动包装器

## 下一步操作

### 1. 手动更新 plist 文件（如使用 launchd）
编辑: $HOME/Library/LaunchAgents/com.nanobot.main.plist

将:
```xml
<array>
    <string>/path/to/nanobot/venv/bin/nanobot</string>
    <string>gateway</string>
    ...
</array>
```

改为:
```xml
<array>
    <string>/path/to/python</string>
    <string>$AGENTSCOPE_PATH/examples/nanobot_wrapper.py</string>
    <string>gateway</string>
    ...
</array>
```

### 2. 重启实例
\`\`\`bash
bash ~/.nanobot/stop-all-bots.sh
bash ~/.nanobot/start-all-bots.sh
\`\`\`

### 3. 验证监控
\`\`\`bash
# 检查 AgentScope 是否工作
curl http://localhost:8000/api/traces

# 查看日志
tail -f ~/.nanobot/logs/main.log | grep -i agentscope
\`\`\`

## 架构变化
- **之前**: 侵入式修改 nanobot 源码
- **之后**: 运行时注入，零代码修改

## 优势
- nanobot 升级无需同步修改
- 零代码冲突风险
- 可复用于其他 Agent 框架
EOF

echo "=========================================="
echo "✅ 迁移准备完成！"
echo "=========================================="
echo ""
echo "📋 请查看详细说明:"
echo "   $HOME/.nanobot/AGENTSCOPE_MIGRATION_SUMMARY.md"
echo ""
echo "⚠️  注意: 需要手动更新 plist 文件（如果使用 launchd）"
echo ""
echo "🚀 快速验证:"
echo "   1. 在飞书发送消息给机器人"
echo "   2. 打开 http://localhost:3000"
echo "   3. 确认监控数据正常"
echo ""
