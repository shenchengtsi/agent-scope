"""Data models for AgentScope."""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid
import json


class StepType(str, Enum):
    """Types of execution steps."""
    INPUT = "input"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    OUTPUT = "output"
    ERROR = "error"
    THINKING = "thinking"


class Status(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool/function call."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


@dataclass
class ExecutionStep:
    """A single step in the execution chain."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: StepType = StepType.INPUT
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    tool_call: Optional[ToolCall] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: Status = Status.PENDING

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "latency_ms": self.latency_ms,
            "tool_call": self.tool_call.to_dict() if self.tool_call else None,
            "metadata": self.metadata,
            "status": self.status.value,
        }


@dataclass
class TraceEvent:
    """A complete trace of an Agent execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    tags: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    steps: List[ExecutionStep] = field(default_factory=list)
    status: Status = Status.PENDING
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    input_query: str = ""
    output_result: str = ""

    def add_step(self, step: ExecutionStep):
        """Add a step to the trace."""
        self.steps.append(step)
        self.total_tokens += step.tokens_input + step.tokens_output

    def finish(self, status: Status = Status.SUCCESS):
        """Mark the trace as finished."""
        self.end_time = datetime.utcnow()
        self.status = status
        if self.start_time:
            self.total_latency_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "tags": self.tags,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "input_query": self.input_query,
            "output_result": self.output_result,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)