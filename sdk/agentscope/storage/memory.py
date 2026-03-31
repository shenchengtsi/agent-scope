"""In-memory storage implementation for AgentScope."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import OrderedDict

from .base import BaseStorage, StorageError

logger = logging.getLogger(__name__)


class InMemoryStorage(BaseStorage):
    """In-memory storage backend.
    
    Suitable for development and testing. Data is lost on restart.
    Uses OrderedDict to maintain insertion order and support LRU eviction.
    """
    
    def __init__(self, max_traces: int = 10000):
        """Initialize in-memory storage.
        
        Args:
            max_traces: Maximum number of traces to keep in memory
        """
        self._traces: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_traces = max_traces
        self._lock = None  # Could add threading.Lock if needed
        
    def save_trace(self, trace: Dict[str, Any]) -> str:
        """Save a trace to memory."""
        try:
            trace_id = trace.get("id")
            if not trace_id:
                raise StorageError("Trace must have an 'id' field")
            
            # Store copy to prevent external mutation
            import copy
            trace_copy = copy.deepcopy(trace)
            
            # Ensure statistics fields exist with defaults
            trace_copy.setdefault("total_tokens", 0)
            trace_copy.setdefault("total_latency_ms", 0.0)
            trace_copy.setdefault("cost_estimate", 0.0)
            trace_copy.setdefault("llm_call_count", 0)
            trace_copy.setdefault("tool_call_count", 0)
            
            self._traces[trace_id] = trace_copy
            
            # Evict oldest if over limit
            while len(self._traces) > self._max_traces:
                oldest_id, _ = self._traces.popitem(last=False)
                logger.debug(f"Evicted oldest trace: {oldest_id}")
            
            logger.debug(f"Saved trace {trace_id} to memory storage (tokens={trace_copy.get('total_tokens', 0)}, cost={trace_copy.get('cost_estimate', 0.0)})")
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to save trace: {e}")
            raise StorageError(f"Failed to save trace: {e}") from e
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a trace from memory."""
        try:
            import copy
            trace = self._traces.get(trace_id)
            return copy.deepcopy(trace) if trace else None
        except Exception as e:
            logger.error(f"Failed to get trace {trace_id}: {e}")
            raise StorageError(f"Failed to get trace: {e}") from e
    
    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List traces from memory with filtering."""
        try:
            traces = list(self._traces.values())
            
            # Apply filters
            if tags:
                traces = [
                    t for t in traces
                    if any(tag in t.get("tags", []) for tag in tags)
                ]
            
            if start_time:
                traces = [
                    t for t in traces
                    if self._parse_time(t.get("start_time")) >= start_time
                ]
            
            if end_time:
                traces = [
                    t for t in traces
                    if self._parse_time(t.get("start_time")) <= end_time
                ]
            
            if status:
                traces = [
                    t for t in traces
                    if t.get("status") == status
                ]
            
            # Sort by start_time descending
            traces.sort(
                key=lambda t: self._parse_time(t.get("start_time")) or datetime.min,
                reverse=True
            )
            
            # Apply pagination
            return traces[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list traces: {e}")
            raise StorageError(f"Failed to list traces: {e}") from e
    
    def count_traces(
        self,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count matching traces."""
        # Don't use list_traces with inf limit to avoid slice issues
        traces = list(self._traces.values())
        
        if tags:
            traces = [t for t in traces if any(tag in t.get("tags", []) for tag in tags)]
        
        if start_time:
            traces = [t for t in traces if self._parse_time(t.get("start_time")) >= start_time]
        
        if end_time:
            traces = [t for t in traces if self._parse_time(t.get("start_time")) <= end_time]
        
        if status:
            traces = [t for t in traces if t.get("status") == status]
        
        return len(traces)
    
    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace from memory."""
        try:
            if trace_id in self._traces:
                del self._traces[trace_id]
                logger.debug(f"Deleted trace {trace_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete trace {trace_id}: {e}")
            raise StorageError(f"Failed to delete trace: {e}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "backend": "memory",
            "total_traces": len(self._traces),
            "max_traces": self._max_traces,
            "storage_size_bytes": self._estimate_size(),
        }
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO format time string."""
        if not time_str:
            return None
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _estimate_size(self) -> int:
        """Estimate memory usage in bytes."""
        import sys
        try:
            return sum(
                sys.getsizeof(trace) for trace in self._traces.values()
            )
        except Exception:
            return 0
