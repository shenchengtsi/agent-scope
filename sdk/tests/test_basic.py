"""Basic smoke tests for AgentScope."""

import pytest


def test_import():
    """Test that agentscope can be imported."""
    import agentscope
    assert agentscope.__version__ is not None


def test_init_monitor():
    """Test init_monitor function exists."""
    from agentscope import init_monitor
    assert callable(init_monitor)


def test_trace_scope():
    """Test trace_scope context manager exists."""
    from agentscope import trace_scope
    assert callable(trace_scope)
