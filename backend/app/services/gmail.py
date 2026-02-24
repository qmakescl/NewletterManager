"""Gmail API 연동 서비스.

per-user OAuth 토큰 기반 Gmail 연동, 뉴스레터 수집, 동기화 파이프라인을 제공한다.
"""

import json
import base64
import logging
from datetime import datetime, timedelta, date
from email.utils import parsedate_to_datetime
from typing import Any

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.app.config import settings
from backend.app.services.db import (
    get_active_sender_emails,
    get_user_by_id,
    insert_newsletter,
    newsletter_exists,
    newsletter_exists_by_gmail_id,
    update_user_gmail_token,
)
from backend.app.services.parser import parse_tldr_email

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_fernet() -> Fernet:
    return Fernet(settings.token_encryption_key.encode())


def get_gmail_service_for_user(user_id: str):
    """DB에 저장된 암호화 토큰으로 Gmail API 서비스를 반환한다.

    토큰 만료 시 자동으로 갱신하고 DB에 재저장한다.
    """
    user = get_user_by_id(user_id)
    if not user or not user.get("gmail_token_encrypted"):
        raise ValueError(f"사용자 {user_id}의 Gmail 토큰이 없습니다.")

    fernet = _get_fernet()
    decrypted = fernet.decrypt(user["gmail_token_encrypted"].encode()).decode()
    token_data = json.loads(decrypted)

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", settings.google_client_id),
        client_secret=token_data.get("client_secret", settings.google_client_secret),
        scopes=token_data.get("scopes", SCOPES),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        new_token_data = {
            **token_data,
            "access_token": creds.token,
        }
        encrypted = fernet.encrypt(json.dumps(new_token_data).encode()).decode()
        expiry = creds.expiry.isoformat() if creds.expiry else None
        update_user_gmail_token(user_id, encrypted, expiry)
        logger.info("Gmail 토큰 갱신 완료: user_id=%s", user_id)

    return build("gmail", "v1", credentials=creds)


def _list_gmail_message_refs(user_id: str, days: int = 30) -> tuple[Any, list[dict]]:
    """Gmail에서 메시지 참조(id, threadId)만 가져온다."""
    active_emails = get_active_sender_emails(user_id)
    if not active_emails:
        logger.warning("활성 발신자가 없습니다. Gmail 검색을 건너뜁니다.")
        return None, []

    service = get_gmail_service_for_user(user_id)
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    sender_parts = " OR ".join(f"from:{s}" for s in active_emails)
    query = f"({sender_parts}) after:{after_date}"

    logger.info("Gmail 검색: %s", query)

    message_refs: list[dict] = []
    page_token = None

    while True:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token)
            .execute()
        )

        if "messages" in result:
            message_refs.extend(result["messages"])

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    logger.info("총 %d개 메시지 참조 발견", len(message_refs))
    return service, message_refs


def _list_gmail_message_refs_for_date(
    user_id: str, target_date: date
) -> tuple[Any, list[dict]]:
    """특정 날짜의 Gmail 메시지 참조를 가져온다."""
    active_emails = get_active_sender_emails(user_id)
    if not active_emails:
        return None, []

    service = get_gmail_service_for_user(user_id)
    after_date = target_date.strftime("%Y/%m/%d")
    before_date = (target_date + timedelta(days=1)).strftime("%Y/%m/%d")
    sender_parts = " OR ".join(f"from:{s}" for s in active_emails)
    query = f"({sender_parts}) after:{after_date} before:{before_date}"

    logger.info("Gmail 날짜 검색: %s", query)

    message_refs: list[dict] = []
    page_token = None

    while True:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token)
            .execute()
        )
        if "messages" in result:
            message_refs.extend(result["messages"])
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return service, message_refs


def _fetch_full_message(service: Any, gmail_id: str) -> dict[str, Any]:
    """단일 메시지의 full content를 가져온다."""
    return (
        service.users()
        .messages()
        .get(userId="me", id=gmail_id, format="full")
        .execute()
    )


def get_message_id(message: dict[str, Any]) -> str:
    """Gmail 메시지에서 Message-ID 헤더를 추출한다."""
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header["name"].lower() == "message-id":
            return header["value"]
    return message["id"]


def get_message_date(message: dict[str, Any]) -> str:
    """Gmail 메시지에서 날짜를 추출하여 YYYY-MM-DD 형식으로 반환한다."""
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header["name"].lower() == "date":
            try:
                dt = parsedate_to_datetime(header["value"])
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    internal_date = message.get("internalDate")
    if internal_date:
        dt = datetime.fromtimestamp(int(internal_date) / 1000)
        return dt.strftime("%Y-%m-%d")

    return datetime.now().strftime("%Y-%m-%d")


def get_message_body(message: dict[str, Any]) -> tuple[str, str]:
    """Gmail 메시지에서 HTML과 plain text 본문을 추출한다."""
    payload = message.get("payload", {})
    _extract_parts(payload, html_body_parts := [], text_body_parts := [])

    html_body = "\n".join(html_body_parts) if html_body_parts else ""
    text_body = "\n".join(text_body_parts) if text_body_parts else ""

    return html_body, text_body


def _extract_parts(
    part: dict[str, Any],
    html_parts: list[str],
    text_parts: list[str],
) -> None:
    """MIME 파트 트리를 재귀적으로 순회하여 본문을 추출한다."""
    mime_type = part.get("mimeType", "")

    if "parts" in part:
        for sub_part in part["parts"]:
            _extract_parts(sub_part, html_parts, text_parts)
    elif mime_type == "text/html":
        data = part.get("body", {}).get("data", "")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            html_parts.append(decoded)
    elif mime_type == "text/plain":
        data = part.get("body", {}).get("data", "")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            text_parts.append(decoded)


# ---------------------------------------------------------------------------
# 동기화 파이프라인
# ---------------------------------------------------------------------------

def _process_messages(
    user_id: str, service: Any, message_refs: list[dict]
) -> dict[str, int]:
    """메시지 참조 목록을 처리하여 뉴스레터를 DB에 저장한다."""
    new_count = 0
    skipped_count = 0
    error_count = 0

    for msg_ref in message_refs:
        gmail_id = msg_ref["id"]

        if newsletter_exists_by_gmail_id(user_id, gmail_id):
            skipped_count += 1
            continue

        try:
            msg = _fetch_full_message(service, gmail_id)
            email_id = get_message_id(msg)

            if newsletter_exists(user_id, email_id):
                skipped_count += 1
                continue

            published_date = get_message_date(msg)
            html_body, text_body = get_message_body(msg)
            parsed_articles = parse_tldr_email(html_body, text_body)

            if parsed_articles:
                insert_newsletter(
                    user_id=user_id,
                    email_id=email_id,
                    published_date=published_date,
                    articles=[
                        {
                            "title": a.title,
                            "summary_en": a.summary_en,
                            "url": a.url,
                        }
                        for a in parsed_articles
                    ],
                    gmail_id=gmail_id,
                )
                new_count += 1
                logger.info(
                    "뉴스레터 저장: %s (%d개 기사)", published_date, len(parsed_articles)
                )
            else:
                logger.warning("파싱 결과 없음: gmail_id=%s", gmail_id)
                error_count += 1
        except Exception:
            logger.exception("뉴스레터 처리 실패: gmail_id=%s", gmail_id)
            error_count += 1

    return {
        "new_newsletters": new_count,
        "skipped_duplicates": skipped_count,
        "errors": error_count,
    }


def sync_emails(user_id: str, days: int = 30) -> dict[str, int]:
    """Gmail 동기화 파이프라인: 목록 조회 → 조기 중복 체크 → full 다운로드 → 파싱 → DB 저장."""
    logger.info("Gmail 동기화 시작 (user=%s, 최근 %d일)", user_id, days)

    service, message_refs = _list_gmail_message_refs(user_id, days=days)
    if not message_refs:
        return {"total_fetched": 0, "new_newsletters": 0, "skipped_duplicates": 0, "errors": 0}

    result = _process_messages(user_id, service, message_refs)
    result["total_fetched"] = len(message_refs)

    logger.info("Gmail 동기화 완료: %s", result)
    return result


def sync_emails_for_date(user_id: str, target_date: date) -> dict[str, int]:
    """특정 날짜의 뉴스레터를 동기화한다 (캘린더 클릭용)."""
    logger.info("Gmail 날짜 동기화 시작 (user=%s, date=%s)", user_id, target_date)

    service, message_refs = _list_gmail_message_refs_for_date(user_id, target_date)
    if not message_refs:
        return {"total_fetched": 0, "new_newsletters": 0, "skipped_duplicates": 0, "errors": 0}

    result = _process_messages(user_id, service, message_refs)
    result["total_fetched"] = len(message_refs)

    logger.info("Gmail 날짜 동기화 완료: %s", result)
    return result
