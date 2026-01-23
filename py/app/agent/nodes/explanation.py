"""Explanation node for generating responses."""
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agent.state import AgentState
from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.core.prompts import SYSTEM_PROMPT, RAG_PROMPT


async def explanation_node(state: AgentState) -> AgentState:
    """Generate explanation/response based on retrieved context.

    Args:
        state: Current agent state

    Returns:
        Updated state with generated response
    """
    # Get the last user message
    messages = state["messages"]
    user_question = messages[-1].content if messages else ""

    # Build context from RAG and search results
    context_parts = []

    # Add RAG context
    retrieved_docs = state.get("retrieved_docs", [])
    if retrieved_docs:
        context_parts.append("**知识库资料：**\n" + "\n".join(retrieved_docs))

    # Add search results
    search_results = state.get("search_results", [])
    if search_results:
        formatted_search = search_service.format_results(search_results)
        context_parts.append("**网络搜索结果：**\n" + formatted_search)

    # Combine context
    context = "\n\n".join(context_parts) if context_parts else "无相关参考资料"

    # Create prompt
    prompt = RAG_PROMPT.format(
        context=context,
        question=user_question
    )

    try:
        # Generate response
        messages_for_llm = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        response = await llm_service.generate(messages_for_llm, temperature=0.7)

        # Add response to messages
        state["messages"].append(AIMessage(content=response))
        state["response"] = response

    except Exception as e:
        print(f"Explanation generation error: {e}")
        error_msg = "抱歉，生成回答时出现错误，请稍后再试。"
        state["messages"].append(AIMessage(content=error_msg))
        state["response"] = error_msg

    return state
