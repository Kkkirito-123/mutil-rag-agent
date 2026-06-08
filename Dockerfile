# ============================================================
# Multi-Agent AIOps Platform - 应用镜像 (API + Worker 共用)
# ============================================================
# 同一镜像跑两种角色, 由 compose 的 command 区分:
#   - API:    uvicorn app.main:app --workers N
#   - Worker: python -m app.diagnosis_worker --name worker-X
#
# 构建:  docker compose --profile app build
# 说明:  默认 rag_rerank_provider=dashscope (走 API), 不需要本地 torch;
#        若启用本地 reranker (FlagEmbedding), 镜像会显著变大, 自行按需取舍。
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# curl 用于健康检查; build-essential 给少数需要编译的轮子兜底
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 9900

# 默认以 API 角色启动; Worker 角色在 compose 里覆盖 command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9900", "--workers", "4"]
