import os
from typing import Dict, Any, Callable
from dotenv import load_dotenv

load_dotenv()

class ToolExecutor:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: Callable):
        if name in self.tools:
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> Callable:
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


def search(query: str) -> str:
    """网页搜索工具（支持 SerpAPI 或模拟模式）"""
    print(f"🔍 正在执行网页搜索: {query}")

    api_key = os.getenv("SERPAPI_API_KEY")

    # 如果没有配置 API key，使用模拟搜索
    if not api_key:
        return search_mock(query)

    # 使用真实的 SerpAPI
    try:
        from serpapi import SerpApiClient
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",
            "hl": "zh-cn",
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}，切换到模拟模式"


def search_mock(query: str) -> str:
    """模拟搜索工具（用于演示，无需 API key）"""
    print("  ℹ️  使用模拟搜索模式（未配置 SERPAPI_API_KEY）")

    # 简单的关键词匹配返回模拟结果
    mock_data = {
        "华为": "[1] 华为最新旗舰手机\n华为 Mate 70 系列是华为最新发布的旗舰手机，搭载麒麟芯片，支持卫星通信，拍照性能出色。\n\n[2] 华为手机官网\n华为手机包括 Mate 系列、P 系列、nova 系列等多个产品线。",
        "天气": "今天天气晴朗，气温 20-28°C，适合外出活动。",
        "python": "[1] Python 官方文档\nPython 是一种广泛使用的高级编程语言，以其简洁的语法和强大的功能而闻名。\n\n[2] Python 教程\n学习 Python 编程的最佳资源。",
    }

    # 查找匹配的关键词
    for keyword, result in mock_data.items():
        if keyword in query.lower():
            return result

    return f"模拟搜索结果：关于 '{query}' 的信息。这是一个演示性的回答，实际使用请配置 SERPAPI_API_KEY。"


def calculator(expression: str) -> str:
    """简单计算器工具"""
    print(f"🔢 正在计算: {expression}")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"
