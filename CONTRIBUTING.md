# Contributing to AgentScope

Thank you for your interest in contributing to AgentScope! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a branch for your changes
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Git

### SDK Development

```bash
cd sdk
pip install -e ".[dev]"
pytest tests/
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

## Making Changes

### Project Structure

```
agentscope/
├── sdk/              # Python SDK
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── docs/             # Documentation
└── examples/         # Integration examples
```

### Adding New Features

1. **For SDK changes**:
   - Add tests in `sdk/tests/`
   - Update documentation
   - Ensure backward compatibility

2. **For backend changes**:
   - Update API models if needed
   - Add tests
   - Update API documentation

3. **For frontend changes**:
   - Follow existing component patterns
   - Ensure responsive design
   - Test in multiple browsers

### Testing

Run all tests before submitting:

```bash
# SDK tests
cd sdk
pytest tests/ -v

# Backend tests
cd backend
pytest tests/ -v

# Linting
black sdk/ backend/
isort sdk/ backend/
flake8 sdk/ backend/
```

## Submitting Changes

### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update CHANGELOG.md following Keep a Changelog format
3. Ensure all tests pass
4. Update documentation as needed
5. Submit PR with clear description

### PR Title Format

```
type: brief description

Examples:
- feat: add memory operation tracking
- fix: resolve context propagation in async calls
- docs: update integration guide
- test: add edge case tests for tool calls
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

## Commit Message Guidelines

We follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

Examples:

```
feat(sdk): add auto-instrumentation for OpenAI client

Add instrument_llm() function to automatically wrap OpenAI
client methods for tracing. This reduces boilerplate code
for users.

Closes #123
```

```
fix(backend): handle missing metadata in TraceData

Ensure backward compatibility with older SDK versions
that don't send metadata field.
```

## Questions?

- Open an issue for bug reports or feature requests
- Start a discussion for questions or ideas
- Join our community chat (coming soon)

Thank you for contributing to AgentScope!
