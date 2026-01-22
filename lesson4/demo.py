#!/usr/bin/env python3
"""
智能体范式演示脚本
实现了三种经典的智能体范式：ReAct、Plan-and-Solve、Reflection
"""

from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search, calculator
from react_agent import ReActAgent
from plan_and_solve_agent import PlanAndSolveAgent
from reflection_agent import ReflectionAgent


def demo_react():
    """演示 ReAct 智能体"""
    print("\n" + "=" * 60)
    print("演示 1: ReAct 智能体 (Reasoning and Acting)")
    print("=" * 60)
    print("\nReAct 将推理和行动结合，通过 Thought-Action-Observation 循环解决问题")

    llm_client = HelloAgentsLLM()
    tool_executor = ToolExecutor()

    tool_executor.registerTool(
        "Search",
        "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。",
        search
    )
    tool_executor.registerTool(
        "Calculator",
        "一个计算器工具。当你需要进行数学计算时，应使用此工具。输入应为数学表达式。",
        calculator
    )

    agent = ReActAgent(llm_client, tool_executor, max_steps=5)

    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    print(f"\n问题: {question}")
    agent.run(question)


def demo_plan_and_solve():
    """演示 Plan-and-Solve 智能体"""
    print("\n" + "=" * 60)
    print("演示 2: Plan-and-Solve 智能体")
    print("=" * 60)
    print("\nPlan-and-Solve 先制定完整计划，然后逐步执行")

    llm_client = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llm_client)

    question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
    agent.run(question)


def demo_reflection():
    """演示 Reflection 智能体"""
    print("\n" + "=" * 60)
    print("演示 3: Reflection 智能体")
    print("=" * 60)
    print("\nReflection 通过反思和优化循环，不断改进解决方案")

    llm_client = HelloAgentsLLM()
    agent = ReflectionAgent(llm_client, max_iterations=2)

    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("智能体经典范式演示")
    print("=" * 60)
    print("\n本演示实现了三种经典的智能体范式：")
    print("1. ReAct - 推理与行动结合")
    print("2. Plan-and-Solve - 先规划后执行")
    print("3. Reflection - 反思与优化")
    print("\n请选择要演示的智能体：")
    print("1 - ReAct")
    print("2 - Plan-and-Solve")
    print("3 - Reflection")
    print("4 - 全部演示")
    print("0 - 退出")

    try:
        choice = input("\n请输入选项 (0-4): ").strip()

        if choice == "1":
            demo_react()
        elif choice == "2":
            demo_plan_and_solve()
        elif choice == "3":
            demo_reflection()
        elif choice == "4":
            demo_react()
            demo_plan_and_solve()
            demo_reflection()
        elif choice == "0":
            print("退出演示")
            return
        else:
            print("无效选项")
            return

        print("\n" + "=" * 60)
        print("演示完成")
        print("=" * 60)

    except ValueError as e:
        print(f"\n初始化错误: {e}")
        print("请确保在 .env 文件中配置了以下环境变量：")
        print("- LLM_API_KEY")
        print("- LLM_MODEL_ID")
        print("- LLM_BASE_URL")
        print("\n参考 .env.example 文件进行配置")
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")


if __name__ == '__main__':
    main()
