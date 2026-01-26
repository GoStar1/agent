"""ReAct Agent implementation using LangGraph."""

import uuid
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.core.config import settings
from app.db.base import get_db_session
from app.db.crud import ConversationCRUD, MessageCRUD
from app.memory.redis_memory import redis_memory
from app.rag.retriever import rag_manager
from app.tools import db_query_tool, math_tool, web_search_tool


# System prompt for the agent
SYSTEM_PROMPT = """You are an intelligent AI assistant with access to various tools.
Your goal is to help users by:
1. Understanding their questions thoroughly
2. Using appropriate tools when needed
3. Providing accurate, helpful, and well-structured responses

Available tools:
- web_search: Search the web for current information
- calculator: Perform mathematical calculations
- database_query: Query the application database

When using tools:
- Think step by step about what information you need
- Use the most appropriate tool for each task
- Synthesize information from multiple sources when needed
- Always provide clear explanations of your findings

{context}

Be concise but thorough. If you're unsure about something, acknowledge it rather than making things up.
"""


class ReActAgent:
    """ReAct Agent with tool use, RAG, and memory capabilities."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_iterations: int = 10,
        enable_rag: bool = True,
    ):
        """Initialize the ReAct agent."""
        self.model_name = model_name or settings.openai_model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.enable_rag = enable_rag

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=settings.openai_api_key,
            streaming=True,
        )

        # Initialize tools
        self.tools = [web_search_tool, math_tool, db_query_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create graph with state
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("persist", self._persist_conversation)

        # Define edges
        workflow.set_entry_point("retrieve")

        workflow.add_edge("retrieve", "agent")

        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "persist": "persist",
            },
        )

        workflow.add_edge("tools", "agent")
        workflow.add_edge("persist", END)

        return workflow.compile()

    async def _retrieve_context(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve relevant context using RAG."""
        if not self.enable_rag or not state.get("should_retrieve", True):
            return {"retrieved_context": None}

        # Get the last user message
        messages = state.get("messages", [])
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break

        if not user_message:
            return {"retrieved_context": None}

        # Retrieve relevant documents
        try:
            documents = await rag_manager.retrieve(user_message, k=3)
            if documents:
                context = rag_manager.format_context(documents)
                return {"retrieved_context": context}
        except Exception:
            pass

        return {"retrieved_context": None}

    async def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Main agent reasoning node."""
        messages = list(state.get("messages", []))
        context = state.get("retrieved_context", "")

        # Build system message with context
        context_section = ""
        if context:
            context_section = f"\n\nRelevant context from knowledge base:\n{context}"

        system_message = SystemMessage(
            content=SYSTEM_PROMPT.format(context=context_section)
        )

        # Prepare messages for the model
        model_messages = [system_message] + messages

        # Invoke the model
        response = await self.llm_with_tools.ainvoke(model_messages)

        # Track tool calls
        tool_calls_made = state.get("tool_calls_made", [])
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_calls_made.append({
                    "name": tc["name"],
                    "args": tc["args"],
                    "id": tc["id"],
                })

        return {
            "messages": [response],
            "tool_calls_made": tool_calls_made,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    def _should_continue(
        self, state: AgentState
    ) -> Literal["tools", "persist"]:
        """Determine if the agent should continue or finish."""
        messages = state.get("messages", [])
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)

        # Check iteration limit
        if iteration_count >= max_iterations:
            return "persist"

        # Check if the last message has tool calls
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                return "tools"

        return "persist"

    async def _persist_conversation(self, state: AgentState) -> Dict[str, Any]:
        """Persist conversation to long-term storage."""
        session_id = state.get("session_id")
        user_id = state.get("user_id")
        messages = state.get("messages", [])

        if not session_id or not user_id:
            return {}

        try:
            # Save to Redis for session continuity
            for msg in messages[-2:]:  # Save last exchange
                await redis_memory.add_message(session_id, msg)

            # Persist to PostgreSQL for long-term storage
            async with get_db_session() as session:
                # Ensure conversation exists
                conversation = await ConversationCRUD.get_by_id(
                    session, uuid.UUID(session_id)
                )

                if not conversation:
                    conversation = await ConversationCRUD.create(
                        session,
                        user_id=uuid.UUID(user_id),
                        title="New Conversation",
                    )

                # Save messages
                for msg in messages[-2:]:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    await MessageCRUD.create(
                        session,
                        conversation_id=conversation.id,
                        role=role,
                        content=msg.content,
                    )

        except Exception:
            # Log error but don't fail the conversation
            pass

        return {}

    async def run(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the agent with a user message."""
        # Create or use existing session
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or str(uuid.uuid4())

        # Ensure session exists in Redis
        if not await redis_memory.session_exists(session_id):
            await redis_memory.create_session(user_id, session_id)

        # Get conversation history from Redis
        history = await redis_memory.get_recent_messages(session_id, limit=10)

        # Build initial state
        initial_state: AgentState = {
            "messages": list(history) + [HumanMessage(content=message)],
            "session_id": session_id,
            "user_id": user_id,
            "retrieved_context": None,
            "should_retrieve": self.enable_rag,
            "next_action": None,
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
            "tool_calls_made": [],
            "metadata": metadata or {},
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Extract response
        messages = final_state.get("messages", [])
        response_content = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                response_content = msg.content
                break

        return {
            "response": response_content,
            "session_id": session_id,
            "tool_calls": final_state.get("tool_calls_made", []),
            "iterations": final_state.get("iteration_count", 0),
        }

    async def stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent responses."""
        # Create or use existing session
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or str(uuid.uuid4())

        # Ensure session exists in Redis
        if not await redis_memory.session_exists(session_id):
            await redis_memory.create_session(user_id, session_id)

        # Get conversation history from Redis
        history = await redis_memory.get_recent_messages(session_id, limit=10)

        # Build initial state
        initial_state: AgentState = {
            "messages": list(history) + [HumanMessage(content=message)],
            "session_id": session_id,
            "user_id": user_id,
            "retrieved_context": None,
            "should_retrieve": self.enable_rag,
            "next_action": None,
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
            "tool_calls_made": [],
            "metadata": metadata or {},
        }

        # Stream the graph execution
        async for event in self.graph.astream_events(initial_state, version="v2"):
            event_type = event.get("event")

            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield {
                        "type": "token",
                        "content": chunk.content,
                        "session_id": session_id,
                    }

            elif event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "session_id": session_id,
                }

            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                output = event.get("data", {}).get("output", "")
                yield {
                    "type": "tool_end",
                    "tool": tool_name,
                    "output": str(output)[:500],
                    "session_id": session_id,
                }

        yield {
            "type": "done",
            "session_id": session_id,
        }


# Create default agent instance
react_agent = ReActAgent()
