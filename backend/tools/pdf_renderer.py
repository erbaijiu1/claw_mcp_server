import os
import markdown
import pdfkit

# 定义数据存储的根目录（容器内目录）
WORKSPACE_DIR = "/app/workspace"

# 确保工作目录存在
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def convert_text_to_pdf(markdown_content: str, pdf_filename: str) -> str:
    """
    接收排版好的 Markdown 文本，并将其渲染转换为可打印的 PDF 文件保存。

    Args:
        markdown_content (str): 大模型整理排版后的 Markdown 格式纯文本内容。
        pdf_filename (str): 目标输出文件名（例如 "homework.pdf"）。
    """
    # 强制将输出文件放到工作目录，防止跨目录写入
    safe_filename = os.path.basename(pdf_filename)
    output_path = os.path.join(WORKSPACE_DIR, safe_filename)

    # 1. Markdown 转 HTML
    # 开启 tables 和 sane_lists 扩展防止格式丢失
    html_body = markdown.markdown(
        markdown_content,
        extensions=['tables', 'sane_lists', 'fenced_code']
    )

    # 2. 构建带中文字体样式的完整 HTML 骨架
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>PDF Document</title>
        <style>
            body {{
                font-family: 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', sans-serif;
                font-size: 16pt; /* 放大一号，从14pt变为16pt，更适合阅读 */
                line-height: 1.6;
                color: #333;
                margin: 0 auto;
            }}
            h1 {{ font-size: 26pt; margin-top: 26pt; margin-bottom: 13pt; }}
            h2 {{ font-size: 22pt; margin-top: 22pt; margin-bottom: 11pt; }}
            h3 {{ font-size: 18pt; margin-top: 18pt; margin-bottom: 9pt; }}
            p, li {{ margin-bottom: 10pt; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20pt;
                font-size: 14pt; /* 表格文字随之放大 */
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10pt; /* 单元格内边距略微放大 */
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                padding: 14pt;
                overflow-x: auto;
                border-radius: 4px;
                font-size: 12pt; /* 代码块也同步放大 */
            }}
            code {{
                font-family: 'Courier New', Courier, monospace;
            }}
            blockquote {{
                border-left: 4px solid #ccc;
                margin: 0 0 16pt 0;
                padding-left: 16pt;
                color: #666;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # 3. 渲染 PDF
    # options 需指定：纸张 A4、边距 0.75in、encoding 为 UTF-8
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'custom-header' : [
            ('Accept-Encoding', 'gzip')
        ]
    }

    try:
        pdfkit.from_string(html_template, output_path, options=options)
        
        # 从环境变量获取文件服务器的主机地址，不同 docker-compose 或不同环境可配置
        # 默认为 host.docker.internal 方便其他容器访问宿主机映射的端口，也可自行在部署时指定
        base_url = os.environ.get("DOWNLOAD_BASE_URL", "http://host.docker.internal:9080").rstrip('/')
        download_url = f"{base_url}/{safe_filename}"
        
        return f"转换成功！PDF 已准备就绪。\n\n**📥 [点击这里下载/查看生成的 PDF]({download_url})**"
    except Exception as e:
        return f"转换失败：{str(e)}"
