"""Mathematical calculation tool with safe expression evaluation."""

import ast
import math
import operator
from typing import Any, Dict, Optional, Type, Union

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class MathInput(BaseModel):
    """Input schema for math calculation tool."""

    expression: str = Field(
        description="Mathematical expression to evaluate. Supports +, -, *, /, **, %, sqrt, sin, cos, tan, log, exp, abs, round, floor, ceil, pi, e"
    )
    precision: int = Field(
        default=6, description="Number of decimal places in the result", ge=0, le=15
    )


class SafeMathEvaluator:
    """Safe evaluator for mathematical expressions."""

    # Allowed binary operators
    OPERATORS: Dict[type, Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Allowed functions
    FUNCTIONS: Dict[str, Any] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "pow": pow,
        "min": min,
        "max": max,
        "sum": sum,
        "radians": math.radians,
        "degrees": math.degrees,
    }

    # Allowed constants
    CONSTANTS: Dict[str, float] = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
    }

    def evaluate(self, expression: str) -> Union[float, int]:
        """Safely evaluate a mathematical expression."""
        try:
            # Parse the expression
            tree = ast.parse(expression, mode="eval")

            # Evaluate the AST
            result = self._eval_node(tree.body)

            return result

        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):
            # Handle numeric constants
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.Name):
            # Handle named constants (pi, e, etc.)
            if node.id in self.CONSTANTS:
                return self.CONSTANTS[node.id]
            raise ValueError(f"Unknown constant: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Handle binary operations (+, -, *, /, etc.)
            if type(node.op) not in self.OPERATORS:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_func = self.OPERATORS[type(node.op)]

            # Check for division by zero
            if isinstance(node.op, (ast.Div, ast.FloorDiv)) and right == 0:
                raise ValueError("Division by zero")

            return op_func(left, right)

        elif isinstance(node, ast.UnaryOp):
            # Handle unary operations (-, +)
            if type(node.op) not in self.OPERATORS:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

            operand = self._eval_node(node.operand)
            return self.OPERATORS[type(node.op)](operand)

        elif isinstance(node, ast.Call):
            # Handle function calls (sqrt, sin, etc.)
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported")

            func_name = node.func.id
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"Unknown function: {func_name}")

            # Evaluate arguments
            args = [self._eval_node(arg) for arg in node.args]

            return self.FUNCTIONS[func_name](*args)

        elif isinstance(node, ast.List):
            # Handle lists for functions like min, max, sum
            return [self._eval_node(elem) for elem in node.elts]

        elif isinstance(node, ast.Tuple):
            # Handle tuples
            return tuple(self._eval_node(elem) for elem in node.elts)

        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class MathTool(BaseTool):
    """Tool for performing mathematical calculations safely."""

    name: str = "calculator"
    description: str = """
    Perform mathematical calculations with high precision.
    Use this tool when you need to:
    - Calculate arithmetic expressions (+, -, *, /, **, %)
    - Compute trigonometric functions (sin, cos, tan, etc.)
    - Calculate logarithms and exponentials
    - Work with mathematical constants (pi, e)
    - Perform statistical operations (min, max, sum)

    Examples:
    - "2 + 3 * 4" → 14
    - "sqrt(16) + pi" → 7.141593
    - "sin(radians(45))" → 0.707107
    - "log(100, 10)" → 2.0
    """
    args_schema: Type[BaseModel] = MathInput
    return_direct: bool = False

    _evaluator: SafeMathEvaluator = SafeMathEvaluator()

    def _run(
        self,
        expression: str,
        precision: int = 6,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute mathematical calculation."""
        try:
            # Clean up the expression
            clean_expr = expression.strip()

            # Evaluate the expression
            result = self._evaluator.evaluate(clean_expr)

            # Format the result
            if isinstance(result, float):
                if result.is_integer():
                    formatted = str(int(result))
                else:
                    formatted = f"{result:.{precision}f}".rstrip("0").rstrip(".")
            else:
                formatted = str(result)

            return f"Result: {formatted}\nExpression: {clean_expr}"

        except ValueError as e:
            return f"Calculation Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

    async def _arun(
        self,
        expression: str,
        precision: int = 6,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute mathematical calculation asynchronously."""
        return self._run(expression=expression, precision=precision, run_manager=run_manager)


# Tool instance
math_tool = MathTool()
