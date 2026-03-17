"""Tests for AgentScope data models."""

import pytest
from datetime import datetime

from agentscope.models import (
    ToolCall,
    ExecutionStep,
    TraceEvent,
    StepType,
    Status,
)


class TestToolCall:
    """Test ToolCall model."""
    
    def test_tool_call_creation(self):
        """Test creating a ToolCall."""
        tool_call = ToolCall(
            name="search",
            arguments={"query": "python"},
            result="Python is great",
            latency_ms=100.0,
        )
        
        assert tool_call.name == "search"
        assert tool_call.arguments == {"query": "python"}
        assert tool_call.result == "Python is great"
        assert tool_call.latency_ms == 100.0
        assert tool_call.id is not None
    
    def test_tool_call_to_dict(self):
        """Test ToolCall serialization."""
        tool_call = ToolCall(
            name="search",
            arguments={"query": "python"},
            result="result",
            error=None,
            latency_ms=100.0,
        )
        
        d = tool_call.to_dict()
        assert d["name"] == "search"
        assert d["arguments"] == {"query": "python"}
        assert d["result"] == "result"
        assert d["error"] is None


class TestExecutionStep:
    """Test ExecutionStep model."""
    
    def test_step_creation(self):
        """Test creating an ExecutionStep."""
        step = ExecutionStep(
            type=StepType.LLM_CALL,
            content="Test content",
            tokens_input=100,
            tokens_output=50,
            latency_ms=500.0,
            status=Status.SUCCESS,
        )
        
        assert step.type == StepType.LLM_CALL
        assert step.content == "Test content"
        assert step.tokens_input == 100
        assert step.tokens_output == 50
        assert step.latency_ms == 500.0
        assert step.status == Status.SUCCESS
    
    def test_step_to_dict(self):
        """Test ExecutionStep serialization."""
        step = ExecutionStep(
            type=StepType.TOOL_CALL,
            content="Tool execution",
            status=Status.SUCCESS,
        )
        
        d = step.to_dict()
        assert d["type"] == "tool_call"
        assert d["content"] == "Tool execution"
        assert d["status"] == "success"
        assert "timestamp" in d


class TestTraceEvent:
    """Test TraceEvent model."""
    
    def test_trace_creation(self):
        """Test creating a TraceEvent."""
        trace = TraceEvent(
            name="test_trace",
            tags=["test", "debug"],
            input_query="test query",
        )
        
        assert trace.name == "test_trace"
        assert trace.tags == ["test", "debug"]
        assert trace.input_query == "test query"
        assert trace.status == Status.PENDING
        assert trace.total_tokens == 0
    
    def test_add_step(self):
        """Test adding steps to trace."""
        trace = TraceEvent(name="test")
        step = ExecutionStep(type=StepType.INPUT, content="Input")
        
        trace.add_step(step)
        
        assert len(trace.steps) == 1
        assert trace.total_tokens == step.tokens_input + step.tokens_output
    
    def test_finish_success(self):
        """Test finishing trace with success."""
        trace = TraceEvent(name="test")
        trace.add_step(ExecutionStep(
            type=StepType.INPUT,
            content="Input",
            tokens_input=10,
            tokens_output=5,
        ))
        
        trace.finish(Status.SUCCESS)
        
        assert trace.status == Status.SUCCESS
        assert trace.end_time is not None
        assert trace.total_latency_ms > 0
    
    def test_finish_error(self):
        """Test finishing trace with error."""
        trace = TraceEvent(name="test")
        trace.finish(Status.ERROR)
        
        assert trace.status == Status.ERROR
        assert trace.end_time is not None
    
    def test_to_dict(self):
        """Test TraceEvent serialization."""
        trace = TraceEvent(
            name="test",
            tags=["debug"],
            input_query="query",
            metadata={"key": "value"},
        )
        trace.add_step(ExecutionStep(type=StepType.INPUT, content="Input"))
        trace.finish(Status.SUCCESS)
        
        d = trace.to_dict()
        assert d["name"] == "test"
        assert d["tags"] == ["debug"]
        assert d["input_query"] == "query"
        assert d["metadata"] == {"key": "value"}
        assert d["status"] == "success"
        assert len(d["steps"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
