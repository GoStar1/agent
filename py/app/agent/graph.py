"""Main agent graph definition."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes.router import router_node
from app.agent.nodes.rag import rag_node
from app.agent.nodes.search import search_node
from app.agent.nodes.exercise import exercise_node
from app.agent.nodes.grading import grading_node
from app.agent.nodes.explanation import explanation_node


def after_rag(state: AgentState) -> str:
    """Determine next step after RAG retrieval."""
    # If we need search and haven't done it yet
    if state.get("needs_search", False) and not state.get("search_results"):
        return "search"
    else:
        return "explanation"


def route_intent(state: AgentState) -> str:
    """Route based on classified intent."""
    intent = state.get("intent", "knowledge_question")

    if intent == "exercise_request":
        return "exercise"
    elif intent == "grading_request":
        return "grading"
    else:
        # All other intents go through RAG
        return "rag"


def create_agent_graph():
    """Create the main agent graph."""

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("search", search_node)
    workflow.add_node("exercise", exercise_node)
    workflow.add_node("grading", grading_node)
    workflow.add_node("explanation", explanation_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "exercise": "exercise",
            "grading": "grading",
            "rag": "rag",
        }
    )

    # After RAG, decide whether to search or generate
    workflow.add_conditional_edges(
        "rag",
        after_rag,
        {
            "search": "search",
            "explanation": "explanation",
        }
    )

    # Connect other nodes to END
    workflow.add_edge("search", "explanation")
    workflow.add_edge("exercise", END)
    workflow.add_edge("grading", END)
    workflow.add_edge("explanation", END)

    # Compile with memory
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph


# Global agent graph instance
agent_graph = create_agent_graph()
