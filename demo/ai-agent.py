"""
DeepSeek AI Agent 示例
使用前请设置环境变量：export DEEPSEEK_API_KEY="your-api-key"
"""
from openai import OpenAI
import json
import os
import sys
from datetime import datetime

# 安全获取 API Key
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    print("错误：请设置环境变量 DEEPSEEK_API_KEY")
    print('示例：export DEEPSEEK_API_KEY="your-api-key"')
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 定义工具
tools = [
    {"type": "function", "function": {
        "name": "calculate",
        "description": "计算一个数学表达式，返回结果",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式，如 2+3*4"}
            },
            "required": ["expression"]
        }
    }},
    {"type": "function", "function": {
        "name": "get_time",
        "description": "获取当前日期和时间",
        "parameters": {"type": "object", "properties": {}}
    }}
]


# 安全的数学表达式求值（仅支持数字和 + - * / // % ** 运算符）
def _safe_eval(expression: str) -> float:
    """安全地计算数学表达式，避免 eval() 的代码注入风险"""
    # 仅允许数字、空格、小数点、括号和基本运算符
    allowed_chars = set("0123456789. +-*/%()")
    if not all(c in allowed_chars for c in expression):
        raise ValueError(f"表达式包含不允许的字符: {expression}")
    import ast
    try:
        tree = ast.parse(expression, mode="eval")
        # 确保 AST 只包含安全的节点类型
        allowed_nodes = (
            ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd, ast.Load,
        )
        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                raise ValueError(f"表达式中包含不安全的操作: {type(node).__name__}")
        # 受限的 eval：仅允许内置的算术运算
        return eval(compile(tree, "<expression>", "eval"), {"__builtins__": {}}, {})
    except Exception as e:
        raise ValueError(f"表达式计算失败: {e}")


# 执行工具
def run_tool(name, args):
    if name == "calculate":
        try:
            return str(_safe_eval(args["expression"]))
        except ValueError as e:
            return f"计算错误: {e}"
    if name == "get_time":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Agent 主循环
def main():
    messages = [{"role": "user", "content": "现在几点了？另外帮我算一下 1024 * 768"}]

    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            tools=tools,
            messages=messages
        )
        msg = response.choices[0].message

        # 如果模型不再需要工具 → 结束
        if not msg.tool_calls:
            print(msg.content)
            break

        # 收集工具调用结果
        messages.append(msg)
        for call in msg.tool_calls:
            result = run_tool(call.function.name, json.loads(call.function.arguments))
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result
            })


if __name__ == "__main__":
    main()
