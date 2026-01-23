"""RAG retrieval node."""
from app.agent.state import AgentState
from app.services.rag_service import rag_service


async def rag_node(state: AgentState) -> AgentState:
    """Retrieve relevant documents from vector store.

    Args:
        state: Current agent state

    Returns:
        Updated state with retrieved documents
    """
    # Get the last user message
    messages = state["messages"]
    query = messages[-1].content if messages else ""

    # Get subject filter
    subject = state.get("subject")

    try:
        # Retrieve relevant documents
        documents = await rag_service.retrieve(
            query=query,
            subject=subject,
            k=5
        )

        # Format documents as context
        if documents:
            context = rag_service.format_context(documents)
            state["retrieved_docs"] = [context]
            state["needs_search"] = False  # Found relevant docs, no need for search
        else:
            state["retrieved_docs"] = []
            state["needs_search"] = True  # No docs found, try web search

    except Exception as e:
        print(f"RAG retrieval error: {e}")
        state["retrieved_docs"] = []
        state["needs_search"] = True

    return state
