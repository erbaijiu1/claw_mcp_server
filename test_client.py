import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def test_mcp_server():
    # 这是我们 Docker 容器暴露在宿主机的服务地址
    url = "http://127.0.0.1:9000/sse"
    
    print(f"正在尝试连接 MCP SSE 服务器: {url} ...")
    
    # 连接 SSE 服务端
    async with sse_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # 1. 发起协议初始化握手
            print("连接成功！正在进行 MCP 初始化握手...")
            await session.initialize()
            
            # （可选）获取当前服务端支持的工具列表
            tools = await session.list_tools()
            print(f"\n服务端支持的工具列表: {[t.name for t in tools.tools]}")
            
            # 2. 准备测试用的 Markdown 数据
            test_md = """# MCP 渲染测试文档

这是一份通过 MCP Client 发送过来的测试文档。
如果能看到这句话，并且**中文字体**显示正常，说明整个服务打通了！

## 功能点测试
- [x] Markdown 标题解析
- [x] Markdown 列表解析
- [x] **加粗** 和 *斜体*

### 代码块测试
```python
def hello_mcp():
    print("Hello from FastMCP Server!")
```

表格测试：
| 字段 | 说明 |
| --- | --- |
| 测试状态 | 成功 |
| 协议 | SSE |
"""
            
            # 3. 发起 Tool Call 请求
            print("\n正在调用工具 'render_markdown_to_pdf'...")
            result = await session.call_tool(
                "render_markdown_to_pdf",
                arguments={
                    "markdown_content": test_md,
                    "pdf_filename": "test_connection.pdf"
                }
            )
            
            # 4. 打印服务端的返回结果
            print("\n✅ 调用完成！服务端返回信息：")
            # 提取返回的文本内容
            for content in result.content:
                print(f"> {content.text}")
                
            print("\n提示：如果返回成功，请去项目目录下的 data/workspace/ 查看是否生成了 test_connection.pdf！")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
