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
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                picture_url TEXT,
                gmail_token_encrypted TEXT,
                gmail_token_expiry DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS newsletters (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                email_id TEXT NOT NULL,
                gmail_id TEXT,
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
                user_id TEXT,
                call_date DATE NOT NULL,
                call_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS senders (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # 기존 DB 마이그레이션
    _migrate_add_gmail_id()
    _migrate_add_user_id()

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


def _migrate_add_user_id() -> None:
    """기존 테이블에 user_id 컬럼이 없으면 추가하고, per-user 복합 UNIQUE 인덱스를 생성한다."""
    with get_db() as conn:
        # newsletters
        nl_cols = [r["name"] for r in conn.execute("PRAGMA table_info(newsletters)").fetchall()]
        if "user_id" not in nl_cols:
            conn.execute("ALTER TABLE newsletters ADD COLUMN user_id TEXT")
            conn.execute("UPDATE newsletters SET user_id = 'legacy' WHERE user_id IS NULL")
            logger.info("Migration: newsletters 테이블에 user_id 컬럼 추가 완료")

        # UNIQUE 인덱스 (기존 단일 UNIQUE → per-user 복합)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_newsletters_user_email_id "
            "ON newsletters(user_id, email_id)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_newsletters_user_gmail_id "
            "ON newsletters(user_id, gmail_id)"
        )

        # senders
        s_cols = [r["name"] for r in conn.execute("PRAGMA table_info(senders)").fetchall()]
        if "user_id" not in s_cols:
            conn.execute("ALTER TABLE senders ADD COLUMN user_id TEXT")
            conn.execute("UPDATE senders SET user_id = 'legacy' WHERE user_id IS NULL")
            logger.info("Migration: senders 테이블에 user_id 컬럼 추가 완료")

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_senders_user_email "
            "ON senders(user_id, email)"
        )

        # api_call_log
        a_cols = [r["name"] for r in conn.execute("PRAGMA table_info(api_call_log)").fetchall()]
        if "user_id" not in a_cols:
            conn.execute("ALTER TABLE api_call_log ADD COLUMN user_id TEXT")
            conn.execute("UPDATE api_call_log SET user_id = 'legacy' WHERE user_id IS NULL")
            logger.info("Migration: api_call_log 테이블에 user_id 컬럼 추가 완료")

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_call_log_user_date "
            "ON api_call_log(user_id, call_date)"
        )


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def get_user_by_google_id(google_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_user(
    google_id: str,
    email: str,
    name: str,
    picture_url: str | None = None,
    gmail_token_encrypted: str | None = None,
    gmail_token_expiry: str | None = None,
) -> dict[str, Any]:
    """사용자를 생성하거나 업데이트한다. 생성 시 UUID를 할당한다."""
    existing = get_user_by_google_id(google_id)

    with get_db() as conn:
        if existing:
            conn.execute(
                """UPDATE users
                   SET email = ?, name = ?, picture_url = ?,
                       gmail_token_encrypted = COALESCE(?, gmail_token_encrypted),
                       gmail_token_expiry = COALESCE(?, gmail_token_expiry),
                       last_login_at = CURRENT_TIMESTAMP
                   WHERE google_id = ?""",
                (email, name, picture_url, gmail_token_encrypted, gmail_token_expiry, google_id),
            )
            user_id = existing["id"]
        else:
            user_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO users (id, google_id, email, name, picture_url,
                                      gmail_token_encrypted, gmail_token_expiry)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, google_id, email, name, picture_url,
                 gmail_token_encrypted, gmail_token_expiry),
            )

        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def update_user_gmail_token(
    user_id: str,
    gmail_token_encrypted: str,
    gmail_token_expiry: str | None = None,
) -> None:
    """사용자의 Gmail 토큰을 업데이트한다."""
    with get_db() as conn:
        conn.execute(
            """UPDATE users
               SET gmail_token_encrypted = ?, gmail_token_expiry = ?
               WHERE id = ?""",
            (gmail_token_encrypted, gmail_token_expiry, user_id),
        )


# ---------------------------------------------------------------------------
# Newsletter CRUD
# ---------------------------------------------------------------------------

def newsletter_exists(user_id: str, email_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM newsletters WHERE user_id = ? AND email_id = ?",
            (user_id, email_id),
        ).fetchone()
        return row is not None


def newsletter_exists_by_gmail_id(user_id: str, gmail_id: str) -> bool:
    """Gmail 내부 ID로 뉴스레터 존재 여부를 확인한다 (조기 필터링용)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM newsletters WHERE user_id = ? AND gmail_id = ?",
            (user_id, gmail_id),
        ).fetchone()
        return row is not None


def insert_newsletter(
    user_id: str,
    email_id: str,
    published_date: str,
    articles: list[dict[str, Any]],
    gmail_id: str | None = None,
) -> str:
    newsletter_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """INSERT INTO newsletters (id, user_id, email_id, gmail_id, published_date, article_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (newsletter_id, user_id, email_id, gmail_id, published_date, len(articles)),
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


def get_newsletters(user_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT published_date, article_count
               FROM newsletters
               WHERE user_id = ?
               ORDER BY published_date DESC""",
            (user_id,),
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
    user_id: str,
    dates: list[str] | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 24,
) -> dict[str, Any]:
    conditions: list[str] = ["a.newsletter_id IN (SELECT id FROM newsletters WHERE user_id = ?)"]
    params: list[Any] = [user_id]

    if dates:
        placeholders = ",".join("?" for _ in dates)
        conditions.append(f"DATE(a.published_at) IN ({placeholders})")
        params.extend(dates)
    if category:
        conditions.append("a.category = ?")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions)

    with get_db() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM articles a {where}", params
        ).fetchone()
        total = total_row["cnt"]

        offset = (page - 1) * size
        rows = conn.execute(
            f"""SELECT a.* FROM articles a {where}
                ORDER BY a.published_at DESC
                LIMIT ? OFFSET ?""",
            [*params, size, offset],
        ).fetchall()

    return {
        "total": total,
        "items": [_row_to_article(r) for r in rows],
    }


def get_article_by_id(user_id: str, article_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """SELECT a.* FROM articles a
               JOIN newsletters n ON a.newsletter_id = n.id
               WHERE a.id = ? AND n.user_id = ?""",
            (article_id, user_id),
        ).fetchone()
    return _row_to_article(row) if row else None


# ---------------------------------------------------------------------------
# AI 처리 관련
# ---------------------------------------------------------------------------

def get_unprocessed_articles(user_id: str, batch_size: int = 5) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.* FROM articles a
               JOIN newsletters n ON a.newsletter_id = n.id
               WHERE a.ai_processed = 0 AND n.user_id = ?
               ORDER BY a.created_at ASC
               LIMIT ?""",
            (user_id, batch_size),
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


def get_categories(user_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.category as name, COUNT(*) as count
               FROM articles a
               JOIN newsletters n ON a.newsletter_id = n.id
               WHERE a.category IS NOT NULL AND a.category != '' AND n.user_id = ?
               GROUP BY a.category
               ORDER BY count DESC""",
            (user_id,),
        ).fetchall()
    return [{"name": row["name"], "count": row["count"]} for row in rows]


# ---------------------------------------------------------------------------
# API 호출 카운터
# ---------------------------------------------------------------------------

def get_daily_api_count(user_id: str, today: date | None = None) -> int:
    today = today or date.today()
    with get_db() as conn:
        row = conn.execute(
            "SELECT call_count FROM api_call_log WHERE user_id = ? AND call_date = ?",
            (user_id, today.isoformat()),
        ).fetchone()
    return row["call_count"] if row else 0


def increment_api_count(user_id: str, today: date | None = None) -> None:
    today = today or date.today()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO api_call_log (user_id, call_date, call_count) VALUES (?, ?, 1)
               ON CONFLICT(user_id, call_date) DO UPDATE SET call_count = call_count + 1""",
            (user_id, today.isoformat()),
        )


# ---------------------------------------------------------------------------
# Sender CRUD
# ---------------------------------------------------------------------------

def get_senders(user_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM senders WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_active_sender_emails(user_id: str) -> list[str]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT email FROM senders WHERE user_id = ? AND is_active = 1",
            (user_id,),
        ).fetchall()
    return [row["email"] for row in rows]


def add_sender(user_id: str, name: str, email: str) -> dict[str, Any]:
    sender_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO senders (id, user_id, name, email) VALUES (?, ?, ?, ?)",
            (sender_id, user_id, name, email),
        )
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ?", (sender_id,)
        ).fetchone()
    return dict(row)


def update_sender(
    user_id: str,
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
        return get_sender_by_id(user_id, sender_id)

    params.extend([sender_id, user_id])
    with get_db() as conn:
        conn.execute(
            f"UPDATE senders SET {', '.join(fields)} WHERE id = ? AND user_id = ?", params
        )
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ? AND user_id = ?", (sender_id, user_id)
        ).fetchone()
    return dict(row) if row else None


def delete_sender(user_id: str, sender_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM senders WHERE id = ? AND user_id = ?", (sender_id, user_id)
        )
    return cursor.rowcount > 0


def get_sender_by_id(user_id: str, sender_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM senders WHERE id = ? AND user_id = ?", (sender_id, user_id)
        ).fetchone()
    return dict(row) if row else None
