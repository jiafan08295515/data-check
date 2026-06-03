"""agent.py —— 一个完整的文件探索 Agent，可直接运行"""
# pip install arcana-agent
# export DEEPSEEK_API_KEY="sk-..."
import arcana, asyncio, os, subprocess
WORKSPACE = os.getcwd()

# ━━━ 安全检查 ━━━
def safe_path(path):
    abs_path = os.path.realpath(os.path.join(WORKSPACE, path))
    if not abs_path.startswith(WORKSPACE):
        return None, "错误：不允许访问项目目录之外的文件"
    return abs_path, None

# ━━━ 工具定义 ━━━
@arcana.tool(when_to_use="当需要了解项目目录结构时")
def list_dir(path: str) -> str:
    """列出指定目录下的文件和子目录。path 是相对于项目根目录的路径，如 'src' 或 '.'"""
    p, err = safe_path(path)
    if err: return err
    if not os.path.isdir(p): return "错误：目录不存在。"
    return "\n".join(os.listdir(p)[:100]) or "(空目录)"

@arcana.tool(when_to_use="当需要读取文件内容时")
def read_file(path: str, offset: int = 0) -> str:
    """读取一个文件的内容，返回带行号的文本。文件过大时只返回前 200 行。"""
    p, err = safe_path(path)
    if err: return err
    if not os.path.isfile(p):
        return f"错误：文件不存在。当前目录包含: {', '.join(os.listdir(os.path.dirname(p))[:20])}"
    with open(p) as f:
        lines = f.readlines()
    chunk = lines[offset:offset+200]
    numbered = "".join(f"{i+offset+1}\t{l}" for i, l in enumerate(chunk))
    if offset + 200 < len(lines):
        numbered += f"\n(共 {len(lines)} 行，当前显示 {offset+1}-{offset+len(chunk)}。用 offset={offset+200} 继续)"
    return numbered

@arcana.tool(when_to_use="当需要搜索包含指定文本的文件时")
def search_files(pattern: str, glob: str = "") -> str:
    """在项目中搜索包含指定文本的文件。返回匹配的文件名和行内容。"""
    cmd = ["grep", "-rn", pattern, WORKSPACE]
    if glob:
        cmd = ["grep", "-rn", f"--include={glob}", pattern, WORKSPACE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split("\n")[:30]
        return "\n".join(lines) if lines[0] else "没有找到匹配结果。"
    except subprocess.TimeoutExpired:
        return "搜索超时，请缩小搜索范围。"

# ━━━ 运行 Agent ━━━
task = input("请输入任务:找出所有 TODO 注释"或"这个项目的入口文件是哪个")
result = asyncio.run(arcana.run(
    task,
    tools=[list_dir, read_file, search_files],
    system="你是一个文件探索助手。使用工具来完成用户的任务。每一步先思考再行动。",
    max_turns=20,
    max_cost_usd=1.00
))
print(f"\n{'='*50}\n{result.output}")