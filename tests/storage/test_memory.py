"""Tests for in-memory storage backend."""

import pytest
from datetime import datetime
from agentscope.storage.memory import InMemoryStorage


class TestInMemoryStorage:
    """Test InMemoryStorage implementation."""
    
    @pytest.fixture
    def storage(self):
        return InMemoryStorage()
    
    def test_save_and_get(self, storage):
        trace = {
            "id": "mem-1",
            "name": "Memory Test",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "tags": ["test", "memory"],
        }
        
        storage.save_trace(trace)
        retrieved = storage.get_trace("mem-1")
        
        assert retrieved is not None
        assert retrieved["name"] == "Memory Test"
        assert retrieved["tags"] == ["test", "memory"]
    
    def test_list_with_pagination(self, storage):
        # Add 5 traces
        for i in range(5):
            storage.save_trace({
                "id": f"trace-{i}",
                "name": f"Trace {i}",
                "status": "success",
                "start_time": datetime.now().isoformat(),
            })
        
        # Test limit
        results = storage.list_traces(limit=3)
        assert len(results) == 3
        
        # Test offset
        results = storage.list_traces(limit=2, offset=2)
        assert len(results) == 2
    
    def test_filter_by_status(self, storage):
        storage.save_trace({
            "id": "success-1",
            "name": "Success",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        })
        storage.save_trace({
            "id": "error-1",
            "name": "Error",
            "status": "error",
            "start_time": datetime.now().isoformat(),
        })
        
        results = storage.list_traces(status="success")
        assert len(results) == 1
        assert results[0]["id"] == "success-1"
    
    def test_filter_by_tags(self, storage):
        storage.save_trace({
            "id": "tagged",
            "name": "Tagged",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "tags": ["important", "production"],
        })
        storage.save_trace({
            "id": "untagged",
            "name": "Untagged",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "tags": [],
        })
        
        results = storage.list_traces(tags=["important"])
        assert len(results) == 1
        assert results[0]["id"] == "tagged"
    
    def test_max_traces_eviction(self):
        storage = InMemoryStorage(max_traces=3)
        
        # Add 5 traces (max is 3)
        for i in range(5):
            storage.save_trace({
                "id": f"evict-{i}",
                "name": f"Trace {i}",
                "status": "success",
                "start_time": datetime.now().isoformat(),
            })
        
        # Should only have 3 most recent
        assert storage.count_traces() == 3
        assert storage.get_trace("evict-0") is None  # Evicted
        assert storage.get_trace("evict-4") is not None  # Kept
    
    def test_stats(self, storage):
        storage.save_trace({
            "id": "stat-1",
            "name": "Stat Test",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        })
        
        stats = storage.get_stats()
        assert stats["backend"] == "memory"
        assert stats["total_traces"] == 1
        assert stats["max_traces"] == 10000
