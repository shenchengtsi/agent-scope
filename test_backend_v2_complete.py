#!/usr/bin/env python3
"""Complete integration tests for Backend v2."""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
os.environ["AGENTSCOPE_STORAGE_BACKEND"] = "memory"

from backend.main_v2 import app
from backend.storage_manager import reset_storage
from fastapi.testclient import TestClient

client = TestClient(app)


class TestHealthAndInfo:
    """Test health and info endpoints."""
    
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "storage" in data
        assert "timestamp" in data
        print(f"✅ Health: {data['status']}")
    
    def test_api_info(self):
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentScope API"
        assert "endpoints" in data
        print(f"✅ API Info: v{data['version']}")


class TestTraceCRUD:
    """Test trace CRUD operations."""
    
    def setup_method(self):
        reset_storage()
    
    def test_create_and_get(self):
        trace = {
            "id": "test-1",
            "name": "Test Trace",
            "tags": ["test"],
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "input_query": "Hello",
            "output_result": "World",
        }
        
        # Create
        resp = client.post("/api/traces", json=trace)
        assert resp.status_code == 200
        
        # Get
        resp = client.get("/api/traces/test-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "test-1"
        assert data["name"] == "Test Trace"
        print("✅ Create & Get")
    
    def test_list_with_filters(self):
        # Create traces
        for i in range(5):
            trace = {
                "id": f"filter-{i}",
                "name": f"Trace {i}",
                "tags": ["test"] if i % 2 == 0 else ["prod"],
                "start_time": datetime.now().isoformat(),
                "status": "success" if i < 3 else "error",
                "steps": [],
                "input_query": f"Query {i}",
                "output_result": f"Result {i}",
            }
            client.post("/api/traces", json=trace)
        
        # Test status filter
        resp = client.get("/api/traces?status=success")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["traces"]) == 3
        
        # Test tag filter
        resp = client.get("/api/traces?tag=test")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["traces"]) == 3
        
        # Test search
        resp = client.get("/api/traces?search=Trace 1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["traces"]) >= 1
        print("✅ List with filters")
    
    def test_delete(self):
        trace = {
            "id": "delete-me",
            "name": "Delete Test",
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "input_query": "Test",
            "output_result": "Result",
        }
        client.post("/api/traces", json=trace)
        
        # Delete
        resp = client.delete("/api/traces/delete-me")
        assert resp.status_code == 200
        
        # Verify deleted
        resp = client.get("/api/traces/delete-me")
        assert resp.status_code == 404
        print("✅ Delete")
    
    def test_batch_delete(self):
        # Create traces
        for i in range(3):
            trace = {
                "id": f"batch-{i}",
                "name": f"Batch {i}",
                "start_time": datetime.now().isoformat(),
                "status": "success",
                "steps": [],
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace)
        
        # Batch delete
        resp = client.post("/api/traces/batch-delete", json={
            "trace_ids": ["batch-0", "batch-1", "nonexistent"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["deleted"]) == 2
        assert len(data["failed"]) == 1
        print("✅ Batch delete")


class TestTraceRelations:
    """Test trace parent/child relations."""
    
    def setup_method(self):
        reset_storage()
    
    def test_parent_child(self):
        # Create parent
        parent = {
            "id": "parent-1",
            "name": "Parent",
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [],
            "child_trace_ids": ["child-1", "child-2"],
            "input_query": "Parent query",
            "output_result": "Parent result",
        }
        client.post("/api/traces", json=parent)
        
        # Create children
        for i in [1, 2]:
            child = {
                "id": f"child-{i}",
                "name": f"Child {i}",
                "start_time": datetime.now().isoformat(),
                "status": "success",
                "steps": [],
                "parent_trace_id": "parent-1",
                "input_query": f"Child query {i}",
                "output_result": f"Child result {i}",
            }
            client.post("/api/traces", json=child)
        
        # Get children
        resp = client.get("/api/traces/parent-1/children")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["children"]) == 2
        
        # Get parent from child
        resp = client.get("/api/traces/child-1/parent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["parent"]["id"] == "parent-1"
        print("✅ Parent/child relations")


class TestComparison:
    """Test trace comparison."""
    
    def setup_method(self):
        reset_storage()
    
    def test_compare_traces(self):
        now = datetime.now().isoformat()
        # Create two traces
        trace1 = {
            "id": "compare-1",
            "name": "Trace 1",
            "start_time": now,
            "status": "success",
            "steps": [{"id": "s1", "type": "input", "content": "test", "timestamp": now}],
            "total_latency_ms": 100.0,
            "total_tokens": 50,
            "cost_estimate": 0.01,
            "input_query": "Query 1",
            "output_result": "Result 1",
        }
        trace2 = {
            "id": "compare-2",
            "name": "Trace 2",
            "start_time": now,
            "status": "error",
            "steps": [
                {"id": "s1", "type": "input", "content": "test", "timestamp": now},
                {"id": "s2", "type": "error", "content": "error", "timestamp": now}
            ],
            "total_latency_ms": 200.0,
            "total_tokens": 100,
            "cost_estimate": 0.02,
            "input_query": "Query 2",
            "output_result": "Error",
        }
        client.post("/api/traces", json=trace1)
        client.post("/api/traces", json=trace2)
        
        # Compare
        resp = client.post("/api/traces/compare", json={
            "trace_id_1": "compare-1",
            "trace_id_2": "compare-2"
        })
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["latency_diff_ms"] == 100.0
        assert data["tokens_diff"] == 50
        assert data["steps_count_diff"] == 1
        assert data["status_changed"] is True
        assert data["trace1_status"] == "success"
        assert data["trace2_status"] == "error"
        print("✅ Trace comparison")
    
    def test_timeline(self):
        trace = {
            "id": "timeline-test",
            "name": "Timeline Test",
            "start_time": datetime.now().isoformat(),
            "status": "success",
            "steps": [
                {"id": "s1", "type": "input", "content": "in", "latency_ms": 10, "timestamp": datetime.now().isoformat()},
                {"id": "s2", "type": "llm", "content": "out", "latency_ms": 50, "timestamp": datetime.now().isoformat()},
            ],
            "total_latency_ms": 60.0,
            "input_query": "Test",
            "output_result": "Result",
        }
        client.post("/api/traces", json=trace)
        
        resp = client.get("/api/traces/timeline-test/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_steps"] == 2
        assert "timeline" in data
        assert len(data["timeline"]) == 2
        print("✅ Timeline analysis")


class TestMetrics:
    """Test metrics endpoints."""
    
    def setup_method(self):
        reset_storage()
    
    def test_realtime_metrics(self):
        # Create traces
        for i in range(10):
            trace = {
                "id": f"metric-{i}",
                "name": f"Metric {i}",
                "start_time": datetime.now().isoformat(),
                "status": "success" if i < 7 else "error",
                "steps": [],
                "total_latency_ms": float(100 + i * 10),
                "total_tokens": 50 + i * 5,
                "cost_estimate": 0.01 + i * 0.001,
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace)
        
        resp = client.get("/api/metrics/realtime")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["total_traces"] == 10
        assert abs(data["success_rate"] - 0.7) < 0.01
        assert abs(data["error_rate"] - 0.3) < 0.01
        assert data["avg_latency_ms"] > 0
        assert data["total_tokens"] > 0
        assert data["total_cost"] > 0
        print(f"✅ Realtime metrics: {data['total_traces']} traces")
    
    def test_historical_metrics(self):
        # Create traces over time
        now = datetime.now()
        for i in range(5):
            trace = {
                "id": f"hist-{i}",
                "name": f"Historical {i}",
                "start_time": (now - timedelta(hours=i)).isoformat(),
                "status": "success",
                "steps": [],
                "total_tokens": 100,
                "total_latency_ms": 100.0,
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace)
        
        resp = client.get("/api/metrics/historical?hours=24&interval=hour")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["interval"] == "hour"
        assert data["hours"] == 24
        assert len(data["data"]) > 0
        print(f"✅ Historical metrics: {len(data['data'])} data points")
    
    def test_stats(self):
        for i in range(3):
            trace = {
                "id": f"stat-{i}",
                "name": f"Stat {i}",
                "start_time": datetime.now().isoformat(),
                "status": "success" if i < 2 else "error",
                "steps": [],
                "input_query": "Test",
                "output_result": "Result",
            }
            client.post("/api/traces", json=trace)
        
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "total_traces" in data
        assert data["total_traces"] == 3
        print(f"✅ Stats: {data['total_traces']} traces")


def run_all_tests():
    """Run all tests programmatically."""
    print("="*60)
    print("Backend v2 Complete Integration Tests")
    print("="*60)
    
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
