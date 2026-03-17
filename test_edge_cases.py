#!/usr/bin/env python3
"""Test edge cases for AgentScope Scheme 3."""

import time
import sys
sys.path.insert(0, '/Users/samsonchoi/agent-scope/sdk')

from agentscope import (
    init_monitor,
    trace_scope,
    instrumented_tool,
    get_current_trace,
    add_thinking,
    add_step,
    StepType,
    Status,
)

# Initialize monitoring
init_monitor("http://localhost:8000")

# Test 1: Tool returning None (should record as "null" not None)
@instrumented_tool
def return_none():
    """Function that returns None."""
    return None

# Test 2: Tool returning complex object
@instrumented_tool
def return_complex():
    """Function that returns complex object."""
    return {
        "nested": {
            "list": [1, 2, 3],
            "dict": {"a": "b"}
        },
        "unicode": "中文测试"
    }

# Test 3: Tool with no trace context (should still work)
@instrumented_tool
def standalone_tool():
    """Tool called without trace context."""
    return "standalone"

# Test 4: Nested trace_scope
def test_nested_scopes():
    with trace_scope("outer_scope", input_query="outer"):
        add_thinking("In outer scope")
        
        # Inner scope should create its own trace
        with trace_scope("inner_scope", input_query="inner"):
            add_thinking("In inner scope")
            return_complex()
        
        add_thinking("Back to outer scope")
        return_none()

def main():
    print("🧪 Testing edge cases...")
    
    # Test 1: Tool returning None
    print("\n1️⃣ Testing tool returning None...")
    with trace_scope("test_none", input_query="test none return"):
        result = return_none()
        print(f"   Result: {result}")
    print("   ✅ Done")
    
    # Test 2: Tool returning complex object
    print("\n2️⃣ Testing tool returning complex object...")
    with trace_scope("test_complex", input_query="test complex return"):
        result = return_complex()
        print(f"   Result type: {type(result)}")
    print("   ✅ Done")
    
    # Test 3: Tool without trace context
    print("\n3️⃣ Testing tool without trace context...")
    result = standalone_tool()  # Should work without error
    print(f"   Result: {result}")
    print("   ✅ Done")
    
    # Test 4: Nested scopes
    print("\n4️⃣ Testing nested trace_scope...")
    test_nested_scopes()
    print("   ✅ Done")
    
    # Test 5: Empty trace_scope
    print("\n5️⃣ Testing empty trace_scope...")
    with trace_scope("empty_scope"):
        pass
    print("   ✅ Done")
    
    # Test 6: Metadata handling
    print("\n6️⃣ Testing metadata...")
    with trace_scope(
        "metadata_test",
        input_query="test metadata",
        tags=["test", "metadata"],
        metadata={"user_id": "123", "session": "abc"}
    ):
        add_thinking("Testing metadata storage")
    print("   ✅ Done")
    
    print("\n✨ All edge case tests completed!")
    print("🌐 Open http://localhost:3001 to see the traces")

if __name__ == "__main__":
    main()
