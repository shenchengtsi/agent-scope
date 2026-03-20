#!/bin/bash
# Stop a nanobot instance
# Usage: ./stop-nanobot.sh <instance-name>
#        ./stop-nanobot.sh all  (stop all instances)

INSTANCE=$1

if [ -z "$INSTANCE" ]; then
    echo "Usage: ./stop-nanobot.sh <instance-name>"
    echo "       ./stop-nanobot.sh all"
    exit 1
fi

if [ "$INSTANCE" = "all" ]; then
    echo "Stopping all nanobot instances..."
    for name in main zhangjuzheng lvfang gaogong zhuzaihou yansong yanshifan; do
        if [ "$name" = "main" ]; then
            label="com.nanobot.main"
        else
            label="com.nanobot.$name"
        fi
        
        if launchctl list | grep -q "$label"; then
            echo "  Stopping $name..."
            launchctl stop "$label" 2>/dev/null || true
            launchctl unload "$HOME/Library/LaunchAgents/$label.plist" 2>/dev/null || true
        fi
    done
    echo "✅ All instances stopped"
else
    if [ "$INSTANCE" = "main" ]; then
        LABEL="com.nanobot.main"
    else
        LABEL="com.nanobot.$INSTANCE"
    fi
    
    PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
    
    echo "Stopping $INSTANCE..."
    launchctl stop "$LABEL" 2>/dev/null || true
    launchctl unload "$PLIST" 2>/dev/null || true
    pkill -9 -f "nanobot.*$INSTANCE" 2>/dev/null || true
    
    echo "✅ $INSTANCE stopped"
fi
