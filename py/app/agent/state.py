"""Agent state definition for LangGraph."""
from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the student learning agent."""

    # Messages in the conversation
    messages: Annotated[List[BaseMessage], add_messages]

    # User information
    user_id: str
    conversation_id: Optional[str]

    # Intent and routing
    intent: Optional[str]  # knowledge_question, exercise_request, etc.
    subject: Optional[str]  # math, physics, chemistry
    topic: Optional[str]  # specific topic

    # Retrieved context
    retrieved_docs: Optional[List[str]]
    search_results: Optional[List[dict]]

    # Generated content
    exercises: Optional[List[dict]]
    grading_result: Optional[dict]

    # Metadata
    needs_search: bool
    needs_rag: bool
    confidence: float

    # Final response
    response: Optional[str]
