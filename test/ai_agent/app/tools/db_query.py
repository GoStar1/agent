"""Database query tool for structured data retrieval."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db.base import get_db_session


class DBQueryInput(BaseModel):
    """Input schema for database query tool."""

    query_type: str = Field(
        description="Type of query: 'users', 'conversations', 'messages', 'documents', or 'custom'"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filters to apply. E.g., {'user_id': 'uuid', 'limit': 10}",
    )
    fields: Optional[List[str]] = Field(
        default=None, description="Specific fields to return"
    )
    order_by: Optional[str] = Field(
        default=None, description="Field to order results by"
    )
    order_direction: str = Field(
        default="desc", description="Order direction: 'asc' or 'desc'"
    )
    limit: int = Field(default=10, description="Maximum number of results", ge=1, le=100)


class DatabaseQueryTool(BaseTool):
    """Tool for querying the application database."""

    name: str = "database_query"
    description: str = """
    Query the application database to retrieve structured information.
    Use this tool when you need to:
    - Look up user information
    - Retrieve conversation history
    - Search through stored documents
    - Get statistics or counts from the database

    Supported query types:
    - 'users': Query user information
    - 'conversations': Query conversation sessions
    - 'messages': Query chat messages
    - 'documents': Query stored documents/knowledge base

    Always specify appropriate filters to narrow down results.
    """
    args_schema: Type[BaseModel] = DBQueryInput
    return_direct: bool = False

    # Allowed tables and their safe columns
    ALLOWED_QUERIES: Dict[str, Dict[str, Any]] = {
        "users": {
            "table": "users",
            "allowed_fields": [
                "id",
                "username",
                "email",
                "full_name",
                "is_active",
                "created_at",
            ],
            "filter_fields": ["id", "username", "email", "is_active"],
            "default_order": "created_at",
        },
        "conversations": {
            "table": "conversations",
            "allowed_fields": [
                "id",
                "user_id",
                "title",
                "summary",
                "is_active",
                "created_at",
                "updated_at",
            ],
            "filter_fields": ["id", "user_id", "is_active"],
            "default_order": "updated_at",
        },
        "messages": {
            "table": "messages",
            "allowed_fields": [
                "id",
                "conversation_id",
                "role",
                "content",
                "token_count",
                "created_at",
            ],
            "filter_fields": ["conversation_id", "role"],
            "default_order": "created_at",
        },
        "documents": {
            "table": "documents",
            "allowed_fields": [
                "id",
                "title",
                "content",
                "source",
                "doc_type",
                "chunk_index",
                "created_at",
            ],
            "filter_fields": ["id", "doc_type", "source"],
            "default_order": "created_at",
        },
    }

    def _run(
        self,
        query_type: str,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc",
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute database query synchronously."""
        # For sync context, we need to run in an event loop
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create a new task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._execute_query(
                            query_type, filters, fields, order_by, order_direction, limit
                        ),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self._execute_query(
                        query_type, filters, fields, order_by, order_direction, limit
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self._execute_query(
                    query_type, filters, fields, order_by, order_direction, limit
                )
            )

    async def _arun(
        self,
        query_type: str,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc",
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute database query asynchronously."""
        return await self._execute_query(
            query_type, filters, fields, order_by, order_direction, limit
        )

    async def _execute_query(
        self,
        query_type: str,
        filters: Optional[Dict[str, Any]],
        fields: Optional[List[str]],
        order_by: Optional[str],
        order_direction: str,
        limit: int,
    ) -> str:
        """Execute the actual database query."""
        # Validate query type
        if query_type not in self.ALLOWED_QUERIES:
            return f"Error: Invalid query type '{query_type}'. Allowed: {list(self.ALLOWED_QUERIES.keys())}"

        config = self.ALLOWED_QUERIES[query_type]
        table = config["table"]
        allowed_fields = config["allowed_fields"]
        filter_fields = config["filter_fields"]

        # Validate and sanitize fields
        if fields:
            safe_fields = [f for f in fields if f in allowed_fields]
            if not safe_fields:
                safe_fields = allowed_fields
        else:
            safe_fields = allowed_fields

        # Build SELECT clause
        select_clause = ", ".join(safe_fields)

        # Build WHERE clause with parameterized queries
        where_clauses = []
        params = {}

        if filters:
            for key, value in filters.items():
                if key in filter_fields:
                    param_name = f"param_{key}"
                    where_clauses.append(f"{key} = :{param_name}")
                    params[param_name] = value

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Validate order_by
        order_field = order_by if order_by in allowed_fields else config["default_order"]
        order_dir = "DESC" if order_direction.lower() == "desc" else "ASC"

        # Build full query
        query = f"""
            SELECT {select_clause}
            FROM {table}
            WHERE {where_sql}
            ORDER BY {order_field} {order_dir}
            LIMIT :limit
        """
        params["limit"] = limit

        try:
            async with get_db_session() as session:
                result = await session.execute(text(query), params)
                rows = result.fetchall()

                if not rows:
                    return f"No results found for query type '{query_type}' with the given filters."

                # Format results
                formatted_results = []
                for row in rows:
                    row_dict = {}
                    for i, field in enumerate(safe_fields):
                        value = row[i]
                        # Handle special types
                        if isinstance(value, uuid.UUID):
                            value = str(value)
                        elif isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[field] = value
                    formatted_results.append(row_dict)

                return json.dumps(
                    {
                        "query_type": query_type,
                        "count": len(formatted_results),
                        "results": formatted_results,
                    },
                    indent=2,
                    default=str,
                )

        except Exception as e:
            return f"Database query error: {str(e)}"


# Tool instance
db_query_tool = DatabaseQueryTool()
