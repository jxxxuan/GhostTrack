FROM python:3.10-slim

WORKDIR /app

# 复制依赖配置并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# GhostTrack 是一个交互式 CLI 工具，启动直接运行脚本
ENTRYPOINT ["python", "GhostTR.py"]
