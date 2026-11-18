# 知卷 · 单容器镜像（FastAPI 同时提供 API 与前端静态文件）
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY web ./web

# 数据库落盘目录（挂载卷即可持久化）
ENV ZUJUAN_DATA_DIR=/data
RUN mkdir -p /data

EXPOSE 8000
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
