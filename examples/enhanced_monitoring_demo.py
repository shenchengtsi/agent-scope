"""
AgentScope Enhanced Monitoring Demo

This demo showcases all the new monitoring capabilities:
1. Complete Prompt structure and content
2. Skills loading details
3. Thinking/Reasoning content
4. Tool Selection decisions
5. Memory operation details
6. Collapsible detail panels with copy buttons
7. Hierarchical view with sub-agent calls
8. Comparison mode
9. Real-time metrics cards

Usage:
    1. Start the AgentScope backend:
       cd agent-scope/backend && python main.py
    
    2. Start the AgentScope frontend:
       cd agent-scope/frontend && npm start
    
    3. Run this demo:
       python examples/enhanced_monitoring_demo.py
"""

import time
import random
from agentscope import (
    init_monitor,
    trace_scope,
    add_prompt_build_step,
    add_skills_loading_step,
    add_tool_selection_step,
    add_memory_operation_step,
    add_subagent_call_step,
    add_reasoning_step,
    add_llm_call,
    add_tool_call,
)


def demo_prompt_build():
    """Demonstrate prompt building monitoring."""
    print("📝 Demo: Prompt Build Monitoring")
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. You can use tools to help users."},
        {"role": "user", "content": "What's the weather like in Beijing?"},
        {"role": "assistant", "content": "I'll check the weather for you."},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "function": {"name": "weather_api", "arguments": '{"city": "Beijing"}'}}]},
        {"role": "tool", "content": "Sunny, 25°C", "tool_call_id": "call_1", "name": "weather_api"},
        {"role": "assistant", "content": "The weather in Beijing is sunny with a temperature of 25°C."},
        {"role": "user", "content": "Thanks! And what's the weather in Shanghai?"},
    ]
    
    add_prompt_build_step(
        messages=messages,
        system_prompt="You are a helpful AI assistant. You can use tools to help users.",
        model_config={
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95,
            "context_window": 128000,
        }
    )
    print("   ✓ Prompt build step recorded with full messages structure")


def demo_skills_loading():
    """Demonstrate skills loading monitoring."""
    print("\n🔧 Demo: Skills Loading Monitoring")
    
    skills = [
        {
            "name": "weather_api",
            "description": "Get current weather data for any city",
            "status": "loaded",
            "load_time_ms": 12.5,
        },
        {
            "name": "github",
            "description": "GitHub API operations - repos, issues, PRs",
            "status": "loaded",
            "load_time_ms": 28.3,
        },
        {
            "name": "web_search",
            "description": "Search the web for information",
            "status": "loaded",
            "load_time_ms": 8.7,
        },
        {
            "name": "database_query",
            "description": "Query internal database",
            "status": "failed",
            "error": "Database connection timeout",
            "load_time_ms": 5000.0,
        },
    ]
    
    add_skills_loading_step(
        skills=skills,
        total_time_ms=5049.5,
    )
    print("   ✓ Skills loading step recorded with 4 skills (3 loaded, 1 failed)")


def demo_tool_selection():
    """Demonstrate tool selection monitoring."""
    print("\n🎯 Demo: Tool Selection Monitoring")
    
    available_tools = [
        {
            "name": "weather_api",
            "description": "Get current weather data for any city. Parameters: city (string)"
        },
        {
            "name": "web_search",
            "description": "Search the web for information. Parameters: query (string)"
        },
        {
            "name": "calculator",
            "description": "Perform mathematical calculations. Parameters: expression (string)"
        },
        {
            "name": "github",
            "description": "GitHub API operations. Parameters: action (string), repo (string)"
        },
    ]
    
    add_tool_selection_step(
        selected_tool="weather_api",
        available_tools=available_tools,
        reason="The user is asking about weather in a specific city (Beijing). The weather_api tool is specifically designed for this purpose and can retrieve current weather data for any city. Other tools like web_search could also work but would be less efficient and accurate than the dedicated weather API.",
        confidence=0.98,
        tool_call_id="call_weather_001",
    )
    print("   ✓ Tool selection step recorded with reasoning and confidence")


def demo_memory_operations():
    """Demonstrate memory operation monitoring."""
    print("\n🧠 Demo: Memory Operations Monitoring")
    
    # Memory write operation
    add_memory_operation_step(
        operation="write",
        key="user_preferences",
        namespace="session_001",
        data={"theme": "dark", "language": "zh-CN", "notifications": True},
        tokens_affected=150,
    )
    print("   ✓ Memory write operation recorded")
    
    # Memory read operation
    add_memory_operation_step(
        operation="read",
        key="conversation_history",
        namespace="session_001",
        data_preview="[10 messages] User: Hello! Assistant: Hi! ...",
        tokens_affected=2500,
    )
    print("   ✓ Memory read operation recorded")
    
    # Memory consolidate operation
    add_memory_operation_step(
        operation="consolidate",
        key="session_memory",
        namespace="session_001",
        tokens_affected=15000,
        details={
            "original_tokens": 20000,
            "new_tokens": 5000,
            "compression_ratio": 0.75,
            "strategy": "summarization",
        }
    )
    print("   ✓ Memory consolidate operation recorded")


def demo_reasoning():
    """Demonstrate reasoning/thinking monitoring."""
    print("\n💭 Demo: Reasoning/Thinking Monitoring")
    
    # Chain of thought reasoning
    add_reasoning_step(
        content="""I need to solve this step by step:
1. First, I should understand what the user is asking - they want to know about machine learning basics
2. I need to provide a clear, structured explanation suitable for beginners
3. I should cover: definition, types (supervised/unsupervised), and a simple example
4. Keep it concise but informative, avoiding overly technical jargon""",
        reasoning_type="chain_of_thought",
        confidence=0.92,
    )
    print("   ✓ Chain of thought reasoning recorded")
    
    # Plan reasoning
    add_reasoning_step(
        content="Breaking down the complex task into manageable steps:",
        reasoning_type="plan",
        plan_steps=[
            "Analyze user query to extract key entities and intent",
            "Retrieve relevant information from knowledge base",
            "Formulate a structured response with examples",
            "Review for accuracy and clarity",
            "Generate final response with citations"
        ],
        confidence=0.88,
    )
    print("   ✓ Plan reasoning recorded")
    
    # Reflection reasoning
    add_reasoning_step(
        content="""Reflection on the previous response:
The previous answer was accurate but too technical. The user asked for "basics" but I included advanced concepts like gradient descent and backpropagation. I should:
- Simplify the explanation
- Use more analogies
- Remove technical jargon
- Add a concrete, relatable example""",
        reasoning_type="reflection",
        confidence=0.85,
    )
    print("   ✓ Reflection reasoning recorded")


def demo_subagent_call():
    """Demonstrate sub-agent call monitoring."""
    print("\n🤖 Demo: Sub-Agent Call Monitoring")
    
    add_subagent_call_step(
        agent_name="code_review_agent",
        agent_id="agent_code_001",
        input_query="""Please review the following Python code for potential issues:

def calculate_sum(numbers):
    result = 0
    for n in numbers:
        result += n
    return result

# Test
print(calculate_sum([1, 2, 3, 4, 5]))""",
        child_trace_id="trace_code_review_001",
        timeout=30.0,
        result_preview="Code review completed. Found 1 suggestion: Add type hints for better code clarity. Overall quality: Good.",
    )
    print("   ✓ Sub-agent call recorded with child trace reference")


def demo_full_workflow():
    """Demonstrate a complete workflow with all monitoring features."""
    print("\n🚀 Demo: Complete Workflow")
    print("   Starting a comprehensive agent execution...")
    
    with trace_scope(
        name="enhanced_agent_workflow",
        input_query="Find the top 3 Python repositories on GitHub about machine learning",
        tags=["demo", "enhanced_monitoring"],
    ) as trace:
        # 1. Load skills
        add_skills_loading_step(
            skills=[
                {"name": "github", "description": "GitHub API", "status": "loaded", "load_time_ms": 15.2},
                {"name": "web_search", "description": "Web search", "status": "loaded", "load_time_ms": 8.5},
            ],
            total_time_ms=23.7,
        )
        time.sleep(0.1)
        
        # 2. Build prompt
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Find the top 3 Python repositories on GitHub about machine learning"},
        ]
        add_prompt_build_step(
            messages=messages,
            system_prompt="You are a helpful assistant.",
            model_config={"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        )
        time.sleep(0.1)
        
        # 3. Reasoning
        add_reasoning_step(
            content="The user wants to find popular ML repositories. I should use the github tool to search for repositories.",
            reasoning_type="chain_of_thought",
            confidence=0.95,
        )
        time.sleep(0.1)
        
        # 4. Tool selection
        add_tool_selection_step(
            selected_tool="github",
            available_tools=[
                {"name": "github", "description": "GitHub API"},
                {"name": "web_search", "description": "Web search"},
            ],
            reason="GitHub API is the best tool for searching GitHub repositories directly",
            confidence=0.97,
        )
        time.sleep(0.1)
        
        # 5. Tool call
        add_tool_call(
            tool_name="github",
            arguments={"action": "search", "query": "machine learning python", "sort": "stars", "limit": 3},
            result={"repositories": ["tensorflow/tensorflow", "scikit-learn/scikit-learn", "pytorch/pytorch"]},
            latency_ms=850.5,
        )
        time.sleep(0.1)
        
        # 6. Memory operation - save results
        add_memory_operation_step(
            operation="write",
            key="github_search_results",
            data={"query": "machine learning python", "results": ["tensorflow", "scikit-learn", "pytorch"]},
            tokens_affected=200,
        )
        time.sleep(0.1)
        
        # 7. LLM call
        add_llm_call(
            prompt="Summarize these ML repositories: tensorflow, scikit-learn, pytorch",
            completion="Here are the top 3 ML repositories: 1. TensorFlow - Google's ML platform...",
            tokens_input=50,
            tokens_output=150,
            latency_ms=1200.0,
        )
        
        # Set output
        trace.output_result = "Found top 3 ML repos: TensorFlow, Scikit-learn, PyTorch"
        
    print("   ✓ Complete workflow finished")
    print(f"   ✓ Trace ID: {trace.id}")
    print(f"   ✓ Total steps: {len(trace.steps)}")
    print(f"   ✓ Total tokens: {trace.total_tokens}")
    print(f"   ✓ Total latency: {trace.total_latency_ms:.1f}ms")


def demo_comparison():
    """Generate two traces for comparison demo."""
    print("\n📊 Demo: Comparison Mode Data Generation")
    
    # First trace - successful
    with trace_scope(name="search_query_v1", input_query="Python tutorials") as trace1:
        add_skills_loading_step(skills=[{"name": "search", "status": "loaded"}])
        add_llm_call(
            prompt="Python tutorials",
            completion="Here are some Python tutorials...",
            tokens_input=10,
            tokens_output=500,
            latency_ms=1500.0,
        )
        trace1.cost_estimate = 0.015
    
    time.sleep(0.5)
    
    # Second trace - optimized
    with trace_scope(name="search_query_v2", input_query="Python tutorials") as trace2:
        add_skills_loading_step(skills=[{"name": "search", "status": "loaded"}])
        add_prompt_build_step(
            messages=[{"role": "user", "content": "Python tutorials"}],
            model_config={"model": "gpt-3.5-turbo"},  # Cheaper model
        )
        add_llm_call(
            prompt="Python tutorials",
            completion="Here are some Python tutorials...",
            tokens_input=10,
            tokens_output=300,  # More concise
            latency_ms=800.0,  # Faster
        )
        trace2.cost_estimate = 0.005  # Lower cost
    
    print(f"   ✓ Generated trace 1: {trace1.id} ({trace1.total_latency_ms:.0f}ms, ${trace1.cost_estimate:.3f})")
    print(f"   ✓ Generated trace 2: {trace2.id} ({trace2.total_latency_ms:.0f}ms, ${trace2.cost_estimate:.3f})")
    print("   ✓ You can now compare these traces in the dashboard!")


def main():
    """Main demo function."""
    print("=" * 60)
    print("🎯 AgentScope Enhanced Monitoring Demo")
    print("=" * 60)
    
    # Initialize monitoring
    init_monitor("http://localhost:8000")
    print("\n✅ Connected to AgentScope backend at http://localhost:8000")
    
    # Run all demos
    demo_prompt_build()
    demo_skills_loading()
    demo_tool_selection()
    demo_memory_operations()
    demo_reasoning()
    demo_subagent_call()
    demo_full_workflow()
    demo_comparison()
    
    print("\n" + "=" * 60)
    print("✅ All demos completed!")
    print("=" * 60)
    print("\n📱 Open http://localhost:3000 to view the dashboard")
    print("\n🎨 New features to explore:")
    print("   1. Click on steps to see collapsible detail panels")
    print("   2. Use the 'Copy JSON' button to copy step data")
    print("   3. View Prompt, Skills, Tool Selection, Memory details")
    print("   4. Check real-time metrics cards at the top")
    print("   5. Click 'Compare' to compare two traces side-by-side")
    print("   6. See reasoning and thinking process details")
    print("\n💡 Press Ctrl+C to exit")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
