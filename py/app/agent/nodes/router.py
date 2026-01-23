"""Router node for intent classification."""
import json
import re
from langchain_core.messages import HumanMessage
from app.agent.state import AgentState
from app.services.llm_service import llm_service
from app.core.prompts import INTENT_CLASSIFICATION_PROMPT


def extract_json_from_response(response: str) -> dict:
    """Extract JSON from LLM response that may contain extra text."""
    # Try to find JSON in the response
    json_patterns = [
        r'\{[^{}]*\}',  # Simple JSON object
        r'\{.*?\}',     # Any JSON-like structure
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    return


def classify_intent_simple(message: str) -> dict:
    """Simple rule-based intent classification as fallback."""
    message_lower = message.lower()

    result = {
        "intent": "knowledge_question",
        "subject": None,
        "topic": None,
        "confidence": 0.6
    }

    # Detect intent
    if any(kw in message_lower for kw in ["练习", "题目", "出题", "做题"]):
        result["intent"] = "exercise_request"
    elif any(kw in message_lower for kw in ["批改", "检查", "对不对", "答案是"]):
        result["intent"] = "grading_request"
    elif any(kw in message_lower for kw in ["解释", "什么是", "为什么", "怎么理解"]):
        result["intent"] = "explanation_request"
    elif any(kw in message_lower for kw in ["怎么做", "如何解", "求解", "计算"]):
        result["intent"] = "problem_solving"

    # Detect subject
    if any(kw in message_lower for kw in ["数学", "函数", "方程", "几何", "代数", "微积分"]):
        result["subject"] = "math"
    elif any(kw in message_lower for kw in ["物理", "力学", "电学", "光学", "热学"]):
        result["subject"] = "physics"
    elif any(kw in message_lower for kw in ["化学", "元素", "反应", "分子", "原子"]):
        result["subject"] = "chemistry"

    return result


async def router_node(state: AgentState) -> AgentState:
    """Classify user intent and route to appropriate node.

    Args:
        state: Current agent state

    Returns:
        Updated state with intent information
    """
    # Get the last user message
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    # First try simple rule-based classification
    simple_result = classify_intent_simple(last_message)

    # Try LLM classification for better accuracy
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(user_input=last_message)
        messages_for_llm = [HumanMessage(content=prompt)]
        response = await llm_service.generate(messages_for_llm, temperature=0.3)

        # Try to parse JSON response
        result = extract_json_from_response(response)

        if result:
            # Use LLM result if valid
            state["intent"] = result.get("intent", simple_result["intent"])
            state["subject"] = result.get("subject", simple_result["subject"])
            state["topic"] = result.get("topic", simple_result["topic"])
            state["confidence"] = result.get("confidence", 0.7)
        else:
            # Fall back to simple classification
            state["intent"] = simple_result["intent"]
            state["subject"] = simple_result["subject"]
            state["topic"] = simple_result["topic"]
            state["confidence"] = simple_result["confidence"]

    except Exception as e:
        print(f"LLM classification error: {e}, using rule-based fallback")
        state["intent"] = simple_result["intent"]
        state["subject"] = simple_result["subject"]
        state["topic"] = simple_result["topic"]
        state["confidence"] = simple_result["confidence"]

    # Determine if RAG or search is needed
    if state["intent"] in ["knowledge_question", "explanation_request", "problem_solving"]:
        state["needs_rag"] = True
        state["needs_search"] = state["confidence"] < 0.7
    else:
        state["needs_rag"] = False
        state["needs_search"] = False

    print(f"Router: intent={state['intent']}, subject={state['subject']}, confidence={state['confidence']}")

    return state
