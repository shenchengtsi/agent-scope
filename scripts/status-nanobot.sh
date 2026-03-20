#!/bin/bash
# Check status of nanobot instances with AgentScope

echo "=== Nanobot + AgentScope Status ==="
echo ""

# Check AgentScope backend
echo "AgentScope Backend:"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "  ✅ http://localhost:8000"
else
    echo "  ❌ http://localhost:8000 (not responding)"
fi

# Check AgentScope frontend
echo ""
echo "AgentScope Frontend:"
if curl -s -I http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✅ http://localhost:3000"
else
    echo "  ❌ http://localhost:3000 (not responding)"
fi

# Check instances
echo ""
echo "Nanobot Instances:"
echo ""
printf "%-12s %-10s %-8s %-15s %s\n" "Name" "Status" "PID" "AgentScope" "Port"
echo "----------------------------------------------------------------"

for pair in "徐阶|main|18800" "张居正|zhangjuzheng|18801" "吕芳|lvfang|18802" "朱载垕|zhuzaihou|18803" "严世蕃|yanshifan|18804" "严嵩|yansong|18805" "高拱|gaogong|18806"; do
    IFS='|' read -r name instance port <<< "$pair"
    
    if [ "$instance" = "main" ]; then
        label="com.nanobot.main"
        dir="$HOME/.nanobot"
    else
        label="com.nanobot.$instance"
        dir="$HOME/.nanobot-$instance"
    fi
    
    # Check process
    pid=$(launchctl list | grep "$label" | awk '{print $1}' 2>/dev/null)
    if [ -n "$pid" ] && [ "$pid" != "-" ]; then
        status="✅"
        
        # Check AgentScope
        if [ -f "$dir/logs/stderr.log" ] && grep -q "AgentScope" "$dir/logs/stderr.log" 2>/dev/null; then
            agentscope="✅"
        else
            agentscope="❌"
        fi
        
        printf "%-12s %-10s %-8s %-15s %s\n" "$name" "$status" "$pid" "$agentscope" "$port"
    else
        printf "%-12s %-10s %-8s %-15s %s\n" "$name" "❌" "-" "-" "$port"
    fi
done

echo ""
echo "Traces:"
curl -s http://localhost:8000/api/traces | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    traces = data.get('traces', [])
    print(f'  Total: {len(traces)} traces')
except:
    print('  Unable to fetch traces')
" 2>/dev/null

echo ""
echo "Legend:"
echo "  ✅ Running / Enabled"
echo "  ❌ Stopped / Not loaded"
