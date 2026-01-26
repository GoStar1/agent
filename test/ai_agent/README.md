# AI Agent - Production-Grade LangChain Agent

A scalable, production-ready AI Agent application built with LangChain, LangGraph, FastAPI, PostgreSQL, and Redis.

## Features

- **ReAct Agent Pattern**: Reasoning and acting loop with LangGraph
- **Multi-level Memory**:
  - Short-term: Redis for session storage
  - Long-term: PostgreSQL for persistent conversations
- **RAG with Hybrid Search**: Combines vector similarity and keyword search
- **Built-in Tools**:
  - Web Search (Tavily)
  - Mathematical Calculator
  - Database Query
- **Streaming Support**: Real-time response streaming via SSE
- **LangSmith Integration**: Full observability and tracing
- **Docker Ready**: Complete Docker Compose setup

## Architecture

```
ai_agent/
├── app/
│   ├── api/              # FastAPI routes
│   │   ├── chat.py       # Chat endpoints
│   │   ├── health.py     # Health checks
│   │   └── rag.py        # RAG endpoints
│   ├── agent/            # LangGraph agent
│   │   ├── react_agent.py
│   │   └── state.py
│   ├── core/             # Configuration
│   │   └── config.py
│   ├── db/               # Database layer
│   │   ├── base.py
│   │   ├── crud.py
│   │   └── models.py
│   ├── memory/           # Memory management
│   │   ├── redis_memory.py
│   │   └── vector_store.py
│   ├── rag/              # RAG retriever
│   │   └── retriever.py
│   ├── schemas/          # Pydantic models
│   │   └── chat.py
│   ├── tools/            # Agent tools
│   │   ├── db_query.py
│   │   ├── math_tool.py
│   │   └── web_search.py
│   └── main.py           # Application entry
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key
- Tavily API Key (for web search)
- LangSmith API Key (optional, for tracing)

### 1. Clone and Setup Environment

```bash
cd ai_agent

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
vim .env
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

### 3. Or Run Locally

```bash
# Install dependencies
pip install -r requirements.txt
# or with Poetry
poetry install

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run the application
uvicorn app.main:app --reload
```

## API Endpoints

### Chat

```bash
# Send a message
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'

# Stream response
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing"}'
```

### Sessions

```bash
# Create session
curl -X POST "http://localhost:8000/api/v1/chat/sessions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123"}'

# Get session
curl "http://localhost:8000/api/v1/chat/sessions/{session_id}"
```

### RAG

```bash
# Ingest document
curl -X POST "http://localhost:8000/api/v1/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Overview",
    "content": "Artificial intelligence is...",
    "doc_type": "article"
  }'

# Search documents
curl "http://localhost:8000/api/v1/rag/search?query=artificial+intelligence&k=5"
```

### Health Check

```bash
curl "http://localhost:8000/health"
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `TAVILY_API_KEY` | Tavily API key | Required for web search |
| `POSTGRES_*` | PostgreSQL connection | See `.env.example` |
| `REDIS_*` | Redis connection | See `.env.example` |
| `LANGCHAIN_*` | LangSmith config | Optional |

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest

# Format code
black app tests
ruff check app tests --fix

# Type checking
mypy app
```

## License

MIT License
