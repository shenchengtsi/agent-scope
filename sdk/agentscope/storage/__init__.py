"""Storage layer for AgentScope.

Provides pluggable storage backends for trace persistence.
"""

from .base import BaseStorage, StorageError, TraceNotFoundError
from .memory import InMemoryStorage
from .sqlite import SQLiteStorage

__all__ = [
    "BaseStorage",
    "StorageError", 
    "TraceNotFoundError",
    "InMemoryStorage",
    "SQLiteStorage",
    "create_storage",
]


def create_storage(backend: str = "memory", **kwargs) -> BaseStorage:
    """Factory function to create storage backend.
    
    Args:
        backend: Storage backend type ("memory", "sqlite")
        **kwargs: Backend-specific configuration
        
    Returns:
        Configured storage instance
        
    Raises:
        ValueError: If backend type is not supported
    """
    backend = backend.lower()
    
    if backend == "memory":
        return InMemoryStorage()
    elif backend == "sqlite":
        db_path = kwargs.get("db_path", "agentscope.db")
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unsupported storage backend: {backend}. "
                        f"Supported: memory, sqlite")
