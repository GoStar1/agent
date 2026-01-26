"""Web search tool using Tavily API."""

from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from tavily import TavilyClient

from app.core.config import settings


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""

    query: str = Field(description="The search query to look up on the web")
    max_results: int = Field(
        default=5, description="Maximum number of results to return", ge=1, le=10
    )
    search_depth: str = Field(
        default="basic",
        description="Search depth: 'basic' for quick results or 'advanced' for thorough search",
    )
    include_domains: Optional[List[str]] = Field(
        default=None, description="List of domains to include in search"
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None, description="List of domains to exclude from search"
    )


class WebSearchTool(BaseTool):
    """Tool for searching the web using Tavily API."""

    name: str = "web_search"
    description: str = """
    Search the web for current information, news, articles, and data.
    Use this tool when you need:
    - Current events or recent news
    - Real-time data or statistics
    - Information that may have changed since your training
    - Verification of facts from online sources

    Returns a list of relevant search results with titles, URLs, and content snippets.
    """
    args_schema: Type[BaseModel] = WebSearchInput
    return_direct: bool = False

    _client: Optional[TavilyClient] = None

    def __init__(self, **kwargs):
        """Initialize the web search tool."""
        super().__init__(**kwargs)
        if settings.tavily_api_key:
            self._client = TavilyClient(api_key=settings.tavily_api_key)

    def _run(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute web search synchronously."""
        if not self._client:
            return "Error: Tavily API key not configured. Please set TAVILY_API_KEY environment variable."

        try:
            response = self._client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )

            return self._format_results(response)

        except Exception as e:
            return f"Error performing web search: {str(e)}"

    async def _arun(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute web search asynchronously."""
        # Tavily client is sync, so we just call the sync version
        return self._run(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            run_manager=run_manager,
        )

    def _format_results(self, response: Dict[str, Any]) -> str:
        """Format search results into a readable string."""
        if not response.get("results"):
            return "No results found for the search query."

        formatted_results = []
        for i, result in enumerate(response["results"], 1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "No content available")

            formatted_results.append(
                f"[{i}] {title}\n"
                f"    URL: {url}\n"
                f"    Content: {content[:500]}{'...' if len(content) > 500 else ''}"
            )

        return "\n\n".join(formatted_results)


# Tool instance
web_search_tool = WebSearchTool()
