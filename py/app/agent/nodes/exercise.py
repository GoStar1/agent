"""Exercise generation node."""
import json
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import AgentState
from app.services.llm_service import llm_service
from app.core.prompts import EXERCISE_GENERATION_PROMPT


async def exercise_node(state: AgentState) -> AgentState:
    """Generate practice exercises.

    Args:
        state: Current agent state

    Returns:
        Updated state with generated exercises
    """
    # Get parameters from state
    subject = state.get("subject", "math")
    topic = state.get("topic", "综合")

    # Parse user message for exercise parameters
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    # Determine difficulty and type from message
    difficulty = "intermediate"  # Default
    exercise_type = "short_answer"  # Default
    count = 3  # Default

    if "简单" in last_message or "基础" in last_message:
        difficulty = "beginner"
    elif "困难" in last_message or "高级" in last_message:
        difficulty = "advanced"

    if "选择题" in last_message:
        exercise_type = "mcq"
    elif "证明" in last_message:
        exercise_type = "proof"

    # Map subject to Chinese
    subject_map = {
        "math": "数学",
        "physics": "物理",
        "chemistry": "化学"
    }

    # Create prompt
    prompt = EXERCISE_GENERATION_PROMPT.format(
        difficulty=difficulty,
        subject=subject_map.get(subject, "数学"),
        topic=topic,
        exercise_type=exercise_type,
        count=count
    )

    try:
        # Generate exercises
        messages_for_llm = [HumanMessage(content=prompt)]
        response = await llm_service.generate(messages_for_llm, temperature=0.7)

        # Try to parse JSON response
        try:
            result = json.loads(response)
            exercises = result.get("exercises", [])
        except json.JSONDecodeError:
            # If not valid JSON, use raw response
            exercises = [{"question": response, "answer": "", "explanation": ""}]

        state["exercises"] = exercises

        # Format response message
        response_text = "为你生成了以下练习题：\n\n"
        for i, ex in enumerate(exercises, 1):
            response_text += f"**题目 {i}**\n{ex.get('question', '')}\n\n"

        response_text += "\n完成后可以告诉我你的答案，我来帮你批改！"

        # Add response to messages
        state["messages"].append(AIMessage(content=response_text))
        state["response"] = response_text

    except Exception as e:
        print(f"Exercise generation error: {e}")
        error_msg = "抱歉，生成练习题时出现错误，请稍后再试。"
        state["messages"].append(AIMessage(content=error_msg))
        state["response"] = error_msg

    return state
