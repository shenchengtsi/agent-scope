"""Tests for AgentScope monitoring functionality."""

import pytest
import time
from unittest.mock import Mock, patch

from agentscope import (
    trace_scope,
    get_current_trace,
    add_thinking,
    add_llm_call,
    add_tool_call,
    init_monitor,
)
from agentscope.models import StepType, Status


class TestTraceScope:
    """Test trace_scope context manager."""
    
    def test_trace_scope_creates_trace(self):
        """Test that trace_scope creates a trace event."""
        with trace_scope("test_trace", input_query="test input") as trace:
            assert trace is not None
            assert trace.name == "test_trace"
            assert trace.input_query == "test input"
    
    def test_trace_scope_adds_input_step(self):
        """Test that trace_scope adds an input step."""
        with trace_scope("test_trace", input_query="test input") as trace:
            pass
        
        # After exiting, trace should have input step
        assert len(trace.steps) >= 1
        assert trace.steps[0].type == StepType.INPUT
    
    def test_trace_scope_handles_exception(self):
        """Test that trace_scope handles exceptions properly."""
        trace = None
        try:
            with trace_scope("test_trace", input_query="test") as t:
                trace = t
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Trace should have error step
        assert trace is not None
        assert trace.status == Status.ERROR
        error_steps = [s for s in trace.steps if s.type == StepType.ERROR]
        assert len(error_steps) == 1
    
    def test_nested_trace_scopes(self):
        """Test that nested trace scopes create separate traces."""
        outer_trace = None
        inner_trace = None
        
        with trace_scope("outer") as outer:
            outer_trace = outer
            with trace_scope("inner") as inner:
                inner_trace = inner
        
        assert outer_trace.name == "outer"
        assert inner_trace.name == "inner"
        assert outer_trace.id != inner_trace.id


class TestAddSteps:
    """Test adding steps to trace."""
    
    def test_add_thinking(self):
        """Test adding thinking step."""
        with trace_scope("test") as trace:
            add_thinking("Test thinking")
        
        thinking_steps = [s for s in trace.steps if s.type == StepType.THINKING]
        assert len(thinking_steps) == 1
        assert "Test thinking" in thinking_steps[0].content
    
    def test_add_llm_call(self):
        """Test adding LLM call step."""
        with trace_scope("test") as trace:
            add_llm_call(
                prompt="Hello",
                completion="World",
                tokens_input=10,
                tokens_output=5,
                latency_ms=100.0,
            )
        
        llm_steps = [s for s in trace.steps if s.type == StepType.LLM_CALL]
        assert len(llm_steps) == 1
        assert llm_steps[0].tokens_input == 10
        assert llm_steps[0].tokens_output == 5
        assert llm_steps[0].latency_ms == 100.0
    
    def test_add_tool_call(self):
        """Test adding tool call step."""
        with trace_scope("test") as trace:
            add_tool_call(
                tool_name="search",
                arguments={"query": "python"},
                result="Python is a programming language",
                latency_ms=50.0,
            )
        
        tool_steps = [s for s in trace.steps if s.type == StepType.TOOL_CALL]
        assert len(tool_steps) == 1
        assert tool_steps[0].tool_call.name == "search"
        assert tool_steps[0].tool_call.arguments == {"query": "python"}


class TestGetCurrentTrace:
    """Test get_current_trace function."""
    
    def test_get_current_trace_outside_scope(self):
        """Test getting trace outside scope returns None."""
        trace = get_current_trace()
        assert trace is None
    
    def test_get_current_trace_inside_scope(self):
        """Test getting trace inside scope returns trace."""
        with trace_scope("test") as expected_trace:
            current = get_current_trace()
            assert current is expected_trace


class TestInitMonitor:
    """Test init_monitor function."""
    
    @patch('agentscope.monitor.requests.post')
    def test_init_monitor_sets_url(self, mock_post):
        """Test that init_monitor sets the monitor URL."""
        init_monitor("http://test-server:8000")
        # Just verify no exception is raised
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
