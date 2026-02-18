# 완료 리포트: Backend 구현

**작업일:** 2026-02-18
**PRD 버전:** v1.3 (옵션 A — 완전 무료)

---

## 구현 완료 항목

### Phase 0 — 프로젝트 스캐폴딩
- `pyproject.toml` 의존성 10개 추가 (google-genai, fastapi, chromadb 등)
- `uv sync`로 103개 패키지 설치 완료
- `.gitignore` 업데이트 (.env, *.db, credentials.json, token.json, chroma_db/)
- `backend/` 디렉토리 트리 + `__init__.py` 생성
- `backend/.env.example` 환경 변수 템플릿 생성
- `backend/app/config.py` — pydantic-settings 기반 설정 (`.env` 자동 로드)

### Phase 1 — Gmail 연동 & 파서
- `backend/app/services/db.py` — SQLite DB (WAL 모드, FK 활성, init_db())
  - 테이블: `newsletters`, `articles`, `api_call_log`
  - CRUD: insert_newsletter, get_articles, get_article_by_id, get_newsletters 등
- `backend/app/models/article.py` — ArticleBase, ArticleListResponse
- `backend/app/models/newsletter.py` — NewsletterItem, NewsletterListResponse
- `backend/app/models/chat.py` — ChatRequest, ChatResponse
- `backend/app/services/parser.py` — BeautifulSoup HTML 파싱 + plain text fallback
- `backend/app/services/gmail.py` — InstalledAppFlow OAuth, 메일 수집, 동기화 파이프라인

### Phase 2 — Gemini AI 처리
- `backend/app/services/gemini.py`
  - 5개 배치 처리 (1 API 호출)
  - 지수 백오프 (429 에러 시 1s→2s→4s)
  - 일일 API 호출 카운터 (한도 90% 경고, 100% 중단)
  - RAG 파이프라인 (`rag_query()`)
- `backend/app/services/vector.py`
  - ChromaDB PersistentClient, text-embedding-004 임베딩
  - cosine 유사도 기반 시맨틱 검색

### Phase 3 — REST API 서버
- `backend/app/main.py` — FastAPI 앱, CORS, lifespan, APScheduler
- `backend/app/routers/articles.py` — GET /api/articles, /api/articles/{id}
- `backend/app/routers/newsletters.py` — GET /api/newsletters
- `backend/app/routers/search.py` — GET /api/search
- `backend/app/routers/chat.py` — POST /api/chat (RAG 연동)
- `backend/app/routers/sync.py` — POST /api/sync (BackgroundTasks)

### Phase 4 — 통합 배포
- APScheduler 자동 동기화 (매일 설정 시간에 증분 동기화)
- 정적 파일 서빙 (프론트엔드 빌드 결과 자동 감지)
- `Dockerfile` + `docker-compose.yml`

---

## API 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/articles | 기사 목록 (?dates=, ?category=, ?page=, ?size=) |
| GET | /api/articles/{id} | 기사 상세 |
| GET | /api/newsletters | 뉴스레터 날짜 목록 (캘린더용) |
| GET | /api/search?q= | 시맨틱 검색 |
| POST | /api/chat | RAG 채팅 |
| POST | /api/sync | 수동 Gmail 동기화 트리거 |

---

## 서버 실행 방법

```bash
# 개발 서버 (프로젝트 루트에서)
uv run python main.py
# 또는
uv run uvicorn backend.app.main:app --reload --port 8000

# Docker
docker-compose up --build
```

---

## 사전 준비 사항 (사용자 필수 작업)

1. **Google Cloud Console** → APIs & Services → Credentials
   - OAuth 2.0 클라이언트 ID 생성 (Application type: Desktop app)
   - JSON 다운로드 → `credentials.json`으로 저장 (프로젝트 루트 또는 backend/ 폴더)
   - Gmail API 활성화
   - 본인 Gmail 주소를 테스트 사용자로 추가

2. **`.env` 파일 생성** (`backend/.env.example` 참고)
   ```
   GEMINI_API_KEY=실제_API_키
   GMAIL_CREDENTIALS_PATH=./credentials.json
   ```

3. **최초 실행 시 브라우저 OAuth 동의 화면** 표시됨 → 승인 후 `token.json` 자동 저장

---

## 파일 구조

```
NewletterManager/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models/ (article.py, newsletter.py, chat.py)
│   │   ├── routers/ (articles.py, newsletters.py, search.py, chat.py, sync.py)
│   │   └── services/ (db.py, gmail.py, gemini.py, parser.py, vector.py)
│   ├── static/        (프론트엔드 빌드 결과 배치 위치)
│   └── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── main.py            (서버 런처)
```
