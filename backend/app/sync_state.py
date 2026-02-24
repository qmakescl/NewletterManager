"""per-user 동기화 상태 관리 모듈.

사용자별 sync lock과 동기화 진행 상태를 관리한다.
"""

import threading
from typing import Any

_user_locks: dict[str, threading.Lock] = {}
_user_sync_status: dict[str, dict[str, Any]] = {}
_global_lock = threading.Lock()


def _default_status() -> dict[str, Any]:
    return {
        "is_syncing": False,
        "phase": "idle",  # idle | gmail_sync | ai_processing | done | error
        "message": "",
    }


def get_user_lock(user_id: str) -> threading.Lock:
    """사용자별 동기화 lock을 반환한다 (없으면 생성)."""
    with _global_lock:
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        return _user_locks[user_id]


def get_user_sync_status(user_id: str) -> dict[str, Any]:
    """사용자별 동기화 상태를 반환한다."""
    with _global_lock:
        if user_id not in _user_sync_status:
            _user_sync_status[user_id] = _default_status()
        return _user_sync_status[user_id].copy()


def update_user_sync_status(user_id: str, **kwargs: Any) -> None:
    """사용자별 동기화 상태를 업데이트한다."""
    with _global_lock:
        if user_id not in _user_sync_status:
            _user_sync_status[user_id] = _default_status()
        _user_sync_status[user_id].update(kwargs)
