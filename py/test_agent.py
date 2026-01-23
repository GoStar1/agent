"""Simple test script to verify the agent setup."""
import asyncio
from langchain_core.messages import HumanMessage
from app.agent.graph import agent_graph
from app.agent.state import AgentState


async def test_agent():
    """Test the agent with a simple question."""
    print("Testing Student Learning Agent...\n")

    # Test question
    test_message = "什么是二次函数？请简单解释一下。"
    print(f"Question: {test_message}\n")

    # Create initial state
    initial_state: AgentState = {
        "messages": [HumanMessage(content=test_message)],
        "user_id": "test_user",
        "conversation_id": "test_conversation",
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

    try:
        # Run the agent
        print("Running agent...\n")
        config = {"configurable": {"thread_id": "test_thread"}}
        result = await agent_graph.ainvoke(initial_state, config)

        # Print results
        print("=" * 60)
        print("AGENT RESPONSE:")
        print("=" * 60)
        print(result.get("response", "No response generated"))
        print("\n" + "=" * 60)
        print("METADATA:")
        print("=" * 60)
        print(f"Intent: {result.get('intent')}")
        print(f"Subject: {result.get('subject')}")
        print(f"Topic: {result.get('topic')}")
        print(f"Used RAG: {bool(result.get('retrieved_docs'))}")
        print(f"Used Search: {bool(result.get('search_results'))}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent())
