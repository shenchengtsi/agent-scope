"""Storage management for AgentScope backend.

Provides singleton storage instance with automatic backend selection.
"""

import os
import logging
from typing import Optional

# Add SDK to path
import sys
sdk_path = os.path.join(os.path.dirname(__file__), '..', 'sdk')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from agentscope.storage import BaseStorage, create_storage

logger = logging.getLogger(__name__)

# Singleton storage instance
_storage_instance: Optional[BaseStorage] = None


def get_storage() -> BaseStorage:
    """Get or create the singleton storage instance.
    
    Storage backend is determined by AGENTSCOPE_STORAGE_BACKEND 
    environment variable (default: memory).
    
    Returns:
        Configured storage instance
    """
    global _storage_instance
    
    if _storage_instance is None:
        backend = os.getenv("AGENTSCOPE_STORAGE_BACKEND", "memory").lower()
        
        if backend == "sqlite":
            db_path = os.getenv("AGENTSCOPE_DB_PATH", "agentscope.db")
            _storage_instance = create_storage("sqlite", db_path=db_path)
            logger.info(f"Initialized SQLite storage: {db_path}")
        else:
            _storage_instance = create_storage("memory")
            logger.info("Initialized in-memory storage")
    
    return _storage_instance


def reset_storage():
    """Reset storage instance (useful for testing)."""
    global _storage_instance
    _storage_instance = None
    logger.info("Storage instance reset")


def health_check() -> dict:
    """Check storage health.
    
    Returns:
        Health status dictionary
    """
    storage = get_storage()
    is_healthy = storage.health_check()
    
    return {
        "storage_backend": storage.__class__.__name__,
        "healthy": is_healthy,
        "stats": storage.get_stats() if is_healthy else None
    }
