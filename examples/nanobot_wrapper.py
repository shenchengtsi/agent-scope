#!/usr/bin/env python3
"""
Zero-code-change nanobot wrapper with AgentScope monitoring.

This script wraps nanobot without modifying its source code.
Simply run this instead of 'nanobot gateway'.

Usage:
    python nanobot_wrapper.py gateway --config ~/.nanobot/config.json
    
Or use as a drop-in replacement:
    alias nanobot='python /path/to/nanobot_wrapper.py'
"""

import sys
import os

# Add agentscope to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import and enable instrumentation BEFORE importing nanobot
from agentscope.instrumentation.nanobot_instrumentor import instrument
instrument()

# Now import and run nanobot normally
from nanobot.cli.commands import app

if __name__ == "__main__":
    app()
