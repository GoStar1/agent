"""Agent state definitions for LangGraph."""

from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the ReAct agent."""

    # Conversation messages with automatic message merging
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Session information
    session_id: str
    user_id: str

    # RAG context
    retrieved_context: Optional[str]
    should_retrieve: bool

    # Agent control
    next_action: Optional[str]
    iteration_count: int
    max_iterations: int

    # Tool execution
    tool_calls_made: List[Dict[str, Any]]

    # Metadata
    metadata: Dict[str, Any]


class PlanExecuteState(TypedDict):
    """State for Plan-and-Execute agent pattern."""

    # Core messages
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Session info
    session_id: str
    user_id: str

    # Planning
    plan: List[str]
    current_step: int
    step_results: List[str]

    # Execution
    final_response: Optional[str]
    is_complete: bool

    # RAG
    retrieved_context: Optional[str]

    # Metadata
    metadata: Dict[str, Any]
