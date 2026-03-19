#!/usr/bin/env python3
"""
Rollback script to remove AgentScope from nanobot source code.

This script restores nanobot to its original state before AgentScope integration.
Run this if you want to switch from intrusive to non-intrusive integration.

Usage:
    python rollback_nanobot_changes.py /path/to/nanobot
"""

import sys
import os
import shutil
from pathlib import Path


def remove_monitoring_py(nanobot_path: Path):
    """Remove the monitoring.py file."""
    monitoring_file = nanobot_path / "nanobot" / "agent" / "monitoring.py"
    if monitoring_file.exists():
        backup = monitoring_file.with_suffix('.py.bak')
        if backup.exists():
            shutil.move(str(backup), str(monitoring_file))
            print(f"✅ Restored monitoring.py from backup")
        else:
            monitoring_file.unlink()
            print(f"✅ Removed monitoring.py")
    else:
        print(f"⏭️  monitoring.py not found (already clean)")


def restore_loop_py(nanobot_path: Path):
    """Restore loop.py to original state."""
    loop_file = nanobot_path / "nanobot" / "agent" / "loop.py"
    backup = loop_file.with_suffix('.py.bak')
    
    if backup.exists():
        shutil.move(str(backup), str(loop_file))
        print(f"✅ Restored loop.py from backup")
        return
    
    # Manual removal if no backup
    if loop_file.exists():
        content = loop_file.read_text()
        
        # Remove imports
        lines = content.split('\n')
        cleaned_lines = []
        skip_imports = False
        
        for line in lines:
            # Skip AgentScope imports
            if 'from nanobot.agent.monitoring import' in line:
                skip_imports = True
                continue
            if skip_imports and line.strip() and not line.startswith('#'):
                skip_imports = False
            if 'AGENTSCOPE' in line or 'init_monitor' in line or 'add_tool_execution' in line:
                continue
            if '# AgentScope' in line:
                continue
            cleaned_lines.append(line)
        
        loop_file.write_text('\n'.join(cleaned_lines))
        print(f"✅ Cleaned loop.py")
    else:
        print(f"❌ loop.py not found")


def restore_registry_py(nanobot_path: Path):
    """Restore registry.py to original state."""
    registry_file = nanobot_path / "nanobot" / "agent" / "tools" / "registry.py"
    backup = registry_file.with_suffix('.py.bak')
    
    if backup.exists():
        shutil.move(str(backup), str(registry_file))
        print(f"✅ Restored registry.py from backup")
        return
    
    print(f"⏭️  registry.py: no backup found (manual check needed)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python rollback_nanobot_changes.py /path/to/nanobot")
        print("\nExample:")
        print("  python rollback_nanobot_changes.py ~/AI_Workspace2/nanobot")
        sys.exit(1)
    
    nanobot_path = Path(sys.argv[1]).resolve()
    
    if not nanobot_path.exists():
        print(f"❌ Path not found: {nanobot_path}")
        sys.exit(1)
    
    print(f"Rolling back AgentScope changes from: {nanobot_path}")
    print("=" * 60)
    
    remove_monitoring_py(nanobot_path)
    restore_loop_py(nanobot_path)
    restore_registry_py(nanobot_path)
    
    print("=" * 60)
    print("✅ Rollback complete!")
    print("\nNext steps:")
    print("  1. Switch to non-intrusive integration:")
    print("     - Use nanobot_wrapper.py")
    print("     - Or use instrumentation module")
    print("  2. Restart nanobot instances")


if __name__ == "__main__":
    main()
