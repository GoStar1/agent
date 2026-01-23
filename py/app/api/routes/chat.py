"""Chat API routes."""
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.agent.graph import agent_graph
from app.agent.state import AgentState
import uuid

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message and get a response.

    Args:
        request: Chat request with message and user info

    Returns:
        Chat response with agent's reply
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Create initial state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "conversation_id": conversation_id,
            "intent": None,
            "subject": None,
            "topic": None,
            "retrieved_docs": None,
            "search_results": None,
            "exercises": None,
            "grading_result": None,
            "needs_search": False,
            "needs_rag": False,
            "confidence": 0.0,
            "response": None,
        }

        # Run the agent graph
        config = {"configurable": {"thread_id": conversation_id}}
        result = await agent_graph.ainvoke(initial_state, config)

        # Extract response
        response_text = result.get("response", "抱歉，我无法生成回答。")

        # Extract sources if available
        sources = []
        if result.get("retrieved_docs"):
            sources.append({"type": "knowledge_base", "count": len(result["retrieved_docs"])})
        if result.get("search_results"):
            sources.extend([
                {"type": "web_search", "title": r.get("title"), "link": r.get("link")}
                for r in result["search_results"]
            ])

        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            sources=sources if sources else None
        )

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation history
    """
    # TODO: Implement conversation history retrieval from database
    return {"conversation_id": conversation_id, "messages": []}
