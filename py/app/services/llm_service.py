"""LLM service for DeepSeek integration via ModelScope API."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.config import settings
from typing import List, AsyncIterator


class LLMService:
    """Service for interacting with DeepSeek LLM."""

    def __init__(self):
        """Initialize LLM service."""
        self.llm = ChatOpenAI(
            model=settings.llm_model_id,
            openai_api_key=settings.llm_api_key,
            openai_api_base=settings.llm_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
            streaming=True
        )

    async def generate(
        self,
        messages: List[BaseMessage],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate a response from the LLM.

        Args:
            messages: List of messages for the conversation
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Generated response text
        """
        llm = self.llm
        if temperature is not None:
            llm = llm.bind(temperature=temperature)
        if max_tokens is not None:
            llm = llm.bind(max_tokens=max_tokens)

        response = await llm.ainvoke(messages)
        return response.content

    async def stream(
        self,
        messages: List[BaseMessage],
        temperature: float = None,
        max_tokens: int = None
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM.

        Args:
            messages: List of messages for the conversation
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Yields:
            Response chunks
        """
        llm = self.llm
        if temperature is not None:
            llm = llm.bind(temperature=temperature)
        if max_tokens is not None:
            llm = llm.bind(max_tokens=max_tokens)

        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    def create_messages(
        self,
        system_prompt: str = None,
        user_message: str = None,
        history: List[dict] = None
    ) -> List[BaseMessage]:
        """Create a list of messages for the LLM.

        Args:
            system_prompt: Optional system prompt
            user_message: User message
            history: Optional conversation history

        Returns:
            List of BaseMessage objects
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        if user_message:
            messages.append(HumanMessage(content=user_message))

        return messages


# Global LLM service instance
llm_service = LLMService()
