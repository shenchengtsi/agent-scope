# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-17

### Added

- Initial release of AgentScope
- **SDK**: Core monitoring functionality with Scheme 3 (Context Manager + ContextVar)
  - `trace_scope()` context manager for creating trace contexts
  - `add_llm_call()` for recording LLM invocations
  - `add_tool_call()` for recording tool executions
  - `add_thinking()` for recording reasoning steps
  - `add_memory()` for recording memory operations
  - `instrument_llm()` for auto-instrumenting LLM clients
  - `@instrumented_tool` decorator for auto-tracing tools
- **Backend**: FastAPI-based server
  - REST API for trace collection
  - WebSocket for real-time updates
  - SQLite storage (configurable for production)
- **Frontend**: React-based web UI
  - Trace list with filtering
  - Execution chain visualization
  - Performance metrics dashboard
- **Documentation**:
  - Comprehensive integration guide
  - Architecture design document
  - nanobot integration example
- **Tests**: Edge case tests and Scheme 3 validation tests

### Features

- Framework-agnostic design supporting LangChain, AutoGen, CrewAI, and custom frameworks
- Low overhead (< 1% performance impact)
- Fault isolation (monitoring failures don't affect main business logic)
- Real-time debugging via WebSocket

[Unreleased]: https://github.com/shenchengtsi/agent-scope/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/shenchengtsi/agent-scope/releases/tag/v0.1.0
