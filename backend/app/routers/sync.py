"""동기화 API 라우터."""

import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from backend.app.dependencies import get_current_user
from backend.app.sync_state import get_user_lock, get_user_sync_status, update_user_sync_status

router = APIRouter(tags=["sync"])
logger = logging.getLogger(__name__)


class DateSyncRequest(BaseModel):
    date: str  # YYYY-MM-DD


@router.get("/sync/status")
def get_sync_status(user: dict = Depends(get_current_user)):
    """현재 사용자의 동기화 진행 상태를 반환한다."""
    return get_user_sync_status(user["id"])


@router.post("/sync")
def trigger_sync(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Gmail 동기화 및 AI 처리를 백그라운드로 실행한다."""
    user_id = user["id"]
    lock = get_user_lock(user_id)

    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="동기화가 이미 진행 중입니다.")

    update_user_sync_status(
        user_id,
        is_syncing=True,
        phase="gmail_sync",
        message="Gmail에서 새로운 뉴스레터를 가져오는 중...",
    )
    background_tasks.add_task(_full_sync_pipeline, user_id)
    return {"status": "sync_started", "message": "동기화가 백그라운드에서 시작되었습니다."}


@router.post("/sync/date")
def trigger_date_sync(
    body: DateSyncRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """특정 날짜의 뉴스레터를 동기화한다 (캘린더 클릭용)."""
    user_id = user["id"]
    lock = get_user_lock(user_id)

    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="동기화가 이미 진행 중입니다.")

    try:
        target_date = date.fromisoformat(body.date)
    except ValueError:
        lock.release()
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")

    update_user_sync_status(
        user_id,
        is_syncing=True,
        phase="gmail_sync",
        message=f"{body.date} 뉴스레터를 가져오는 중...",
    )
    background_tasks.add_task(_date_sync_pipeline, user_id, target_date)
    return {"status": "sync_started", "message": f"{body.date} 동기화가 시작되었습니다."}


def _full_sync_pipeline(user_id: str) -> None:
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails

    lock = get_user_lock(user_id)
    try:
        logger.info("전체 동기화 파이프라인 시작 (user=%s)", user_id)

        update_user_sync_status(
            user_id, phase="gmail_sync", message="Gmail에서 새로운 뉴스레터를 가져오는 중..."
        )
        sync_result = sync_emails(user_id, days=7)
        logger.info("Gmail 동기화 완료: %s", sync_result)

        update_user_sync_status(
            user_id, phase="ai_processing", message="AI가 뉴스레터를 분석하고 있습니다..."
        )
        ai_result = run_ai_processing(user_id)
        logger.info("AI 처리 완료: %s", ai_result)

        update_user_sync_status(
            user_id, phase="done", message="동기화가 완료되었습니다!"
        )
    except Exception:
        logger.exception("동기화 파이프라인 실패 (user=%s)", user_id)
        update_user_sync_status(
            user_id, phase="error", message="동기화 중 오류가 발생했습니다."
        )
    finally:
        update_user_sync_status(user_id, is_syncing=False)
        lock.release()


def _date_sync_pipeline(user_id: str, target_date: date) -> None:
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails_for_date

    lock = get_user_lock(user_id)
    try:
        logger.info("날짜 동기화 파이프라인 시작 (user=%s, date=%s)", user_id, target_date)

        update_user_sync_status(
            user_id, phase="gmail_sync", message=f"{target_date} 뉴스레터를 가져오는 중..."
        )
        sync_result = sync_emails_for_date(user_id, target_date)
        logger.info("날짜 동기화 완료: %s", sync_result)

        update_user_sync_status(
            user_id, phase="ai_processing", message="AI가 뉴스레터를 분석하고 있습니다..."
        )
        ai_result = run_ai_processing(user_id)
        logger.info("AI 처리 완료: %s", ai_result)

        update_user_sync_status(
            user_id, phase="done", message="동기화가 완료되었습니다!"
        )
    except Exception:
        logger.exception("날짜 동기화 실패 (user=%s, date=%s)", user_id, target_date)
        update_user_sync_status(
            user_id, phase="error", message="동기화 중 오류가 발생했습니다."
        )
    finally:
        update_user_sync_status(user_id, is_syncing=False)
        lock.release()
