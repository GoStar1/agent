"""Grading node for homework evaluation."""
import json
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import AgentState
from app.services.llm_service import llm_service
from app.core.prompts import GRADING_PROMPT


async def grading_node(state: AgentState) -> AgentState:
    """Grade student's homework.

    Args:
        state: Current agent state

    Returns:
        Updated state with grading results
    """
    # Get the last user message (student's answer)
    messages = state["messages"]
    student_answer = messages[-1].content if messages else ""

    # For now, we'll grade based on the context
    # In a real implementation, you'd need to track the question being answered

    prompt = f"""请评估以下学生答案的质量：

学生答案：
{student_answer}

请提供：
1. 评分 (0-100)
2. 详细反馈
3. 优点
4. 需要改进的地方

以JSON格式返回：
{{
    "score": 分数,
    "feedback": "详细反馈",
    "strengths": ["优点1", "优点2"],
    "improvements": ["改进建议1", "改进建议2"]
}}
"""

    try:
        # Generate grading
        messages_for_llm = [HumanMessage(content=prompt)]
        response = await llm_service.generate(messages_for_llm, temperature=0.3)

        # Try to parse JSON response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "score": 70,
                "feedback": response,
                "strengths": [],
                "improvements": []
            }

        state["grading_result"] = result

        # Format response message
        response_text = f"""**作业批改结果**

评分：{result.get('score', 0)}/100

反馈：
{result.get('feedback', '')}

"""
        if result.get('strengths'):
            response_text += "\n优点：\n"
            for strength in result['strengths']:
                response_text += f"- {strength}\n"

        if result.get('improvements'):
            response_text += "\n改进建议：\n"
            for improvement in result['improvements']:
                response_text += f"- {improvement}\n"

        # Add response to messages
        state["messages"].append(AIMessage(content=response_text))
        state["response"] = response_text

    except Exception as e:
        print(f"Grading error: {e}")
        error_msg = "抱歉，批改作业时出现错误，请稍后再试。"
        state["messages"].append(AIMessage(content=error_msg))
        state["response"] = error_msg

    return state
