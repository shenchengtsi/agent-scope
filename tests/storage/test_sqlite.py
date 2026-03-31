"""Tests for SQLite storage backend."""

import pytest
import tempfile
import os
from datetime import datetime
from agentscope.storage.sqlite import SQLiteStorage


class TestSQLiteStorage:
    """Test SQLiteStorage implementation."""
    
    @pytest.fixture
    def storage(self):
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        storage = SQLiteStorage(db_path)
        yield storage
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_save_and_get(self, storage):
        trace = {
            "id": "sqlite-1",
            "name": "SQLite Test",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "tags": ["test", "sqlite"],
            "metadata": {"key": "value"},
            "steps": [{"type": "llm", "content": "test"}],
        }
        
        storage.save_trace(trace)
        retrieved = storage.get_trace("sqlite-1")
        
        assert retrieved is not None
        assert retrieved["name"] == "SQLite Test"
        assert retrieved["tags"] == ["test", "sqlite"]
        assert retrieved["metadata"] == {"key": "value"}
    
    def test_persistence(self, storage):
        trace = {
            "id": "persist",
            "name": "Persistent",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        }
        
        storage.save_trace(trace)
        
        # Create new storage instance with same DB
        db_path = storage._db_path
        new_storage = SQLiteStorage(db_path)
        
        retrieved = new_storage.get_trace("persist")
        assert retrieved is not None
        assert retrieved["name"] == "Persistent"
    
    def test_list_with_filters(self, storage):
        # Add traces with different statuses
        for i in range(3):
            storage.save_trace({
                "id": f"list-{i}",
                "name": f"Trace {i}",
                "status": "success" if i < 2 else "error",
                "start_time": datetime.now().isoformat(),
            })
        
        results = storage.list_traces(status="success")
        assert len(results) == 2
    
    def test_count(self, storage):
        assert storage.count_traces() == 0
        
        for i in range(5):
            storage.save_trace({
                "id": f"count-{i}",
                "name": f"Trace {i}",
                "status": "success",
                "start_time": datetime.now().isoformat(),
            })
        
        assert storage.count_traces() == 5
    
    def test_delete(self, storage):
        storage.save_trace({
            "id": "del",
            "name": "To Delete",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        })
        
        assert storage.delete_trace("del") is True
        assert storage.get_trace("del") is None
        assert storage.delete_trace("del") is False
    
    def test_stats(self, storage):
        storage.save_trace({
            "id": "stat",
            "name": "Stats",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        })
        
        stats = storage.get_stats()
        assert stats["backend"] == "sqlite"
        assert stats["total_traces"] == 1
        assert "db_path" in stats
        assert "storage_size_bytes" in stats
    
    def test_health_check(self, storage):
        assert storage.health_check() is True
