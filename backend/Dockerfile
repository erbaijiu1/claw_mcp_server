FROM docker.1ms.run/library/python:3.10-slim-bullseye

# 设置工作目录
WORKDIR /app

# 设置环境变量防止 Python 缓冲输出
ENV PYTHONUNBUFFERED=1

# 必须先执行 update 才能找到包，这里直接暴力替换为清华源避免下载慢
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并使用阿里云源安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制项目代码
COPY . /app

# 暴露 SSE 端口
EXPOSE 9000

# 运行聚合 FastMCP 服务入口
CMD ["python", "main.py"]
