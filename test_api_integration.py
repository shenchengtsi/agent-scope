#!/usr/bin/env python3
"""API Integration tests for Backend v2."""

import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Import the FastAPI app
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["AGENTSCOPE_STORAGE_BACKEND"] = "memory"

from backend.main_v2 import app, get_storage
from backend.storage_manager import reset_storage

client = TestClient(app)


class TestHealth:
    """Test health check endpoints."""
    
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "storage" in data
        print(f"✅ Health check: {data}")


class TestTraceAPI:
    """Test trace CRUD operations."""
    
    def setup_method(self):
        """Reset storage before each test."""
        reset_storage()
    
    def test_create_trace(self):
        """Test creating a trace."""
        trace_data = {
            "id": "test-trace-1",
            "name": "Test Trace",
            "tags": ["test", "api"],
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "input_query": "Hello",
            "output_result": "World",
        }
        
        response = client.post("/api/traces", json=trace_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["id"] == "test-trace-1"
        print("✅ Create trace: PASSED")
    
    def test_get_trace(self):
        """Test retrieving a trace."""
        # First create a trace
        trace_data = {
            "id": "test-trace-2",
            "name": "Get Test",
            "tags": [],
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "input_query": "Test",
            "output_result": "Result",
        }
        client.post("/api/traces", json=trace_data)
        
        # Then retrieve it
        response = client.get("/api/traces/test-trace-2")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-trace-2"
        assert data["name"] == "Get Test"
        print("✅ Get trace: PASSED")
    
    def test_get_nonexistent_trace(self):
        """Test retrieving a nonexistent trace."""
        response = client.get("/api/traces/nonexistent")
        assert response.status_code == 404
        print("✅ Get nonexistent trace: PASSED")
    
    def test_list_traces(self):
        """Test listing traces."""
        # Create multiple traces
        for i in range(5):
            trace_data = {
                "id": f"list-trace-{i}",
                "name": f"Trace {i}",
                "tags": ["test"] if i % 2 == 0 else ["other"],
                "start_time": datetime.now().isoformat(),
                "status": "success" if i < 3 else "error",
                "steps": [],
                "input_query": f"Query {i}",
                "output_result": f"Result {i}",
            }
            client.post("/api/traces", json=trace_data)
        
        # List all
        response = client.get("/api/traces")
        assert response.status_code == 200
        data = response.json()
        assert len(data["traces"]) == 5
        assert "pagination" in data
        print(f"✅ List traces: {len(data['traces'])} found")
    
    def test_list_traces_with_filter(self):
        """Test listing traces with status filter."""
        # Create traces with different statuses
        for i in range(4):
            trace_data = {
                "id": f"filter-trace-{i}",
                "name": f"Filter Trace {i}",
                "tags": [],
                "start_time": datetime.now().isoformat(),
                "status": "success" if i < 2 else "error",
                "steps": [],
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace_data)
        
        # Filter by success status
        response = client.get("/api/traces?status=success")
        assert response.status_code == 200
        data = response.json()
        assert len(data["traces"]) == 2
        for trace in data["traces"]:
            assert trace["status"] == "success"
        print("✅ Filter traces by status: PASSED")
    
    def test_delete_trace(self):
        """Test deleting a trace."""
        # Create a trace
        trace_data = {
            "id": "delete-me",
            "name": "Delete Test",
            "tags": [],
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "input_query": "Test",
            "output_result": "Result",
        }
        client.post("/api/traces", json=trace_data)
        
        # Delete it
        response = client.delete("/api/traces/delete-me")
        assert response.status_code == 200
        
        # Verify it's gone
        response = client.get("/api/traces/delete-me")
        assert response.status_code == 404
        print("✅ Delete trace: PASSED")
    
    def test_create_raw_trace(self):
        """Test creating a trace with raw JSON."""
        raw_data = {
            "id": "raw-trace",
            "name": "Raw Test",
            "custom_field": "custom value",
            "nested": {"key": "value"},
            "start_time": datetime.now().isoformat(),
        }
        
        response = client.post("/api/traces/raw", json=raw_data)
        assert response.status_code == 200
        
        # Verify it was saved
        response = client.get("/api/traces/raw-trace")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "raw-trace"
        print("✅ Create raw trace: PASSED")


class TestStats:
    """Test statistics endpoints."""
    
    def setup_method(self):
        reset_storage()
    
    def test_get_stats(self):
        """Test getting storage statistics."""
        # Create some traces
        for i in range(3):
            trace_data = {
                "id": f"stats-trace-{i}",
                "name": f"Stats Trace {i}",
                "tags": [],
                "start_time": datetime.now().isoformat(),
                "status": "success",
                "steps": [],
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace_data)
        
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "backend" in data
        assert data["total_traces"] == 3
        print(f"✅ Stats: {data}")


def run_tests():
    """Run all API integration tests."""
    print("="*60)
    print("AgentScope Backend API Integration Tests")
    print("="*60)
    
    # Run tests using pytest programmatically
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "test_api_integration.py", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
