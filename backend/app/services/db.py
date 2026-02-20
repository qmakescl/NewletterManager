import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

from backend.app.config import settings

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = str(_BACKEND_DIR / settings.database_url.replace("sqlite:///", ""))


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 테이블 초기화
# ---------------------------------------------------------------------------

def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS newsletters (
                id TEXT PRIMARY KEY,
                email_id TEXT UNIQUE NOT NULL,
                gmail_id TEXT UNIQUE,
                published_date DATE NOT NULL,
                article_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_newsletters_published_date
                ON newsletters(published_date DESC);

            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                newsletter_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary_en TEXT,
                summary_ko TEXT,
                url TEXT,
                category TEXT DEFAULT 'Other',
                tags TEXT DEFAULT '[]',
                importance INTEGER DEFAULT 0,
                published_at DATETIME,
                email_id TEXT,
                ai_processed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
            );

            CREATE INDEX IF NOT EXISTS idx_articles_published_at
                ON articles(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_category
                ON articles(category);
            CREATE INDEX IF NOT EXISTS idx_articles_newsletter_id
                ON articles(newsletter_id);
            CREATE INDEX IF NOT EXISTS idx_articles_email_id
                ON articles(email_id);

            CREATE TABLE IF NOT EXISTS api_call_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_date DATE NOT NULL,
                call_count INTEGER DEFAULT 0,
                UNIQUE(call_date)
            );

            CREATE TABLE IF NOT EXISTS senders (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 기존 newsletters 테이블에 gmail_id 컬럼이 없으면 추가 (마이그레이션)
    _migrate_add_gmail_id()

    # 기존 .env 발신자를 시드 데이터로 마이그레이션
    _seed_senders()

    logger.info("Database initialized: %s", DB_PATH)


def _migrate_add_gmail_id() -> None:
    """기존 DB에 gmail_id 컬럼이 없으면 추가한다."""
    with get_db() as conn:
        columns = [
            row["name"]
            for row in conn.execute("PRAGMA table_info(newsletters)").fetchall()
        ]
        if "gmail_id" not in columns:
            conn.execute("ALTER TABLE newsletters ADD COLUMN gmail_id TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_newsletters_gmail_id "
                "ON newsletters(gmail_id)"
            )
            logger.info("Migration: newsletters 테이블에 gmail_id 컬럼 추가 완료")


def _seed_senders() -> None:
    """senders 테이블이 비어있으면 .env의 newsletter_senders를 초기 데이터로 삽입."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as cnt FROM senders").fetchone()["cnt"]
        if count > 0:
            return

        for email in settings.newsletter_senders:
            conn.execute(
                "INSERT OR IGNORE INTO senders (id, name, email) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), email.split("@")[0], email),
            )
        logger.info("Seeded %d sender(s) from .env", len(settings.newsletter_senders))


# ---------------------------------------------------------------------------
# Newsletter CRUD
# ---------------------------------------------------------------------------

def newsletter_exists(email_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM newsletters WHERE email_id = ?", (email_id,)
        ).fetchone()
        return row is not None


def newsletter_exists_by_gmail_id(gmail_id: str) -> bool:
    """Gmail 내부 ID로 뉴스레터 존재 여부를 확인한다 (조기 필터링용)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM newsletters WHERE gmail_id = ?", (gmail_id,)
        ).fetchone()
        return row is not None


def insert_newsletter(
    email_id: str,
    published_date: str,
    articles: list[dict[str, Any]],
    gmail_id: str | None = None,
) -> str:
    newsletter_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """INSERT INTO newsletters (id, email_id, gmail_id, published_date, article_count)
               VALUES (?, ?, ?, ?, ?)""",
            (newsletter_id, email_id, gmail_id, published_date, len(articles)),
        )

        for art in articles:
            article_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO articles
                   (id, newsletter_id, title, summary_en, url, published_at, email_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    article_id,
                    newsletter_id,
                    art["title"],
                    art.get("summary_en", ""),
                    art.get("url", ""),
                    published_date,
                    email_id,
                ),
            )

    logger.info(
        "Inserted newsletter %s (%s) with %d articles",
        newsletter_id, published_date, len(articles),
    )
    return newsletter_id


def get_newsletters() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT published_date, article_count
               FROM newsletters
               ORDER BY published_date DESC"""
        ).fetchall()

    return [
        {
            "date": row["published_date"],
            "article_count": row["article_count"],
            "selectable": True,
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Article CRUD
# ---------------------------------------------------------------------------

def _row_to_article(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["tags"] = json.loads(d.get("tags") or "[]")
    return d


def get_articles(
    dates: list[str] | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 24,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: list[Any] = []

    if dates:
        placeholders = ",".join("?" for _ in dates)
        conditions.append(f"DATE(published_at) IN ({placeholders})")
        params.extend(dates)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM articles {where}", params
        ).fetchone()
        total = total_row["cnt"]

        offset = (page - 1) * size
        rows = conn.execute(
            f"""SELECT * FROM articles {where}
                ORDER BY published_at DESC
                LIMIT ? OFFSET ?""",
            [*params, size, offset],
        ).fetchall()

    return {
        "total": total,
        "items": [_row_to_article(r) for r in rows],
    }


def get_article_by_id(article_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
    return _row_to_article(row) if row else None


# ---------------------------------------------------------------------------
# AI 처리 관련
# ---------------------------------------------------------------------------

def get_unprocessed_articles(batch_size: int = 5) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM articles
               WHERE ai_processed = 0
               ORDER BY created_at ASC
               LIMIT ?""",
            (batch_size,),
        ).fetchall()
    return [_row_to_article(r) for r in rows]


def update_article_ai_data(
    article_id: str,
    summary_ko: str,
    category: str,
    importance: int,
    tags: list[str],
) -> None:
    with get_db() as conn:
        conn.execute(
            """UPDATE articles
               SET summary_ko = ?, category = ?, importance = ?,
                   tags = ?, ai_processed = 1
               WHERE id = ?""",
            (summary_ko, category, importance, json.dumps(tags, ensure_ascii=False), article_id),
        )


# ---------------------------------------------------------------------------
# Category 집계
# ---------------------------------------------------------------------------


def get_categories() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT category as name, COUNT(*) as count
               FROM articles
               WHERE category IS NOT NULL AND category != ''
               GROUP BY category
               ORDER BY count DESC"""
        ).fetchall()
    return [{"name": row["name"], "count": row["count"]} for row in rows]


# ---------------------------------------------------------------------------
# API 호출 카운터
# ---------------------------------------------------------------------------

def get_daily_api_count(today: date | None = None) -> int:
    today = today or date.today()
    with get_db() as conn:
        row = conn.execute(
            "SELECT call_count FROM api_call_log WHERE call_date = ?",
            (today.isoformat(),),
        ).fetchone()
    return row["call_count"] if row else 0


def increment_api_count(today: date | None = None) -> None:
    today = today or date.today()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO api_call_log (call_date, call_count) VALUES (?, 1)
               ON CONFLICT(call_date) DO UPDATE SET call_count = call_count + 1""",
            (today.isoformat(),),
        )


# ---------------------------------------------------------------------------
# Sender CRUD
# ---------------------------------------------------------------------------

def get_senders() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM senders ORDER BY created_at ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_active_sender_emails() -> list[str]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT email FROM senders WHERE is_active = 1"
        ).fetchall()
    return [row["email"] for row in rows]


def add_sender(name: str, email: str) -> dict[str, Any]:
    sender_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO senders (id, name, email) VALUES (?, ?, ?)",
            (sender_id, name, email),
        )
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ?", (sender_id,)
        ).fetchone()
    return dict(row)


def update_sender(
    sender_id: str,
    name: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    fields: list[str] = []
    params: list[Any] = []

    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if email is not None:
        fields.append("email = ?")
        params.append(email)
    if is_active is not None:
        fields.append("is_active = ?")
        params.append(int(is_active))

    if not fields:
        return get_sender_by_id(sender_id)

    params.append(sender_id)
    with get_db() as conn:
        conn.execute(
            f"UPDATE senders SET {', '.join(fields)} WHERE id = ?", params
        )
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ?", (sender_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_sender(sender_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM senders WHERE id = ?", (sender_id,)
        )
    return cursor.rowcount > 0


def get_sender_by_id(sender_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ?", (sender_id,)
        ).fetchone()
    return dict(row) if row else None
