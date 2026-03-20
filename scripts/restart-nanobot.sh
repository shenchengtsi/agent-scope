#!/bin/bash
# Restart a nanobot instance with AgentScope monitoring
# Usage: ./restart-nanobot.sh <instance-name>

set -e

INSTANCE=$1

if [ -z "$INSTANCE" ]; then
    echo "Usage: ./restart-nanobot.sh <instance-name>"
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

echo "=== Restarting $INSTANCE ==="
echo ""

# Stop if running
if launchctl list | grep -q "$LABEL"; then
    echo "Stopping $INSTANCE..."
    launchctl stop "$LABEL" 2>/dev/null || true
    launchctl unload "$PLIST" 2>/dev/null || true
    sleep 2
fi

# Kill any remaining processes
pkill -9 -f "nanobot.*$INSTANCE" 2>/dev/null || true
sleep 1

# Clear logs
echo "Clearing logs..."
> "$DIR/logs/stderr.log" 2>/dev/null || true
> "$DIR/logs/stdout.log" 2>/dev/null || true

# Start
echo "Starting $INSTANCE..."
launchctl load "$PLIST"

sleep 3

# Verify
if launchctl list | grep -q "$LABEL"; then
    PID=$(launchctl list | grep "$LABEL" | awk '{print $1}')
    echo "✅ $INSTANCE restarted (PID $PID)"
else
    echo "❌ Failed to restart $INSTANCE"
    exit 1
fi
