# 구현 계획: 다중 사용자 뉴스레터 아카이브 서비스로 전환

> 작성일: 2026-02-24

## 개요

단일 사용자용 Newsletter Manager를 다중 사용자 서비스 **"My News Archive"**로 확장한다.

- **인증**: Google OAuth 로그인 (gmail.readonly scope 포함 → 로그인 + Gmail 접근 한 번에 해결)
- **데이터 격리**: 사용자별 발신자 관리, 뉴스레터 수집, AI 분석
- **동기화**: Cron 제거 → 온디맨드 (페이지 접속, 발신자 등록, 수동 버튼, 캘린더 날짜 클릭)

---

## 동기화 시점 정의

| 트리거 | 범위 | 조건 |
|--------|------|------|
| 발신자 등록 | 최근 2일 | 새 발신자 추가 시 자동 |
| 페이지 접속 | 최근 2일 | 기존 데이터 있으면 백그라운드 |
| 수동 버튼 | 최근 7일 | 사용자 클릭 |
| 캘린더 날짜 클릭 | 해당 날짜 1일 | 뉴스레터 없는 날 클릭 |

모든 경우 `newsletter_exists_by_gmail_id(user_id, gmail_id)`로 중복 건너뜀.

---

## Phase 1: DB 스키마 + 인증 기반

### 1-1. users 테이블 생성
**파일:** `backend/app/services/db.py`

```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    google_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    picture_url TEXT,
    gmail_token_encrypted TEXT,  -- Fernet 암호화된 OAuth JSON
    gmail_token_expiry DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 1-2. 기존 테이블에 user_id 추가 (마이그레이션)
**파일:** `backend/app/services/db.py` — `_migrate_add_user_id()` 함수 추가

- newsletters, articles, senders, api_call_log 모든 테이블에 `user_id TEXT` 컬럼 추가
- 기존 UNIQUE 제약을 per-user 복합 UNIQUE로 변경:
  - `newsletters(user_id, email_id)`, `newsletters(user_id, gmail_id)`
  - `senders(user_id, email)`, `api_call_log(user_id, call_date)`
- 기존 데이터는 `user_id = "legacy"` 할당

### 1-3. 새 Python 의존성
**파일:** `pyproject.toml`

```
authlib>=1.3
httpx>=0.25
python-jose[cryptography]>=3.3
cryptography>=41.0
```

제거: `apscheduler`

### 1-4. Config 확장
**파일:** `backend/app/config.py`

```python
google_client_id: str = ""
google_client_secret: str = ""
jwt_secret_key: str = ""
token_encryption_key: str = ""  # Fernet key (32-byte base64)
frontend_url: str = "http://localhost:3000"
```

### 1-5. Auth 의존성
**파일 (신규):** `backend/app/dependencies.py`

- `get_current_user(request)` → JWT 쿠키(`session`) 또는 `Authorization` 헤더에서 사용자 추출
- 미인증 시 401

### 1-6. Auth 라우터
**파일 (신규):** `backend/app/routers/auth.py`

| 엔드포인트 | 동작 |
|-----------|------|
| `GET /api/auth/login` | Google OAuth URL 반환 (scopes: openid, email, profile, gmail.readonly) |
| `GET /api/auth/callback` | 코드 교환 → 사용자 생성/업데이트 → Gmail 토큰 Fernet 암호화 저장 → JWT 쿠키 발급 |
| `GET /api/auth/me` | 현재 사용자 정보 반환 |
| `POST /api/auth/logout` | 세션 쿠키 삭제 |

---

## Phase 2: 모든 DB 함수 user_id 스코프 적용

**파일:** `backend/app/services/db.py`

모든 함수에 `user_id` 첫 번째 파라미터 추가, 모든 SQL에 `WHERE user_id = ?` 조건 추가:

- `get_newsletters(user_id)`
- `get_articles(user_id, dates, category, page, size)`
- `get_article_by_id(user_id, article_id)`
- `insert_newsletter(user_id, email_id, ...)`
- `newsletter_exists(user_id, email_id)`
- `newsletter_exists_by_gmail_id(user_id, gmail_id)`
- `get_senders(user_id)`, `get_active_sender_emails(user_id)`
- `add_sender(user_id, name, email)`, `update_sender(user_id, sender_id, ...)`
- `delete_sender(user_id, sender_id)`
- `get_unprocessed_articles(user_id, batch_size)`
- `get_daily_api_count(user_id, today)`, `increment_api_count(user_id, today)`
- `_seed_senders()` 제거 (발신자는 사용자별 등록으로 대체)

---

## Phase 3: per-user Gmail + 동기화 아키텍처

### 3-1. Gmail 서비스 리팩터링
**파일:** `backend/app/services/gmail.py`

- `get_gmail_service()` (파일 기반) → `get_gmail_service_for_user(user_id)` (DB 토큰 로드/복호화/갱신)
- `token.json` 파일 기반 완전 제거
- `sync_emails(user_id, days)` — user_id 스코프
- `sync_emails_for_date(user_id, target_date)` — 캘린더 클릭용 (신규, 하루치 동기화)

### 3-2. per-user 동기화 상태
**파일:** `backend/app/sync_state.py`

```python
_user_locks: Dict[str, threading.Lock] = {}
_user_sync_status: Dict[str, dict] = {}

def get_user_lock(user_id: str) -> threading.Lock
def get_user_sync_status(user_id: str) -> dict
def update_user_sync_status(user_id: str, **kwargs) -> None
```

### 3-3. APScheduler 제거
**파일:** `backend/app/main.py`

- `_scheduled_sync()`, `_scheduler` 전체 제거
- lifespan에서 스케줄러 등록/시작/종료 제거
- `_resume_ai_processing()` 제거 (동기화 파이프라인 내에서 자동 처리)

### 3-4. 동기화 라우터 업데이트
**파일:** `backend/app/routers/sync.py`

- 모든 엔드포인트에 `Depends(get_current_user)` 추가
- per-user lock/status 사용
- `POST /api/sync/date` — 특정 날짜 동기화 엔드포인트 (신규)

### 3-5. 발신자 등록 시 동기화 자동 트리거
**파일:** `backend/app/routers/senders.py`

- `POST /api/senders` 성공 후 → 백그라운드에서 `sync_emails(user_id, days=2)` + `run_ai_processing(user_id)` 실행

---

## Phase 4: per-user AI + Vector

### 4-1. Vector DB 격리
**파일:** `backend/app/services/vector.py`

- 컬렉션 이름: `articles_{user_id}` (사용자별 분리, 데이터 누출 없음)
- 모든 함수에 `user_id` 파라미터 추가

### 4-2. Gemini 서비스 스코프
**파일:** `backend/app/services/gemini.py`

- `run_ai_processing(user_id)` — 사용자 미처리 기사만 처리
- `rag_query(user_id, message)` — 사용자 Vector 컬렉션만 검색
- `_check_daily_limit(user_id)` — per-user API 호출 제한

---

## Phase 5: 모든 라우터 인증 가드

**대상 파일:** `backend/app/routers/` 내 articles, categories, newsletters, search, chat, sync, senders

각 파일에:
- `user = Depends(get_current_user)` 파라미터 추가
- `user["user_id"]` 를 모든 DB/서비스 호출에 전달

---

## Phase 6: 프론트엔드 인증 + 라우팅

### 6-1. 의존성 추가
```
npm install react-router-dom
```

### 6-2. AuthContext
**파일 (신규):** `frontend/src/contexts/AuthContext.jsx`

- 앱 초기화 시 `GET /api/auth/me` 로 세션 확인
- `login()` → `/api/auth/login` 에서 Google OAuth URL 받아 이동
- `logout()` → `POST /api/auth/logout` 후 `/login` 이동

### 6-3. 라우팅 구조
**파일:** `frontend/src/main.jsx` — `<BrowserRouter>` + `<AuthProvider>` 래핑
**파일:** `frontend/src/App.jsx` — Routes 셋업

```
/login         → LoginPage       (미인증)
/auth/callback → AuthCallback    (OAuth 콜백 처리)
/*             → MainLayout      (인증 필요, 미인증 시 /login 리다이렉트)
```

### 6-4. 신규 컴포넌트

| 파일 | 역할 |
|------|------|
| `frontend/src/components/LoginPage.jsx` | "My News Archive" 브랜딩 + "Sign in with Google" 버튼 |
| `frontend/src/components/AuthCallback.jsx` | OAuth 콜백 URL 파라미터 처리 후 `/` 리다이렉트 |
| `frontend/src/components/MainLayout.jsx` | 기존 App.jsx 메인 레이아웃 이동 |

### 6-5. API 클라이언트 업데이트
**파일:** `frontend/src/api/client.js`

- 모든 `fetch()` 에 `credentials: 'include'` 추가
- 401 응답 시 `window.location.href = '/login'` 처리
- 신규 함수: `fetchCurrentUser()`, `triggerDateSync(date)`

### 6-6. 브랜딩 변경 ("My Newsletter Manager" → "My News Archive")

| 파일 | 변경 위치 |
|------|----------|
| `frontend/index.html` | `<title>` 태그 |
| `frontend/src/components/MainLayout.jsx` | header `<h1>` |
| `frontend/src/components/InitialSyncScreen.jsx` | logo `<h1>` |

---

## Phase 7: 캘린더 기능 + 온보딩 강화

### 7-1. 캘린더 음영 처리
**파일:** `frontend/src/components/NewsletterCalendar.jsx`

- 지난 평일(월~금) 중 뉴스레터 없는 날 → `.missing-newsletter` CSS 클래스 (회색 음영)
- 해당 날 클릭 시 `POST /api/sync/date` 호출 → 해당 날짜 뉴스레터 가져오기
- 가져오는 중 해당 셀에 로딩 스피너 표시

### 7-2. 첫 방문 온보딩
- 로그인 후 발신자 0개 감지 → 환영 메시지 + 설정 페이지 안내 오버레이
- 첫 발신자 등록 → 자동 2일 동기화 → 완료 후 메인 화면 전환

### 7-3. 페이지 접속 시 자동 동기화
- 기존 데이터 있는 사용자: 메인 화면 즉시 표시 + 백그라운드 2일 동기화
- SyncStatus 헤더 버튼에서 진행 상태 표시 (InitialSyncScreen 표시 안 함)

---

## 수정 파일 목록

| 구분 | 파일 | 주요 변경 내용 |
|------|------|--------------|
| **신규** | `backend/app/dependencies.py` | JWT 인증 의존성 |
| **신규** | `backend/app/routers/auth.py` | Google OAuth 라우터 |
| **신규** | `frontend/src/contexts/AuthContext.jsx` | 인증 컨텍스트 |
| **신규** | `frontend/src/components/LoginPage.jsx` (+CSS) | 로그인 페이지 |
| **신규** | `frontend/src/components/AuthCallback.jsx` | OAuth 콜백 처리 |
| **신규** | `frontend/src/components/MainLayout.jsx` | 메인 레이아웃 분리 |
| **수정** | `backend/app/services/db.py` | users 테이블, user_id 마이그레이션, 모든 CRUD 함수 |
| **수정** | `backend/app/services/gmail.py` | per-user Gmail 토큰, sync 함수 시그니처 |
| **수정** | `backend/app/services/gemini.py` | user_id 파라미터, per-user 처리 |
| **수정** | `backend/app/services/vector.py` | per-user 컬렉션 (`articles_{user_id}`) |
| **수정** | `backend/app/sync_state.py` | per-user lock/status 관리 함수 |
| **수정** | `backend/app/config.py` | OAuth/JWT/암호화 설정 추가 |
| **수정** | `backend/app/main.py` | APScheduler 제거, auth 라우터 등록 |
| **수정** | `backend/app/routers/articles.py` | 인증 가드 + user_id |
| **수정** | `backend/app/routers/categories.py` | 인증 가드 + user_id |
| **수정** | `backend/app/routers/newsletters.py` | 인증 가드 + user_id |
| **수정** | `backend/app/routers/search.py` | 인증 가드 + user_id |
| **수정** | `backend/app/routers/chat.py` | 인증 가드 + user_id |
| **수정** | `backend/app/routers/sync.py` | 인증 가드, per-user 동기화, /sync/date 추가 |
| **수정** | `backend/app/routers/senders.py` | 인증 가드, 발신자 등록 시 동기화 트리거 |
| **수정** | `frontend/src/App.jsx` | Routes 셋업, 인증 분기 |
| **수정** | `frontend/src/main.jsx` | BrowserRouter + AuthProvider 래핑 |
| **수정** | `frontend/src/api/client.js` | credentials, 401 처리, 신규 함수 |
| **수정** | `frontend/src/components/NewsletterCalendar.jsx` | 음영 + 클릭 시 날짜 동기화 |
| **수정** | `frontend/src/components/SyncStatus.jsx` | per-user 동기화 상태 표시 |
| **수정** | `frontend/src/components/InitialSyncScreen.jsx` | 브랜딩 변경 |
| **수정** | `frontend/index.html` | 타이틀 변경 |
| **수정** | `pyproject.toml` | 의존성 추가(authlib 등) / 제거(apscheduler) |

---

## 검증 시나리오

1. Google OAuth 로그인 → JWT 발급 → `GET /api/auth/me` 정상 응답
2. 신규 사용자: 온보딩 화면 → 발신자 등록 → 자동 2일 동기화 → 메인 화면 전환
3. 기존 사용자: 페이지 접속 → 즉시 메인 화면 + 백그라운드 동기화 (중복 건너뜀)
4. 캘린더 음영 날짜 클릭 → 해당 날짜 뉴스레터 가져오기 → 캘린더 갱신
5. 사용자 A/B 데이터 격리 확인 (서로의 기사/발신자 접근 불가)
6. 수동 동기화 버튼 → 최근 7일 동기화 정상 동작
7. Gmail 토큰 만료 시 자동 갱신 확인

Q의 지침에 따라 Claude Code - Claude Opus 4.6이 2026-02-24에 생성했습니다.
