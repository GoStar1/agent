"""Web search node."""
from app.agent.state import AgentState
from app.services.search_service import search_service


async def search_node(state: AgentState) -> AgentState:
    """Perform web search for additional information.

    Args:
        state: Current agent state

    Returns:
        Updated state with search results
    """
    # Get the last user message
    messages = state["messages"]
    query = messages[-1].content if messages else ""

    # Add subject context to query
    subject = state.get("subject")
    if subject:
        subject_map = {
            "math": "数学",
            "physics": "物理",
            "chemistry": "化学"
        }
        query = f"{subject_map.get(subject, '')} {query}"

    try:
        # Perform search
        results = search_service.search(query, num_results=5)

        # Store results
        state["search_results"] = results

    except Exception as e:
        print(f"Search error: {e}")
        state["search_results"] = []

    return state
