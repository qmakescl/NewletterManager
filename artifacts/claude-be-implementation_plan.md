# Backend 구현 계획서

> **프로젝트:** TLDR AI Newsletter Manager
> **작성일:** 2026-02-18
> **PRD 버전:** v1.3 (옵션 A — 완전 무료)

---

## 프로젝트 구조

PRD에 따라 `backend/` 서브디렉토리에 코드 배치. 루트의 `pyproject.toml`에서 의존성 관리 (uv 사용).

```
NewletterManager/                    (프로젝트 루트)
├── pyproject.toml                   (수정: 의존성 추가)
├── .gitignore                       (수정: .env, *.db 등 추가)
├── main.py                          (수정: 서버 실행 런처로 변경)
├── backend/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                ← pydantic-settings 기반 설정
│   │   ├── main.py                  ← FastAPI 진입점
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── articles.py          ← GET /api/articles, /api/articles/{id}
│   │   │   ├── newsletters.py       ← GET /api/newsletters
│   │   │   ├── search.py            ← GET /api/search
│   │   │   ├── chat.py              ← POST /api/chat
│   │   │   └── sync.py              ← POST /api/sync
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── article.py           ← Pydantic 스키마
│   │   │   ├── newsletter.py
│   │   │   └── chat.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── db.py                ← SQLite DB (스키마 + CRUD)
│   │       ├── gmail.py             ← Gmail OAuth + 메일 수집
│   │       ├── gemini.py            ← Gemini AI 배치 처리 + RAG
│   │       ├── parser.py            ← TLDR HTML 파싱
│   │       └── vector.py            ← ChromaDB 벡터 검색
│   ├── static/                      (Phase 4: 프론트엔드 빌드 결과)
│   └── .env.example
├── Dockerfile                       (선택: 서버 배포용)
├── docker-compose.yml               (선택: 서버 배포용)
└── report/
    └── claude_report_backend.md     (.CLAUDE.md 규칙)
```

---

## 구현 순서 (Phase 0 → 4)

### Phase 0 — 프로젝트 스캐폴딩

| # | 작업 | 파일 |
|---|------|------|
| 0.1 | `pyproject.toml` 의존성 추가 | `pyproject.toml` |
| 0.2 | `uv sync` 실행 | — |
| 0.3 | `.gitignore` 업데이트 (.env, *.db, credentials.json, token.json, chroma_db/) | `.gitignore` |
| 0.4 | 디렉토리 구조 + `__init__.py` 생성 | `backend/` 트리 전체 |
| 0.5 | `.env.example` 생성 | `backend/.env.example` |
| 0.6 | `config.py` — pydantic-settings 기반 환경변수 관리 | `backend/app/config.py` |

**의존성 목록:**
```
google-api-python-client>=2.0, google-auth-oauthlib>=1.0, google-genai>=1.0,
fastapi>=0.100, uvicorn[standard]>=0.20, chromadb>=0.4, apscheduler>=3.10,
beautifulsoup4>=4.12, pydantic>=2.0, pydantic-settings>=2.0, python-dotenv>=1.0
```

---

### Phase 1 — Gmail 연동 & 파서

| # | 작업 | 파일 | 핵심 포인트 |
|---|------|------|-------------|
| 1.1 | SQLite DB 서비스 | `services/db.py` | `newsletters` + `articles` + `api_call_log` 테이블, PRAGMA WAL/FK, `init_db()` |
| 1.2 | Pydantic 모델 | `models/article.py`, `models/newsletter.py` | ArticleBase, ArticleListResponse, NewsletterItem |
| 1.3 | TLDR 파서 | `services/parser.py` | BeautifulSoup HTML 파싱, plain text fallback |
| 1.4 | Gmail 서비스 | `services/gmail.py` | InstalledAppFlow OAuth, `from:@tldr.tech` 필터, Message-ID 중복체크 |

**DB 스키마:**
- `newsletters`: id(UUID), email_id(UNIQUE), published_date, article_count, created_at
- `articles`: id(UUID), newsletter_id(FK), title, summary_en, summary_ko, url, category, tags(JSON text), importance, published_at, email_id, ai_processed(0/1), created_at
- `api_call_log`: id, call_date(UNIQUE), call_count

**Gmail OAuth 흐름:**
- `InstalledAppFlow.run_local_server(port=0)` → 브라우저 인증 → `token.json` 자동 저장/갱신
- 사전 준비: Google Cloud Console에서 OAuth 2.0 Desktop 클라이언트 생성, Gmail API 활성화

**파일 의존 관계:**
```
config.py → db.py → models/ → parser.py → gmail.py
```

---

### Phase 2 — Gemini AI 처리

| # | 작업 | 파일 | 핵심 포인트 |
|---|------|------|-------------|
| 2.1 | Gemini 서비스 | `services/gemini.py` | `google-genai` SDK, 5개 배치 프롬프트, JSON 응답 파싱, 지수 백오프 |
| 2.2 | 벡터 서비스 | `services/vector.py` | ChromaDB PersistentClient, `text-embedding-004` 임베딩, cosine 유사도 |
| 2.3 | AI 파이프라인 통합 | `services/gemini.py` | `run_ai_processing()`: DB 미처리 기사 → 배치 분류/요약 → 벡터 저장 |

**AI 처리 항목:** 카테고리(8종), 한국어 요약(2-3문장), 중요도(1-5), 태그(최대 5개)

**무료 한도 보호 전략:**
- DB에서 `ai_processed=0`인 기사만 처리 (핵심 절약)
- 5개 기사 → 1 API 호출 (배치)
- 429 에러 시 1s→2s→4s 지수 백오프
- `api_call_log` 테이블로 일일 카운터, 90% 도달 시 경고, 100% 도달 시 중단

---

### Phase 3 — REST API 서버

| # | 작업 | 파일 | 핵심 포인트 |
|---|------|------|-------------|
| 3.1 | FastAPI 앱 | `app/main.py` | CORS 설정, lifespan으로 DB init + APScheduler 시작 |
| 3.2 | Articles 라우터 | `routers/articles.py` | `?dates=` 복수 날짜 IN 쿼리, `?category=` 필터, 페이지네이션 |
| 3.3 | Newsletters 라우터 | `routers/newsletters.py` | published_date DESC, article_count, selectable 플래그 |
| 3.4 | Sync 라우터 | `routers/sync.py` | FastAPI BackgroundTasks로 비동기 실행 (즉시 응답) |
| 3.5 | Search 라우터 | `routers/search.py` | ChromaDB 시맨틱 검색 → article_id 목록 → DB 조회 |
| 3.6 | Chat 라우터 | `routers/chat.py` | RAG 파이프라인 연동 |
| 3.7 | Chat 모델 | `models/chat.py` | ChatRequest(message), ChatResponse(answer, sources) |

**실행 명령:**
```bash
uv run python main.py
# 또는
uv run uvicorn backend.app.main:app --reload --port 8000
```

---

### Phase 4 — RAG 엔진 & 통합

| # | 작업 | 파일 | 핵심 포인트 |
|---|------|------|-------------|
| 4.1 | RAG 파이프라인 | `services/gemini.py` | 질의→임베딩→ChromaDB top-10→context→Gemini 답변+출처 ID |
| 4.2 | 자동 동기화 | `app/main.py` | APScheduler cron (매일 `SYNC_SCHEDULE_HOUR`시, 증분 2일) |
| 4.3 | 정적 파일 서빙 | `app/main.py` | `backend/static/` 비어있지 않으면 StaticFiles 자동 마운트 |
| 4.4 | 완료 리포트 | `report/claude_report_backend.md` | .CLAUDE.md 규칙 준수 |

---

## 수정/생성 파일 요약

- **수정 (3개):** `pyproject.toml`, `.gitignore`, `main.py`
- **생성 (22개):** `backend/` 하위 전체 트리 + `.env.example` + 완료 리포트

---

## 검증 방법

| Phase | 검증 명령 | 기대 결과 |
|-------|-----------|-----------|
| Phase 0 | `uv run python -c "import fastapi"` | 오류 없음 |
| Phase 1 | Gmail 동기화 수동 실행 | SQLite에 newsletters/articles 데이터 저장 |
| Phase 2 | AI 처리 실행 | articles.summary_ko, category, importance 채워짐 |
| Phase 3 | `curl http://localhost:8000/api/articles` | JSON 응답 반환 |
| Phase 4 | `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"최근 LLM 뉴스"}'` | answer + sources 배열 반환 |

---

## 주요 설계 결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| DB | SQLite (python 내장) | 단일 사용자 로컬 앱, ORM 불필요 |
| 동기 vs 비동기 SQLite | 동기 (sqlite3) | 로컬 단일 사용자, 불필요한 복잡도 제거 |
| ChromaDB 모드 | Embedded (PersistentClient) | 별도 서버 불필요, 로컬 파일로 영속화 |
| 인증 토큰 저장 | `token.json` 로컬 파일 | InstalledAppFlow 표준 방식 |
| API 응답 형식 | Pydantic v2 모델 | FastAPI 네이티브, 자동 validation + docs |
| 스케줄러 | APScheduler (in-process) | 별도 서버 불필요, 단일 프로세스로 충분 |
| Docker | 선택 사항 | 로컬 개발에는 불필요, 서버 배포 시 참고용 |
