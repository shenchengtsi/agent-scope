"""
Python sitecustomize for automatic AgentScope instrumentation.

Place this file in your Python site-packages directory to auto-instrument
nanobot whenever it runs.

Usage:
    # Find your site-packages
    python -c "import site; print(site.getsitepackages())"
    
    # Copy this file there
    cp sitecustomize.py /path/to/site-packages/
    
    # Set environment variable to enable
    export AGENTSCOPE_AUTO_INSTRUMENT=1
    
    # Run nanobot normally
    nanobot gateway --config ~/.nanobot/config.json
"""

import os

# Only instrument when explicitly enabled
if os.getenv("AGENTSCOPE_AUTO_INSTRUMENT") == "1":
    try:
        from agentscope.instrumentation.nanobot_instrumentor import instrument
        instrument()
    except Exception:
        pass  # Fail silently
