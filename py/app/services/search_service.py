"""Search service using SerpAPI."""
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from app.config import settings


class SearchService:
    """Service for web search using SerpAPI."""

    def __init__(self):
        """Initialize search service."""
        self.api_key = settings.serpapi_api_key

    def search(
        self,
        query: str,
        num_results: int = 5,
        language: str = "zh-cn"
    ) -> List[Dict]:
        """Perform a web search.

        Args:
            query: Search query
            num_results: Number of results to return
            language: Search language

        Returns:
            List of search results
        """
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "hl": language,
            })

            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            formatted_results = []
            for result in organic_results[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                })

            return formatted_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def format_results(self, results: List[Dict]) -> str:
        """Format search results into a readable string.

        Args:
            results: List of search results

        Returns:
            Formatted string
        """
        if not results:
            return "未找到相关搜索结果。"

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"[搜索结果 {i}]\n"
                f"标题: {result['title']}\n"
                f"链接: {result['link']}\n"
                f"摘要: {result['snippet']}\n"
            )

        return "\n".join(formatted)


# Global search service instance
search_service = SearchService()
