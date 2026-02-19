"""FastAPI 백엔드 진입점.

CORS 설정, DB 초기화, APScheduler 자동 동기화, 라우터 등록, 정적 파일 서빙을 담당한다.
"""

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.routers import articles, categories, chat, newsletters, search, senders, sync
from backend.app.services.db import get_newsletters, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def _scheduled_sync() -> None:
    """APScheduler가 호출하는 증분 동기화 작업 (최근 2일)."""
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails

    logger.info("자동 동기화 시작 (스케줄)")
    try:
        sync_emails(days=2)
        run_ai_processing()
    except Exception:
        logger.exception("자동 동기화 실패")


def _initial_sync() -> None:
    """최초 실행 시 최근 30일치 뉴스레터를 가져오는 초기 동기화."""
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails

    logger.info("최초 동기화 시작 (최근 7일)")
    try:
        sync_emails(days=7)
        run_ai_processing()
        logger.info("최초 동기화 완료")
    except Exception:
        logger.exception("최초 동기화 실패")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    init_db()

    # DB가 비어있으면 최초 동기화 백그라운드 실행
    if not get_newsletters():
        logger.info("DB 비어있음 — 최초 동기화 스레드 시작")
        threading.Thread(target=_initial_sync, daemon=True).start()

    _scheduler.add_job(
        _scheduled_sync,
        trigger="cron",
        hour=settings.sync_schedule_hour,
        id="daily_sync",
        replace_existing=True,
        misfire_grace_time=None,  # 앱 재시작 시 누락된 작업을 즉시 실행
        coalesce=True,            # 다수 누락 시 한 번만 실행
    )
    _scheduler.start()
    logger.info(
        "APScheduler 시작 — 매일 %02d:00 자동 동기화", settings.sync_schedule_hour
    )

    yield

    # 종료 시
    _scheduler.shutdown(wait=False)
    logger.info("APScheduler 종료")


app = FastAPI(
    title="TLDR AI Newsletter Manager",
    description="TLDR AI 뉴스레터 수집·분류·검색·RAG 채팅 API",
    version="0.1.0",
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
app.include_router(articles.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(newsletters.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(senders.router, prefix="/api")

# 정적 파일 서빙 (프론트엔드 빌드 결과 — Phase 4에서 활성화)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir() and any(_static_dir.iterdir()):
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
    logger.info("정적 파일 서빙 활성화: %s", _static_dir)
