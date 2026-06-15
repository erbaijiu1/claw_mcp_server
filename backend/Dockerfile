FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量防止 Python 缓冲输出
ENV PYTHONUNBUFFERED=1

# 安装目前所需的所有系统依赖（wkhtmltopdf, 字体等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . /app

# 暴露 SSE 端口
EXPOSE 9000

# 运行聚合 FastMCP 服务入口
CMD ["python", "main.py"]
