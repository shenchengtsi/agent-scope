#!/usr/bin/env python3
"""Integration test for AgentScope SDK + Storage."""

import sys
import os
import json
import tempfile
from datetime import datetime

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from agentscope.storage import create_storage, InMemoryStorage, SQLiteStorage
from agentscope.models import TraceEvent, ExecutionStep, StepType, Status


def test_memory_storage_integration():
    """Test SDK models with InMemoryStorage."""
    print("\n=== Test 1: SDK + InMemoryStorage ===")
    
    storage = create_storage("memory")
    
    # Create a trace using SDK models
    trace = TraceEvent(
        name="test_agent",
        tags=["test", "integration"],
        input_query="Hello, world!",
    )
    
    # Add some steps
    trace.add_step(ExecutionStep(
        type=StepType.INPUT,
        content="Hello, world!",
        status=Status.SUCCESS,
    ))
    
    trace.add_step(ExecutionStep(
        type=StepType.LLM_CALL,
        content="Hi there!",
        status=Status.SUCCESS,
        tokens_input=10,
        tokens_output=5,
        latency_ms=150.0,
    ))
    
    # Finish trace
    trace.finish(Status.SUCCESS)
    
    # Save to storage
    trace_dict = trace.to_dict()
    trace_id = storage.save_trace(trace_dict)
    
    # Retrieve and verify
    retrieved = storage.get_trace(trace_id)
    assert retrieved is not None, "Trace should be retrieved"
    assert retrieved["name"] == "test_agent", "Name should match"
    assert len(retrieved.get("steps", [])) == 2, "Should have 2 steps"
    assert retrieved["status"] == "success", "Status should be success"
    
    print(f"✅ Trace created: {trace_id}")
    print(f"✅ Steps: {len(retrieved['steps'])}")
    print(f"✅ Storage stats: {storage.get_stats()}")
    
    return True


def test_sqlite_storage_integration():
    """Test SDK models with SQLiteStorage."""
    print("\n=== Test 2: SDK + SQLiteStorage ===")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = create_storage("sqlite", db_path=db_path)
        
        # Create multiple traces
        for i in range(5):
            trace = TraceEvent(
                name=f"agent_{i}",
                tags=["batch", f"agent{i}"],
                input_query=f"Query {i}",
            )
            trace.add_step(ExecutionStep(
                type=StepType.INPUT,
                content=f"Query {i}",
                status=Status.SUCCESS,
            ))
            trace.finish(Status.SUCCESS if i % 2 == 0 else Status.ERROR)
            
            storage.save_trace(trace.to_dict())
        
        # Test filtering
        success_traces = storage.list_traces(status="success")
        print(f"✅ Success traces: {len(success_traces)}")
        
        # Test stats
        stats = storage.get_stats()
        print(f"✅ Total traces: {stats['total_traces']}")
        print(f"✅ By status: {stats.get('by_status', {})}")
        
        assert stats['total_traces'] == 5, "Should have 5 traces"
        
        return True
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_storage_switching():
    """Test switching between storage backends."""
    print("\n=== Test 3: Storage Backend Switching ===")
    
    # Test memory backend
    os.environ["AGENTSCOPE_STORAGE_BACKEND"] = "memory"
    from backend.storage_manager import reset_storage, get_storage
    
    reset_storage()
    memory_storage = get_storage()
    assert isinstance(memory_storage, InMemoryStorage), "Should be memory storage"
    print("✅ Memory storage initialized")
    
    # Add a trace
    memory_storage.save_trace({
        "id": "test-123",
        "name": "Test",
        "status": "success",
        "start_time": datetime.now().isoformat(),
    })
    
    # Test SQLite backend
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        sqlite_storage = create_storage("sqlite", db_path=db_path)
        assert isinstance(sqlite_storage, SQLiteStorage), "Should be SQLite storage"
        print("✅ SQLite storage initialized")
        
        # Save and retrieve
        sqlite_storage.save_trace({
            "id": "test-456",
            "name": "SQLite Test",
            "status": "success",
            "start_time": datetime.now().isoformat(),
        })
        
        retrieved = sqlite_storage.get_trace("test-456")
        assert retrieved is not None, "Should retrieve from SQLite"
        print("✅ SQLite persistence works")
        
        return True
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_error_handling():
    """Test error handling in storage operations."""
    print("\n=== Test 4: Error Handling ===")
    
    storage = create_storage("memory")
    
    # Test missing trace
    result = storage.get_trace("nonexistent")
    assert result is None, "Should return None for missing trace"
    print("✅ Missing trace handling correct")
    
    # Test invalid data
    try:
        storage.save_trace({})  # Missing required fields
        # Should handle gracefully
    except Exception as e:
        print(f"✅ Invalid data caught: {type(e).__name__}")
    
    # Test delete nonexistent
    result = storage.delete_trace("nonexistent")
    assert result is False, "Should return False for nonexistent delete"
    print("✅ Delete nonexistent handling correct")
    
    return True


def test_concurrent_access():
    """Test concurrent access to storage."""
    print("\n=== Test 5: Concurrent Access ===")
    
    import threading
    import time
    
    storage = create_storage("memory")
    errors = []
    
    def writer(thread_id):
        try:
            for i in range(10):
                trace = {
                    "id": f"thread-{thread_id}-{i}",
                    "name": f"Thread {thread_id}",
                    "status": "success",
                    "start_time": datetime.now().isoformat(),
                }
                storage.save_trace(trace)
                time.sleep(0.01)  # Small delay
        except Exception as e:
            errors.append(str(e))
    
    # Start multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=writer, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    if errors:
        print(f"❌ Concurrent access errors: {errors}")
        return False
    
    # Verify all traces saved
    count = storage.count_traces()
    print(f"✅ Saved {count} traces from 3 threads")
    assert count == 30, f"Should have 30 traces, got {count}"
    
    return True


def main():
    """Run all integration tests."""
    print("="*60)
    print("AgentScope SDK + Storage Integration Tests")
    print("="*60)
    
    tests = [
        ("Memory Storage", test_memory_storage_integration),
        ("SQLite Storage", test_sqlite_storage_integration),
        ("Backend Switching", test_storage_switching),
        ("Error Handling", test_error_handling),
        ("Concurrent Access", test_concurrent_access),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
