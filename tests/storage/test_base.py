"""Tests for storage base interface."""

import pytest
from datetime import datetime
from agentscope.storage.base import BaseStorage, StorageError


class MockStorage(BaseStorage):
    """Mock implementation for testing base interface."""
    
    def __init__(self):
        self._data = {}
    
    def save_trace(self, trace):
        self._data[trace["id"]] = trace
        return trace["id"]
    
    def get_trace(self, trace_id):
        return self._data.get(trace_id)
    
    def list_traces(self, **kwargs):
        return list(self._data.values())
    
    def count_traces(self, **kwargs):
        return len(self._data)
    
    def delete_trace(self, trace_id):
        if trace_id in self._data:
            del self._data[trace_id]
            return True
        return False
    
    def get_stats(self):
        return {"total": len(self._data)}


class TestBaseStorage:
    """Test BaseStorage interface."""
    
    def test_save_and_get(self):
        storage = MockStorage()
        trace = {
            "id": "test-1",
            "name": "Test Trace",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        }
        
        trace_id = storage.save_trace(trace)
        assert trace_id == "test-1"
        
        retrieved = storage.get_trace("test-1")
        assert retrieved is not None
        assert retrieved["name"] == "Test Trace"
    
    def test_get_nonexistent(self):
        storage = MockStorage()
        result = storage.get_trace("nonexistent")
        assert result is None
    
    def test_delete(self):
        storage = MockStorage()
        trace = {"id": "to-delete", "name": "Delete Me", "status": "success", "start_time": datetime.now().isoformat()}
        storage.save_trace(trace)
        
        assert storage.delete_trace("to-delete") is True
        assert storage.get_trace("to-delete") is None
        assert storage.delete_trace("to-delete") is False
    
    def test_count(self):
        storage = MockStorage()
        assert storage.count_traces() == 0
        
        storage.save_trace({"id": "1", "name": "T1", "status": "success", "start_time": datetime.now().isoformat()})
        storage.save_trace({"id": "2", "name": "T2", "status": "success", "start_time": datetime.now().isoformat()})
        
        assert storage.count_traces() == 2
