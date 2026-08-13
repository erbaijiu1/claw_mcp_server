from mcp.server.fastmcp import FastMCP
from tools.pdf_renderer import convert_text_to_pdf
from tools.calendar_todo import (
    get_daily_briefing,
    get_next_n_days_briefing,
    create_task,
    update_task,
    query_tasks,
    get_task_history
)

# 初始化统一的 FastMCP 服务
# 指定聚合服务名为 ClawMCPServer，并在此处绑定 0.0.0.0:9000
mcp = FastMCP("ClawMCPServer", host="0.0.0.0", port=9000)

import asyncio

# 注册 Markdown 转 PDF 渲染接口
@mcp.tool()
async def render_markdown_to_pdf(markdown_content: str = "", pdf_filename: str = "output.pdf") -> str:
    """
    接收排版好的 Markdown 文本，并将其渲染转换为可打印的 PDF 文件保存。

    Args:
        markdown_content (str): 大模型整理排版后的 Markdown 格式纯文本内容。
        pdf_filename (str): 目标输出文件名（例如 "homework.pdf"）。
    """
    # 针对 OpenClaw 或大模型工具调用时漏传参数（如传入 {}）的容错处理
    # 避免引发底层的参数校验异常从而导致 ASGI 服务器崩溃
    if not markdown_content.strip():
        return "❌ 生成失败：传入的 markdown_content 为空。请确保你已正确地在【工具调用参数 (Tool Arguments)】中传递了内容，而不仅仅是把内容打印在了聊天文本里！"

    # 将耗时的 PDF 渲染放入独立线程执行，防止阻塞异步事件循环
    return await asyncio.to_thread(convert_text_to_pdf, markdown_content, pdf_filename)

# 如果未来有其他的接口，可以直接引入并注册
@mcp.tool()
async def mcp_get_daily_briefing(date: str = None) -> dict:
    """
    获取每日简报 (核心工具)。
    OpenClaw 每天早上或当用户问“今天有什么安排”时，优先调用这个接口。
    
    Args:
        date (str, optional): 日期 (YYYY-MM-DD格式)，默认为今天。
        
    Returns:
        dict: 包含逾期任务、今日任务和高优先级任务的聚合结果。
    """
    return await asyncio.to_thread(get_daily_briefing, date)

@mcp.tool()
async def mcp_get_next_n_days_briefing(date: str = None, days: int = 7) -> dict:
    """
    获取未来 N 天简报 (核心工具)。
    OpenClaw 当用户问“未来几天有什么安排”、“这周安排”或“未来N天安排”时，调用这个接口。
    
    Args:
        date (str, optional): 开始日期 (YYYY-MM-DD格式)，默认为今天。
        days (int, optional): 想要查询的未来天数，默认为 7。
        
    Returns:
        dict: 包含逾期任务、未来N天任务和高优先级任务的聚合结果。
    """
    return await asyncio.to_thread(get_next_n_days_briefing, date, days)

@mcp.tool()
async def mcp_create_task(title: str, description: str = None, due_date: str = None, priority: str = "P2-中", category: str = "WORK", tags: list = None) -> dict:
    """
    创建新待办/备忘任务。
    
    Args:
        title (str): 必填，待办标题 (简短清晰)。
        description (str, optional): 详细说明。
        due_date (str, optional): 截止日期 (YYYY-MM-DD 格式，需自动解析如“下周三”的具体日期填入)。
        priority (str, optional): 优先级 (如: P0-紧急, P1-高, P2-中, P3-低)。默认为 P2-中。
        category (str, optional): 分类大类，默认 WORK。建议使用如 WORK, LIFE, STUDY, PERSONAL 等。
        tags (list, optional): 多标签数组，如 ["报销", "重要"]。
    """
    return await asyncio.to_thread(create_task, title, description, due_date, priority, category, tags)

@mcp.tool()
async def mcp_update_task(task_id: str, status: str = None, due_date: str = None, priority: str = None, title: str = None, description: str = None, category: str = None, tags: list = None) -> dict:
    """
    更新或延期待办任务。
    满足“调整结束日期”、“标记完成”的需求。
    
    Args:
        task_id (str): 必填，任务唯一标识。
        status (str, optional): 状态 (TODO, IN_PROGRESS, DONE, CANCELLED)。
        due_date (str, optional): 截止日期 (YYYY-MM-DD)。
        priority (str, optional): 优先级。
        title (str, optional): 新标题。
        description (str, optional): 新描述。
        category (str, optional): 分类大类。
        tags (list, optional): 多标签数组。
    """
    return await asyncio.to_thread(update_task, task_id, status, due_date, priority, title, description, category, tags)

@mcp.tool()
async def mcp_query_tasks(status: str = None, priority: str = None, category: str = None, tag: str = None, keyword: str = None, is_overdue: bool = None) -> list:
    """
    多条件条件查询任务。
    用于查找特定任务，例如所有还在拖延的中等优先级任务。
    
    Args:
        status (str, optional): 状态 (TODO, IN_PROGRESS, DONE, CANCELLED)。
        priority (str, optional): 优先级。
        category (str, optional): 按大类过滤 (如 WORK, LIFE)。
        tag (str, optional): 包含特定标签。
        keyword (str, optional): 搜索关键字(匹配标题和描述)。
        is_overdue (bool, optional): 是否逾期。
    """
    return await asyncio.to_thread(query_tasks, status, priority, category, tag, keyword, is_overdue)

@mcp.tool()
async def mcp_get_task_history(task_id: str) -> list:
    """
    查看任务变更历史。
    满足追踪溯源需求，如查询任务推迟了几次。
    
    Args:
        task_id (str): 必填，任务唯一标识。
    """
    return await asyncio.to_thread(get_task_history, task_id)

if __name__ == "__main__":
    # 使用 SSE 模式运行
    mcp.run(transport='sse')
