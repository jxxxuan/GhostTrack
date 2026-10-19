FROM python:3.10-slim

WORKDIR /app

# 复制依赖配置并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 暴露 Web 端口
EXPOSE 5000

# 默认启动 Web 前端服务
CMD ["python", "web_app.py"]
