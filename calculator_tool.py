from typing import Any, Dict
import ast
import operator as op

from tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    """
    Safe calculator tool for basic arithmetic expressions.
    Supported operators:
    +, -, *, /, %, **, unary -
    """

    ALLOWED_OPERATORS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.USub: op.neg,
    }

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates basic arithmetic expressions like 2+2, 10*5, or (8-3)/2."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        expression = (
            args.get("expression")
            or args.get("query")
            or args.get("input")
            or args.get("text")
        )

        if not expression:
            return {"error": "Missing required argument: 'expression'"}

        if not isinstance(expression, str):
            return {"error": "'expression' must be a string"}

        try:
            result = self._safe_eval(expression)
            return {
                "expression": expression,
                "result": result
            }
        except ZeroDivisionError:
            return {"error": "Division by zero is not allowed"}
        except Exception as e:
            return {
                "error": f"Invalid calculation: {str(e)}"
            }

    def get_declaration(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A mathematical expression such as 2+2, 5*8, or (10-4)/3"
                    }
                },
                "required": ["expression"]
            }
        }

    def _safe_eval(self, expression: str) -> float | int:
        """
        Safely evaluate a math expression using Python AST.
        """

        def eval_node(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise TypeError("Only numeric constants are allowed")

            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                operator_type = type(node.op)

                if operator_type not in self.ALLOWED_OPERATORS:
                    raise TypeError(f"Operator {operator_type.__name__} is not allowed")

                return self.ALLOWED_OPERATORS[operator_type](left, right)

            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                operator_type = type(node.op)

                if operator_type not in self.ALLOWED_OPERATORS:
                    raise TypeError(f"Unary operator {operator_type.__name__} is not allowed")

                return self.ALLOWED_OPERATORS[operator_type](operand)

            raise TypeError("Unsupported expression")

        parsed = ast.parse(expression, mode="eval")
        return eval_node(parsed.body)