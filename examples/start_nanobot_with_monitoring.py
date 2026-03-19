#!/usr/bin/env python3
"""
启动 nanobot 并启用 AgentScope 监控

Usage:
    python start_nanobot_with_monitoring.py [nanobot_args...]
"""

import sys
import os

# 添加 agentscope 到路径
sys.path.insert(0, '/Users/samsonchoi/agent-scope/sdk')

# 启用 instrumentation
os.environ["AGENTSCOPE_AUTO_INSTRUMENT"] = "true"

# 在导入 nanobot 之前执行 instrumentation
from agentscope.instrumentation.nanobot_instrumentor import instrument

print("🔧 AgentScope: Starting instrumentation...")
try:
    instrument()
    print("✅ AgentScope: Instrumentation enabled")
except Exception as e:
    print(f"⚠️ AgentScope: Instrumentation failed: {e}")
    import traceback
    traceback.print_exc()

# 现在导入并启动 nanobot
print("🚀 Starting nanobot...")
try:
    # 尝试不同的 nanobot 入口点
    try:
        from nanobot.cli import main as nanobot_main
        nanobot_main()
    except ImportError:
        try:
            from nanobot.__main__ import main as nanobot_main
            nanobot_main()
        except ImportError:
            # 直接导入并运行 AgentLoop
            import asyncio
            from nanobot.agent.loop import AgentLoop
            from nanobot.bus.queue import MessageBus
            from nanobot.providers.registry import get_provider
            from nanobot.config.loader import load_config
            from pathlib import Path
            
            config = load_config()
            bus = MessageBus()
            provider = get_provider(config.model)
            
            loop = AgentLoop(
                bus=bus,
                provider=provider,
                workspace=Path(config.workspace),
                model=config.model.name,
                temperature=config.model.temperature,
                max_tokens=config.model.max_tokens,
            )
            
            asyncio.run(loop.run())
            
except KeyboardInterrupt:
    print("\n👋 Goodbye!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
