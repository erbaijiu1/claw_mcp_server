from mcp.server.fastmcp import FastMCP
from tools.pdf_renderer import convert_text_to_pdf

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
# @mcp.tool()
# def other_tool(...): ...

if __name__ == "__main__":
    # 使用 SSE 模式运行
    mcp.run(transport='sse')
