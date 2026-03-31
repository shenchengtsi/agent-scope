#!/usr/bin/env python3
"""Performance benchmarks for AgentScope storage."""

import time
import tempfile
import os
import sys
from datetime import datetime

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from agentscope.storage import create_storage


def benchmark_storage(storage, name, num_operations=1000):
    """Benchmark storage operations."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {name}")
    print(f"Operations: {num_operations}")
    print('='*60)
    
    results = {}
    
    # Benchmark: Save
    start = time.time()
    trace_ids = []
    for i in range(num_operations):
        trace = {
            "id": f"perf-{i}",
            "name": f"Performance Test {i}",
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "input_query": f"Query {i}",
            "output_result": f"Result {i}",
            "steps": [
                {"type": "input", "content": f"Step {i}-1"},
                {"type": "llm", "content": f"Step {i}-2"},
            ],
        }
        storage.save_trace(trace)
        trace_ids.append(f"perf-{i}")
    
    save_time = time.time() - start
    results['save'] = {
        'total_seconds': save_time,
        'per_operation_ms': (save_time / num_operations) * 1000,
        'ops_per_second': num_operations / save_time,
    }
    
    print(f"\n📊 Save Performance:")
    print(f"   Total time: {save_time:.3f}s")
    print(f"   Per operation: {results['save']['per_operation_ms']:.3f}ms")
    print(f"   Operations/sec: {results['save']['ops_per_second']:.1f}")
    
    # Benchmark: Get
    start = time.time()
    for trace_id in trace_ids:
        storage.get_trace(trace_id)
    
    get_time = time.time() - start
    results['get'] = {
        'total_seconds': get_time,
        'per_operation_ms': (get_time / num_operations) * 1000,
        'ops_per_second': num_operations / get_time,
    }
    
    print(f"\n📊 Get Performance:")
    print(f"   Total time: {get_time:.3f}s")
    print(f"   Per operation: {results['get']['per_operation_ms']:.3f}ms")
    print(f"   Operations/sec: {results['get']['ops_per_second']:.1f}")
    
    # Benchmark: List (with limit)
    start = time.time()
    for _ in range(100):  # List 100 times
        storage.list_traces(limit=100)
    
    list_time = time.time() - start
    results['list'] = {
        'total_seconds': list_time,
        'per_operation_ms': (list_time / 100) * 1000,
        'ops_per_second': 100 / list_time,
    }
    
    print(f"\n📊 List Performance (100 items, 100 calls):")
    print(f"   Total time: {list_time:.3f}s")
    print(f"   Per operation: {results['list']['per_operation_ms']:.3f}ms")
    print(f"   Operations/sec: {results['list']['ops_per_second']:.1f}")
    
    # Benchmark: Count
    start = time.time()
    for _ in range(100):
        storage.count_traces()
    
    count_time = time.time() - start
    results['count'] = {
        'total_seconds': count_time,
        'per_operation_ms': (count_time / 100) * 1000,
        'ops_per_second': 100 / count_time,
    }
    
    print(f"\n📊 Count Performance (100 calls):")
    print(f"   Total time: {count_time:.3f}s")
    print(f"   Per operation: {results['count']['per_operation_ms']:.3f}ms")
    print(f"   Operations/sec: {results['count']['ops_per_second']:.1f}")
    
    # Stats
    print(f"\n📦 Storage Stats:")
    stats = storage.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return results


def compare_backends():
    """Compare memory vs SQLite performance."""
    print("\n" + "="*60)
    print("Storage Backend Performance Comparison")
    print("="*60)
    
    # Test memory storage
    memory_storage = create_storage("memory")
    memory_results = benchmark_storage(memory_storage, "InMemoryStorage", num_operations=1000)
    
    # Test SQLite storage
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        sqlite_storage = create_storage("sqlite", db_path=db_path)
        sqlite_results = benchmark_storage(sqlite_storage, "SQLiteStorage", num_operations=1000)
        
        # Comparison
        print("\n" + "="*60)
        print("Performance Comparison (SQLite vs Memory)")
        print("="*60)
        
        for operation in ['save', 'get', 'list', 'count']:
            mem_ms = memory_results[operation]['per_operation_ms']
            sql_ms = sqlite_results[operation]['per_operation_ms']
            ratio = sql_ms / mem_ms if mem_ms > 0 else 0
            
            print(f"\n{operation.upper()}:")
            print(f"   Memory: {mem_ms:.3f}ms")
            print(f"   SQLite: {sql_ms:.3f}ms")
            print(f"   Ratio:  {ratio:.2f}x slower")
        
        # Check if SQLite meets requirements
        print("\n" + "="*60)
        print("Requirements Check")
        print("="*60)
        
        save_latency = sqlite_results['save']['per_operation_ms']
        if save_latency < 100:
            print(f"✅ Save latency: {save_latency:.3f}ms (< 100ms requirement)")
        else:
            print(f"⚠️  Save latency: {save_latency:.3f}ms (exceeds 100ms requirement)")
        
        get_latency = sqlite_results['get']['per_operation_ms']
        if get_latency < 50:
            print(f"✅ Get latency: {get_latency:.3f}ms (< 50ms requirement)")
        else:
            print(f"⚠️  Get latency: {get_latency:.3f}ms (exceeds 50ms requirement)")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def stress_test():
    """Stress test with large data."""
    print("\n" + "="*60)
    print("Stress Test: Large Traces")
    print("="*60)
    
    storage = create_storage("memory")
    
    # Create a large trace with many steps
    large_trace = {
        "id": "large-trace",
        "name": "Large Trace Test",
        "status": "success",
        "start_time": datetime.now().isoformat(),
        "input_query": "x" * 10000,  # 10KB input
        "output_result": "y" * 10000,  # 10KB output
        "steps": [
            {
                "type": "llm",
                "content": "z" * 5000,
                "tokens_input": 1000,
                "tokens_output": 500,
                "latency_ms": 1000.0,
            }
            for _ in range(100)  # 100 steps
        ],
    }
    
    # Measure save time
    start = time.time()
    storage.save_trace(large_trace)
    save_time = time.time() - start
    
    # Measure get time
    start = time.time()
    retrieved = storage.get_trace("large-trace")
    get_time = time.time() - start
    
    trace_size = len(str(large_trace))
    
    print(f"\n📊 Large Trace ({trace_size} bytes, {len(large_trace['steps'])} steps):")
    print(f"   Save time: {save_time*1000:.3f}ms")
    print(f"   Get time: {get_time*1000:.3f}ms")
    print(f"   Retrieved steps: {len(retrieved['steps'])}")


def main():
    """Run all performance tests."""
    print("="*60)
    print("AgentScope Storage Performance Tests")
    print("="*60)
    
    # Compare backends
    compare_backends()
    
    # Stress test
    stress_test()
    
    print("\n" + "="*60)
    print("Performance Tests Complete")
    print("="*60)


if __name__ == "__main__":
    main()
