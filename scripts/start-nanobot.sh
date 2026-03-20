#!/bin/bash
# Start a nanobot instance with AgentScope monitoring
# Usage: ./start-nanobot.sh <instance-name>
# Example: ./start-nanobot.sh zhangjuzheng

set -e

INSTANCE=$1

if [ -z "$INSTANCE" ]; then
    echo "Usage: ./start-nanobot.sh <instance-name>"
    echo ""
    echo "Available instances:"
    echo "  main          - 徐阶 (main instance)"
    echo "  zhangjuzheng  - 张居正"
    echo "  lvfang        - 吕芳"
    echo "  gaogong       - 高拱"
    echo "  zhuzaihou     - 朱载垕"
    echo "  yansong       - 严嵩"
    echo "  yanshifan     - 严世蕃"
    echo ""
    exit 1
fi

# Map instance name to label
if [ "$INSTANCE" = "main" ]; then
    LABEL="com.nanobot.main"
    DIR="$HOME/.nanobot"
else
    LABEL="com.nanobot.$INSTANCE"
    DIR="$HOME/.nanobot-$INSTANCE"
fi

PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

# Check if plist exists
if [ ! -f "$PLIST" ]; then
    echo "❌ Plist not found: $PLIST"
    exit 1
fi

echo "=== Starting $INSTANCE ==="
echo ""

# Check if already running
if launchctl list | grep -q "$LABEL"; then
    echo "⚠️  $INSTANCE is already running!"
    echo ""
    echo "To check status:"
    echo "  launchctl list | grep $LABEL"
    echo ""
    echo "To restart:"
    echo "  ./restart-nanobot.sh $INSTANCE"
    exit 1
fi

# Clear logs for verification
if [ -d "$DIR/logs" ]; then
    echo "Clearing logs..."
    > "$DIR/logs/stderr.log" 2>/dev/null || true
    > "$DIR/logs/stdout.log" 2>/dev/null || true
fi

# Start the instance
echo "Loading $LABEL..."
launchctl load "$PLIST"

echo ""
echo "Waiting for initialization..."
sleep 3

# Verify startup
echo ""
echo "=== Verification ==="

# Check process
if launchctl list | grep -q "$LABEL"; then
    PID=$(launchctl list | grep "$LABEL" | awk '{print $1}')
    echo "✅ Process running: PID $PID"
else
    echo "❌ Process not found"
    exit 1
fi

# Check AgentScope
sleep 2
if [ -f "$DIR/logs/stderr.log" ]; then
    if grep -q "AgentScope" "$DIR/logs/stderr.log" 2>/dev/null; then
        echo "✅ AgentScope monitoring enabled"
        grep "AgentScope" "$DIR/logs/stderr.log" | tail -1 | sed 's/^/   /'
    else
        echo "⚠️  AgentScope may not be loaded"
        echo "   Check logs: tail -f $DIR/logs/stderr.log"
    fi
fi

echo ""
echo "=== $INSTANCE started successfully ==="
