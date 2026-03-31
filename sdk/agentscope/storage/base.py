"""Base storage interface for AgentScope."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class TraceNotFoundError(StorageError):
    """Raised when a trace is not found."""
    pass


class BaseStorage(ABC):
    """Abstract base class for trace storage backends.
    
    This interface defines the contract for all storage implementations,
    allowing easy swapping between in-memory, SQLite, PostgreSQL, etc.
    """
    
    @abstractmethod
    def save_trace(self, trace: Dict[str, Any]) -> str:
        """Save a trace to storage.
        
        Args:
            trace: Trace data dictionary
            
        Returns:
            trace_id: The ID of the saved trace
            
        Raises:
            StorageError: If save operation fails
        """
        pass
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a trace by ID.
        
        Args:
            trace_id: Unique trace identifier
            
        Returns:
            Trace data or None if not found
            
        Raises:
            StorageError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List traces with optional filtering.
        
        Args:
            limit: Maximum number of traces to return
            offset: Number of traces to skip
            tags: Filter by tags (OR logic)
            start_time: Filter traces after this time
            end_time: Filter traces before this time
            status: Filter by trace status
            
        Returns:
            List of trace dictionaries
            
        Raises:
            StorageError: If query fails
        """
        pass
    
    @abstractmethod
    def count_traces(
        self,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count traces matching filters.
        
        Args:
            tags: Filter by tags
            start_time: Filter traces after this time
            end_time: Filter traces before this time
            status: Filter by trace status
            
        Returns:
            Number of matching traces
        """
        pass
    
    @abstractmethod
    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace by ID.
        
        Args:
            trace_id: Trace to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with stats like total_traces, storage_size, etc.
        """
        pass
    
    def health_check(self) -> bool:
        """Check if storage is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            self.list_traces(limit=1)
            return True
        except Exception:
            return False
