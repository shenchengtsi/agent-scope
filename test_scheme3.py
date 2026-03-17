#!/usr/bin/env python3
"""Test script for AgentScope Scheme 3 implementation."""

import time
import sys
sys.path.insert(0, '/Users/samsonchoi/agent-scope/sdk')

from agentscope import (
    init_monitor,
    trace_scope,
    instrumented_tool,
    get_current_trace,
    add_thinking,
)

# Initialize monitoring
init_monitor("http://localhost:8000")

# Define a tool with auto-tracing
@instrumented_tool
def search_weather(city: str) -> dict:
    """Search weather for a city."""
    time.sleep(0.1)  # Simulate API call
    return {"city": city, "temp": 25, "weather": "sunny"}

@instrumented_tool
def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    time.sleep(0.05)
    return eval(expression)

def mock_llm_call(prompt: str) -> str:
    """Mock LLM call to demonstrate manual tracing."""
    trace = get_current_trace()
    if trace:
        from agentscope import add_llm_call
        start = time.time()
        time.sleep(0.2)  # Simulate LLM latency
        result = f"This is a mock response for: {prompt}"
        latency_ms = (time.time() - start) * 1000
        add_llm_call(
            prompt=prompt,
            completion=result,
            tokens_input=len(prompt.split()),
            tokens_output=len(result.split()),
            latency_ms=latency_ms
        )
    return result

def main():
    """Test the trace_scope context manager."""
    print("🧪 Testing AgentScope Scheme 3...")
    
    # Test 1: Basic trace_scope
    print("\n1️⃣ Testing trace_scope context manager...")
    with trace_scope(
        name="weather_agent",
        input_query="What's the weather in Beijing?",
        tags=["test", "scheme3"]
    ):
        # Simulate agent thinking
        add_thinking("User wants to know weather in Beijing")
        
        # Simulate LLM call
        llm_result = mock_llm_call("Extract city from: What's the weather in Beijing?")
        
        # Call tool (auto-traced)
        weather = search_weather("Beijing")
        
        # More thinking
        add_thinking(f"Got weather data: {weather}")
        
        # Another tool call
        temp_c = calculate("25 * 9 / 5 + 32")  # Convert to Fahrenheit
        
    print("   ✅ Trace sent to AgentScope")
    
    # Test 2: Multiple tool calls
    print("\n2️⃣ Testing multiple tool calls...")
    with trace_scope(
        name="multi_tool_agent",
        input_query="Compare weather in Beijing and Shanghai",
        tags=["test", "multi-tool"]
    ):
        add_thinking("Need to fetch weather for two cities")
        
        beijing = search_weather("Beijing")
        shanghai = search_weather("Shanghai")
        
        add_thinking(f"Beijing: {beijing}, Shanghai: {shanghai}")
        
        diff = calculate(f"{shanghai['temp']} - {beijing['temp']}")
        add_thinking(f"Temperature difference: {diff}°C")
        
    print("   ✅ Multi-tool trace sent")
    
    # Test 3: Error handling
    print("\n3️⃣ Testing error handling...")
    try:
        with trace_scope(
            name="error_agent",
            input_query="This will fail",
            tags=["test", "error"]
        ):
            add_thinking("About to call a tool that will fail...")
            result = calculate("1 / 0")  # This will raise ZeroDivisionError
    except ZeroDivisionError:
        print("   ✅ Error caught and trace should show failure")
    
    print("\n✨ All tests completed!")
    print("🌐 Open http://localhost:3001 to see the traces")

if __name__ == "__main__":
    main()
