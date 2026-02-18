# =============================================================================
# Stage 1: Frontend 빌드 (Node.js)
# =============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci --quiet

COPY frontend/ ./
RUN npm run build

# =============================================================================
# Stage 2: Backend 서버 (Python)
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# 의존성 설치
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system .

# 소스 복사
COPY backend/ ./backend/
COPY main.py .

# Frontend 빌드 산출물을 static/ 으로 복사
COPY --from=frontend-builder /frontend/dist ./backend/static/

# 데이터 디렉토리 생성
RUN mkdir -p /app/data /app/chroma_db

ENV DATABASE_URL=sqlite:////app/data/tldr.db
ENV CHROMA_PERSIST_DIR=/app/chroma_db

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
