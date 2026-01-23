#!/usr/bin/env python3
"""Test the API with different queries."""
import requests
import json

API_URL = "http://localhost:8000/api/chat/message"

def ask_question(question: str, user_id: str = "test_user"):
    """Send a question to the agent."""
    payload = {
        "message": question,
        "user_id": user_id
    }

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print('='*60)

    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        print(f"\nResponse:\n{result['response']}")

        if result.get('sources'):
            print(f"\nSources: {result['sources']}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    # 测试不同类型的问题

    # 1. 知识问答
    ask_question("什么是二次函数？请简单解释")

    # 2. 练习题生成
    ask_question("给我生成3道关于二次函数的练习题")

    # 3. 概念解释
    ask_question("为什么抛物线的顶点公式是 x = -b/2a？")

    # 4. 物理问题
    ask_question("什么是牛顿第二定律？")
