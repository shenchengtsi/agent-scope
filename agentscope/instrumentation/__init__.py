"""AgentScope instrumentation module for non-intrusive framework integration."""

from .nanobot_instrumentor import instrument, uninstrument

__all__ = ['instrument', 'uninstrument']
