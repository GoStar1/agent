"""Prompt templates for the agent."""

# System prompt for the student learning agent
SYSTEM_PROMPT = """你是一个专业的学生学习助手，专注于数学、物理和化学三个学科。

你的职责包括：
1. 回答学生关于数学、物理、化学的问题
2. 提供清晰的概念解释和例子
3. 生成练习题帮助学生巩固知识
4. 批改学生的作业并提供详细反馈
5. 追踪学生的学习进度并给出建议

回答时请：
- 使用清晰、易懂的语言
- 提供具体的例子和步骤
- 鼓励学生独立思考
- 指出常见错误和注意事项
"""

# Intent classification prompt
INTENT_CLASSIFICATION_PROMPT = """分析用户的输入，判断用户的意图。

可能的意图类型：
1. knowledge_question: 询问知识点、概念解释
2. problem_solving: 需要帮助解决具体问题
3. exercise_request: 请求生成练习题
4. grading_request: 请求批改作业
5. explanation_request: 请求详细解释某个概念
6. progress_inquiry: 询问学习进度

用户输入: {user_input}

请以JSON格式返回：
{{
    "intent": "意图类型",
    "subject": "学科(math/physics/chemistry)",
    "topic": "具体主题(如果能识别)",
    "confidence": 0.0-1.0
}}
"""

# RAG prompt template
RAG_PROMPT = """基于以下参考资料回答学生的问题。

参考资料：
{context}

学生问题：{question}

请提供准确、详细的回答。如果参考资料中没有相关信息，请说明并尝试基于你的知识回答。
"""

# Exercise generation prompt
EXERCISE_GENERATION_PROMPT = """为学生生成{difficulty}难度的{subject}练习题。

主题：{topic}
题目类型：{exercise_type}
题目数量：{count}

要求：
1. 题目要有针对性，覆盖该主题的关键知识点
2. 提供详细的解答步骤
3. 标注每道题的知识点

请以JSON格式返回：
{{
    "exercises": [
        {{
            "question": "题目内容",
            "type": "题目类型",
            "answer": "正确答案",
            "explanation": "详细解答",
            "knowledge_points": ["知识点1", "知识点2"]
        }}
    ]
}}
"""

# Grading prompt
GRADING_PROMPT = """批改学生的作业。

题目：{question}
标准答案：{correct_answer}
学生答案：{student_answer}

请评估学生的答案并提供：
1. 分数 (0-100)
2. 详细反馈
3. 指出错误之处
4. 给出改进建议

以JSON格式返回：
{{
    "score": 分数,
    "feedback": "详细反馈",
    "errors": ["错误1", "错误2"],
    "suggestions": ["建议1", "建议2"]
}}
"""

# Explanation prompt
EXPLANATION_PROMPT = """为学生详细解释以下概念。

学科：{subject}
概念：{concept}

请提供：
1. 概念的定义
2. 通俗易懂的解释
3. 具体例子
4. 常见误区
5. 相关知识点

使用清晰的结构和语言，帮助学生理解。
"""

# Search query generation prompt
SEARCH_QUERY_PROMPT = """基于学生的问题，生成适合网络搜索的查询词。

学生问题：{question}

生成3个不同角度的搜索查询词，以JSON格式返回：
{{
    "queries": ["查询词1", "查询词2", "查询词3"]
}}
"""
