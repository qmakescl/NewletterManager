import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.app.sync_state import sync_lock

router = APIRouter(tags=["sync"])
logger = logging.getLogger(__name__)


@router.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks):
    """Gmail 동기화 및 AI 처리를 백그라운드로 실행한다."""
    if not sync_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="동기화가 이미 진행 중입니다.")
    background_tasks.add_task(_full_sync_pipeline)
    return {"status": "sync_started", "message": "동기화가 백그라운드에서 시작되었습니다."}


def _full_sync_pipeline() -> None:
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails

    try:
        logger.info("전체 동기화 파이프라인 시작")
        sync_result = sync_emails(days=7)
        logger.info("Gmail 동기화 완료: %s", sync_result)

        ai_result = run_ai_processing()
        logger.info("AI 처리 완료: %s", ai_result)
    except Exception:
        logger.exception("동기화 파이프라인 실패")
    finally:
        sync_lock.release()
