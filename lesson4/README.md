# 智能体经典范式演示

本项目实现了三种经典的智能体范式：ReAct、Plan-and-Solve 和 Reflection。

## 项目结构

```
.
├── .env.example          # 环境变量配置示例
├── llm_client.py         # LLM 客户端封装
├── tools.py              # 工具执行器和工具定义
├── react_agent.py        # ReAct 智能体实现
├── plan_and_solve_agent.py  # Plan-and-Solve 智能体实现
├── reflection_agent.py   # Reflection 智能体实现
├── demo.py               # 统一演示脚本
└── README.md             # 本文件
```

## 环境配置

1. 安装依赖：
```bash
pip install openai python-dotenv google-search-results
```

2. 配置环境变量：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：
```
LLM_API_KEY="your-api-key"
LLM_MODEL_ID="your-model-id"
LLM_BASE_URL="your-base-url"
SERPAPI_API_KEY="your-serpapi-key"  # 可选，用于 ReAct 搜索工具
```

## 三种智能体范式

### 1. ReAct (Reasoning and Acting)

**核心思想**：将推理和行动结合，通过 Thought-Action-Observation 循环解决问题。

**工作流程**：
- Thought: 分析当前情况，规划下一步
- Action: 调用工具或输出答案
- Observation: 获取工具执行结果
- 循环直到得出最终答案

**适用场景**：
- 需要外部知识的任务（搜索、查询）
- 需要精确计算的任务
- 需要与 API 交互的任务

**运行示例**：
```bash
python react_agent.py
```

### 2. Plan-and-Solve

**核心思想**：先制定完整计划，然后严格执行。

**工作流程**：
- Planning Phase: 将问题分解为多个步骤
- Solving Phase: 按顺序执行每个步骤

**适用场景**：
- 多步数学应用题
- 需要整合多个信息源的任务
- 结构化的代码生成任务

**运行示例**：
```bash
python plan_and_solve_agent.py
```

### 3. Reflection

**核心思想**：通过反思和优化循环，不断改进解决方案。

**工作流程**：
- Execution: 生成初始解决方案
- Reflection: 评审和发现问题
- Refinement: 根据反馈优化
- 循环直到无需改进

**适用场景**：
- 代码生成与优化
- 需要高质量输出的任务
- 复杂的逻辑推演

**运行示例**：
```bash
python reflection_agent.py
```

## 统一演示

运行交互式演示脚本：
```bash
python demo.py
```

选择要演示的智能体类型，或选择全部演示。

## 注意事项

1. **API 配置**：确保 `.env` 文件中的 API 配置正确
2. **模型选择**：建议使用能力较强的模型（如 GPT-4、Claude 等）
3. **成本控制**：Reflection 模式会多次调用 LLM，注意成本
4. **搜索工具**：ReAct 的搜索功能需要 SerpAPI 密钥（可选）

## 参考文献

- ReAct: Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (2022)
- Plan-and-Solve: Wang et al., "Plan-and-Solve Prompting" (2023)
- Reflection: Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" (2023)
