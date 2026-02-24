"""FastAPI 백엔드 진입점.

CORS 설정, DB 초기화, 라우터 등록, 정적 파일 서빙을 담당한다.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.routers import articles, auth, categories, chat, newsletters, search, senders, sync
from backend.app.services.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("서버 시작 완료")
    yield
    logger.info("서버 종료")


app = FastAPI(
    title="My News Archive API",
    description="뉴스레터 수집·분류·검색·RAG 채팅 API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터
app.include_router(auth.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(newsletters.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(senders.router, prefix="/api")

# 정적 파일 서빙 (프론트엔드 빌드 결과)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir() and any(_static_dir.iterdir()):
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
    logger.info("정적 파일 서빙 활성화: %s", _static_dir)
