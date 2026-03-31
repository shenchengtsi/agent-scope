#!/usr/bin/env python3
"""End-to-end test simulating real-world usage."""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
os.environ["AGENTSCOPE_STORAGE_BACKEND"] = "sqlite"
os.environ["AGENTSCOPE_DB_PATH"] = "/tmp/agentscope_e2e.db"

from fastapi.testclient import TestClient
from backend.main_v2 import app
from backend.storage_manager import reset_storage

client = TestClient(app)


def test_complete_workflow():
    """Test a complete agent workflow with parent-child traces."""
    print("\n" + "="*60)
    print("End-to-End Test: Complete Agent Workflow")
    print("="*60)
    
    reset_storage()
    
    # Step 1: Create a parent trace
    print("\n📋 Step 1: Creating parent trace...")
    now = datetime.now().isoformat()
    parent_trace = {
        "id": "agent-main-001",
        "name": "Customer Support Agent",
        "tags": ["production", "support"],
        "start_time": now,
        "status": "in_progress",
        "input_query": "Help customer with refund",
        "output_result": "",
        "steps": [
            {"id": "s1", "type": "input", "content": "Customer wants refund", "timestamp": now},
        ],
        "child_trace_ids": ["agent-sub-001"],
    }
    
    resp = client.post("/api/traces", json=parent_trace)
    assert resp.status_code == 200
    print(f"✅ Parent trace created")
    
    # Step 2: Create child trace
    print("\n🔍 Step 2: Creating child trace...")
    child = {
        "id": "agent-sub-001",
        "name": "Search Agent",
        "tags": ["sub-agent"],
        "start_time": now,
        "status": "success",
        "input_query": "Search order",
        "output_result": "Order found",
        "parent_trace_id": "agent-main-001",
        "steps": [{"id": "s1", "type": "tool_call", "content": "Searching...", "timestamp": now}],
    }
    
    resp = client.post("/api/traces", json=child)
    assert resp.status_code == 200
    print(f"✅ Child trace created")
    
    # Step 3: Complete parent
    print("\n✅ Step 3: Completing parent...")
    parent_trace["status"] = "success"
    parent_trace["end_time"] = now
    client.post("/api/traces", json=parent_trace)
    print("✅ Parent completed")
    
    # Step 4: Query children
    print("\n👨‍👧‍👦 Step 4: Querying children...")
    resp = client.get("/api/traces/agent-main-001/children")
    assert resp.status_code == 200
    children = resp.json()
    assert children["count"] == 1
    print(f"✅ Found {children['count']} child")
    
    # Step 5: Compare
    print("\n📊 Step 5: Comparing...")
    resp = client.post("/api/traces/compare", json={
        "trace_id_1": "agent-main-001",
        "trace_id_2": "agent-sub-001"
    })
    assert resp.status_code == 200
    print("✅ Comparison done")
    
    # Step 6: Metrics
    print("\n📈 Step 6: Getting metrics...")
    resp = client.get("/api/metrics/realtime")
    assert resp.status_code == 200
    metrics = resp.json()
    print(f"✅ Total traces: {metrics['total_traces']}")
    print(f"✅ Success rate: {metrics['success_rate']:.0%}")
    
    # Step 7: Stats
    print("\n📊 Step 7: Storage stats...")
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    stats = resp.json()
    print(f"✅ Backend: {stats['backend']}")
    print(f"✅ Total: {stats['total_traces']}")
    
    print("\n" + "="*60)
    print("✅ All E2E tests passed!")
    print("="*60)


def test_batch_operations():
    """Test batch operations."""
    print("\n" + "="*60)
    print("Batch Operations Test")
    print("="*60)
    
    reset_storage()
    
    # Create 10 traces
    print("\n📝 Creating 10 traces...")
    now = datetime.now().isoformat()
    for i in range(10):
        trace = {
            "id": f"batch-{i:03d}",
            "name": f"Batch Trace {i}",
            "start_time": now,
            "status": "success" if i < 8 else "error",
            "steps": [],
            "input_query": f"Query {i}",
            "output_result": f"Result {i}",
        }
        client.post("/api/traces", json=trace)
    
    # List with pagination
    print("\n📄 Testing pagination...")
    resp = client.get("/api/traces?limit=5")
    assert len(resp.json()["traces"]) == 5
    
    resp = client.get("/api/traces?limit=5&offset=5")
    assert len(resp.json()["traces"]) == 5
    print("✅ Pagination works")
    
    # Batch delete
    print("\n🗑️  Batch deleting...")
    resp = client.post("/api/traces/batch-delete", json={
        "trace_ids": ["batch-000", "batch-001", "batch-999"]  # 999 doesn't exist
    })
    result = resp.json()
    assert len(result["deleted"]) == 2
    assert len(result["failed"]) == 1
    print(f"✅ Deleted {len(result['deleted'])}, failed {len(result['failed'])}")
    
    print("\n✅ Batch operations passed!")


def main():
    print("="*60)
    print("AgentScope Backend v2 - End-to-End Tests")
    print("="*60)
    
    try:
        test_complete_workflow()
        test_batch_operations()
        
        print("\n" + "="*60)
        print("🎉 ALL E2E TESTS PASSED!")
        print("="*60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
