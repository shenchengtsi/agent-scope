"""Data models for AgentScope."""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid
import json


class StepType(str, Enum):
    """Types of execution steps."""
    # Basic steps
    INPUT = "input"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    OUTPUT = "output"
    ERROR = "error"
    THINKING = "thinking"
    
    # Enhanced monitoring steps
    SKILL_LOADING = "skill_loading"       # Skills 加载详情
    PROMPT_BUILD = "prompt_build"         # Prompt 构建过程
    TOOL_SELECTION = "tool_selection"     # Tool 选择决策
    MEMORY_OPERATION = "memory_operation" # Memory 读写操作
    SUBAGENT_CALL = "subagent_call"       # Sub-agent 调用
    REASONING = "reasoning"               # 推理/思考过程


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


# =============================================================================
# Enhanced Monitoring Data Models
# =============================================================================

@dataclass
class SkillInfo:
    """Skill 信息"""
    name: str
    description: str = ""
    status: str = "loaded"  # loaded, failed, loading
    error: Optional[str] = None
    load_time_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "error": self.error,
            "load_time_ms": self.load_time_ms,
        }


@dataclass
class PromptMessage:
    """Prompt Message 结构"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None  # for tool messages
    tool_calls: Optional[List[Dict]] = None  # assistant's tool calls
    tool_call_id: Optional[str] = None  # tool response id

    def to_dict(self) -> Dict:
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class PromptBuildInfo:
    """Prompt 构建信息"""
    messages: List[PromptMessage] = field(default_factory=list)
    system_prompt: str = ""
    context_window: int = 0
    max_tokens: int = 0
    temperature: float = 0.0
    top_p: float = 0.0
    model: str = ""

    def to_dict(self) -> Dict:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "system_prompt": self.system_prompt,
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "model": self.model,
        }


@dataclass
class ToolSelectionInfo:
    """Tool 选择决策信息"""
    selected_tool: str
    available_tools: List[Dict] = field(default_factory=list)  # 所有可用 tools 列表
    selection_reason: str = ""   # 选择原因/模型思考过程
    confidence: float = 0.0      # 置信度（如果有）
    tool_call_id: str = ""       # 关联的 tool call ID

    def to_dict(self) -> Dict:
        return {
            "selected_tool": self.selected_tool,
            "available_tools": self.available_tools,
            "selection_reason": self.selection_reason,
            "confidence": self.confidence,
            "tool_call_id": self.tool_call_id,
        }


@dataclass
class MemoryOperationInfo:
    """Memory 操作详情"""
    operation: str = ""  # read, write, delete, search, consolidate
    key: str = ""
    namespace: str = "default"
    data_preview: str = ""       # 数据摘要（前500字符）
    tokens_affected: int = 0
    operation_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "operation": self.operation,
            "key": self.key,
            "namespace": self.namespace,
            "data_preview": self.data_preview,
            "tokens_affected": self.tokens_affected,
            "operation_details": self.operation_details,
        }


@dataclass
class SubAgentCallInfo:
    """Sub-agent 调用信息"""
    agent_name: str = ""
    agent_id: str = ""
    input_query: str = ""
    child_trace_id: Optional[str] = None  # 关联的子 trace
    timeout: float = 0.0
    result_preview: str = ""  # 执行结果摘要

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "input_query": self.input_query,
            "child_trace_id": self.child_trace_id,
            "timeout": self.timeout,
            "result_preview": self.result_preview,
        }


@dataclass
class ReasoningInfo:
    """推理/思考过程信息"""
    reasoning_content: str = ""      # 原始推理内容
    reasoning_type: str = ""         # chain_of_thought, plan, reflection
    plan_steps: List[str] = field(default_factory=list)  # 如果是 plan，记录步骤
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "reasoning_content": self.reasoning_content,
            "reasoning_type": self.reasoning_type,
            "plan_steps": self.plan_steps,
            "confidence": self.confidence,
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
    
    # Enhanced monitoring fields
    prompt_info: Optional[PromptBuildInfo] = None
    skill_info: Optional[List[SkillInfo]] = None
    tool_selection: Optional[ToolSelectionInfo] = None
    memory_info: Optional[MemoryOperationInfo] = None
    subagent_info: Optional[SubAgentCallInfo] = None
    reasoning_info: Optional[ReasoningInfo] = None
    
    # Hierarchical structure
    sub_steps: List['ExecutionStep'] = field(default_factory=list)
    parent_step_id: Optional[str] = None
    depth: int = 0

    def to_dict(self) -> Dict:
        # Format timestamp with UTC indicator (Z suffix) so frontend knows it's UTC
        timestamp_str = self.timestamp.isoformat() + 'Z' if self.timestamp else None
        
        result = {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "timestamp": timestamp_str,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "latency_ms": self.latency_ms,
            "tool_call": self.tool_call.to_dict() if self.tool_call else None,
            "metadata": self.metadata,
            "status": self.status.value,
            # Enhanced fields
            "prompt_info": self.prompt_info.to_dict() if self.prompt_info else None,
            "skill_info": [s.to_dict() for s in self.skill_info] if self.skill_info else None,
            "tool_selection": self.tool_selection.to_dict() if self.tool_selection else None,
            "memory_info": self.memory_info.to_dict() if self.memory_info else None,
            "subagent_info": self.subagent_info.to_dict() if self.subagent_info else None,
            "reasoning_info": self.reasoning_info.to_dict() if self.reasoning_info else None,
            # Hierarchy
            "sub_steps": [s.to_dict() for s in self.sub_steps],
            "parent_step_id": self.parent_step_id,
            "depth": self.depth,
        }
        return result


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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Hierarchical structure
    parent_trace_id: Optional[str] = None
    child_trace_ids: List[str] = field(default_factory=list)
    depth: int = 0  # 嵌套深度
    
    # Statistics
    cost_estimate: float = 0.0  # 预估成本（USD）
    context_window_usage: float = 0.0  # 上下文窗口使用率（0-1）
    llm_call_count: int = 0
    tool_call_count: int = 0

    def add_step(self, step: ExecutionStep):
        """Add a step to the trace."""
        self.steps.append(step)
        self.total_tokens += step.tokens_input + step.tokens_output
        
        # Update counters
        if step.type == StepType.LLM_CALL:
            self.llm_call_count += 1
        elif step.type == StepType.TOOL_CALL:
            self.tool_call_count += 1

    def finish(self, status: Status = Status.SUCCESS):
        """Mark the trace as finished."""
        self.end_time = datetime.utcnow()
        self.status = status
        if self.start_time:
            self.total_latency_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict:
        # Format timestamps with UTC indicator (Z suffix)
        start_time_str = self.start_time.isoformat() + 'Z' if self.start_time else None
        end_time_str = self.end_time.isoformat() + 'Z' if self.end_time else None
        
        return {
            "id": self.id,
            "name": self.name,
            "tags": self.tags,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "input_query": self.input_query,
            "output_result": self.output_result,
            "metadata": self.metadata,
            # Hierarchy
            "parent_trace_id": self.parent_trace_id,
            "child_trace_ids": self.child_trace_ids,
            "depth": self.depth,
            # Statistics
            "cost_estimate": self.cost_estimate,
            "context_window_usage": self.context_window_usage,
            "llm_call_count": self.llm_call_count,
            "tool_call_count": self.tool_call_count,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)