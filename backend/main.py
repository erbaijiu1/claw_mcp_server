from mcp.server.fastmcp import FastMCP
from tools.pdf_renderer import convert_text_to_pdf

# 初始化统一的 FastMCP 服务
# 指定聚合服务名为 ClawMCPServer
mcp = FastMCP("ClawMCPServer")

# 注册 Markdown 转 PDF 渲染接口
@mcp.tool()
def render_markdown_to_pdf(markdown_content: str, pdf_filename: str) -> str:
    """
    接收排版好的 Markdown 文本，并将其渲染转换为可打印的 PDF 文件保存。

    Args:
        markdown_content (str): 大模型整理排版后的 Markdown 格式纯文本内容。
        pdf_filename (str): 目标输出文件名（例如 "homework.pdf"）。
    """
    return convert_text_to_pdf(markdown_content, pdf_filename)

# 如果未来有其他的接口，可以直接引入并注册
# @mcp.tool()
# def other_tool(...): ...

if __name__ == "__main__":
    # 使用 SSE 模式运行，监听 9000 端口
    # FastMCP.run() 的底层依赖 starlette/uvicorn 会启动 HTTP Server
    mcp.run(transport='sse')
