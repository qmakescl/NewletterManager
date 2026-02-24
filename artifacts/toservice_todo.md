# 할일 목록: 다중 사용자 서비스 전환 (My News Archive)

> 작성일: 2026-02-24
> 상세 계획: `artifacts/toservice_implementationplan.md`

---

## Phase 1: DB 스키마 + 인증 기반

- [x] `pyproject.toml` — `authlib`, `httpx`, `python-jose[cryptography]`, `cryptography` 추가 / `apscheduler` 제거
- [x] `backend/app/config.py` — `google_client_id`, `google_client_secret`, `jwt_secret_key`, `token_encryption_key`, `frontend_url` 추가
- [x] `backend/.env` — 위 설정값 플레이스홀더 추가 (Google Cloud Console에서 OAuth 2.0 웹 앱 자격증명 생성 필요)
- [x] `backend/app/services/db.py` — `users` 테이블 CREATE 추가 (`init_db()` 내)
- [x] `backend/app/services/db.py` — `_migrate_add_user_id()` 구현 (4개 테이블 ALTER + 복합 UNIQUE 재생성)
- [x] `backend/app/services/db.py` — `init_db()`에서 `_migrate_add_user_id()` 호출
- [x] `backend/app/services/db.py` — `get_user_by_google_id()`, `upsert_user()`, `get_user_by_id()`, `update_user_gmail_token()` 함수 추가
- [x] `backend/app/dependencies.py` (신규) — `get_current_user(request)` JWT 인증 의존성 구현
- [x] `backend/app/routers/auth.py` (신규) — `GET /api/auth/login` 구현
- [x] `backend/app/routers/auth.py` — `GET /api/auth/callback` 구현 (코드 교환 → 토큰 암호화 저장 → JWT 쿠키 발급)
- [x] `backend/app/routers/auth.py` — `GET /api/auth/me` 구현
- [x] `backend/app/routers/auth.py` — `POST /api/auth/logout` 구현
- [x] `backend/app/main.py` — auth 라우터 등록, APScheduler 제거

---

## Phase 2: DB 함수 user_id 스코프 적용

- [x] `backend/app/services/db.py` — `_seed_senders()` 제거
- [x] `backend/app/services/db.py` — `get_newsletters(user_id)` 수정
- [x] `backend/app/services/db.py` — `get_articles(user_id, ...)` 수정
- [x] `backend/app/services/db.py` — `get_article_by_id(user_id, id)` 수정
- [x] `backend/app/services/db.py` — `insert_newsletter(user_id, ...)` 수정
- [x] `backend/app/services/db.py` — `newsletter_exists(user_id, email_id)` 수정
- [x] `backend/app/services/db.py` — `newsletter_exists_by_gmail_id(user_id, gmail_id)` 수정
- [x] `backend/app/services/db.py` — `get_senders(user_id)` 수정
- [x] `backend/app/services/db.py` — `get_active_sender_emails(user_id)` 수정
- [x] `backend/app/services/db.py` — `add_sender(user_id, name, email)` 수정
- [x] `backend/app/services/db.py` — `update_sender(user_id, sender_id, ...)` 수정
- [x] `backend/app/services/db.py` — `delete_sender(user_id, sender_id)` 수정
- [x] `backend/app/services/db.py` — `get_unprocessed_articles(user_id, batch_size)` 수정
- [x] `backend/app/services/db.py` — `get_daily_api_count(user_id, today)` 수정
- [x] `backend/app/services/db.py` — `increment_api_count(user_id, today)` 수정

---

## Phase 3: per-user Gmail + 동기화 아키텍처

- [x] `backend/app/services/gmail.py` — `token.json` 파일 기반 코드 제거
- [x] `backend/app/services/gmail.py` — `get_gmail_service_for_user(user_id)` 구현 (DB 토큰 로드 → Fernet 복호화 → Credentials 생성 → 만료 시 갱신 → DB 재저장)
- [x] `backend/app/services/gmail.py` — `_list_gmail_message_refs(user_id, days)` 수정
- [x] `backend/app/services/gmail.py` — `sync_emails(user_id, days)` 수정
- [x] `backend/app/services/gmail.py` — `sync_emails_for_date(user_id, target_date)` 신규 구현
- [x] `backend/app/sync_state.py` — per-user 구조로 전면 재작성 (`get_user_lock`, `get_user_sync_status`, `update_user_sync_status`)
- [x] `backend/app/main.py` — `_scheduled_sync()`, `_scheduler` 제거
- [x] `backend/app/main.py` — lifespan에서 APScheduler 등록/시작/종료 제거
- [x] `backend/app/main.py` — `_resume_ai_processing()` 제거
- [x] `backend/app/routers/sync.py` — `POST /api/sync` 에 `Depends(get_current_user)`, per-user lock/status 적용
- [x] `backend/app/routers/sync.py` — `GET /api/sync/status` 에 `Depends(get_current_user)` 적용
- [x] `backend/app/routers/sync.py` — `POST /api/sync/date` 신규 엔드포인트 구현
- [x] `backend/app/routers/senders.py` — `POST /api/senders` 성공 후 2일 동기화 백그라운드 트리거

---

## Phase 4: per-user AI + Vector

- [x] `backend/app/services/vector.py` — 컬렉션 이름 `articles` → `articles_{user_id}` 변경
- [x] `backend/app/services/vector.py` — 모든 함수에 `user_id` 파라미터 추가
- [x] `backend/app/services/gemini.py` — `run_ai_processing(user_id)` 수정
- [x] `backend/app/services/gemini.py` — `rag_query(user_id, message)` 수정
- [x] `backend/app/services/gemini.py` — `_check_daily_limit(user_id)` per-user 적용

---

## Phase 5: 모든 라우터 인증 가드

- [x] `backend/app/routers/articles.py` — `Depends(get_current_user)` + `user_id` 전달
- [x] `backend/app/routers/categories.py` — `Depends(get_current_user)` + `user_id` 전달
- [x] `backend/app/routers/newsletters.py` — `Depends(get_current_user)` + `user_id` 전달
- [x] `backend/app/routers/search.py` — `Depends(get_current_user)` + `user_id` 전달
- [x] `backend/app/routers/chat.py` — `Depends(get_current_user)` + `user_id` 전달
- [x] `backend/app/routers/senders.py` — `Depends(get_current_user)` + `user_id` 전달

---

## Phase 6: 프론트엔드 인증 + 라우팅

- [x] `frontend/` — `npm install react-router-dom`
- [x] `frontend/src/contexts/AuthContext.jsx` (신규) — `useAuth`, `AuthProvider`, `login()`, `logout()` 구현
- [x] `frontend/src/components/LoginPage.jsx` + CSS (신규) — "My News Archive" 브랜딩 + Google 로그인 버튼
- [x] `frontend/src/components/AuthCallback.jsx` (신규) — OAuth 콜백 처리 후 `/` 리다이렉트
- [x] `frontend/src/components/MainLayout.jsx` (신규) — App.jsx 기존 메인 레이아웃 이동
- [x] `frontend/src/main.jsx` — `<BrowserRouter>` + `<AuthProvider>` 래핑
- [x] `frontend/src/App.jsx` — Routes 셋업 (`/login`, `/auth/callback`, `/*`)
- [x] `frontend/src/api/client.js` — 모든 fetch에 `credentials: 'include'` 추가
- [x] `frontend/src/api/client.js` — 401 응답 시 `/login` 리다이렉트 처리
- [x] `frontend/src/api/client.js` — `fetchCurrentUser()` 함수 추가
- [x] `frontend/src/api/client.js` — `triggerDateSync(date)` 함수 추가
- [x] `frontend/index.html` — `<title>My News Archive</title>` 변경
- [x] `frontend/src/components/MainLayout.jsx` — header logo "My News Archive"로 변경
- [x] `frontend/src/components/InitialSyncScreen.jsx` — logo "My News Archive"로 변경

---

## Phase 7: 캘린더 + 온보딩 기능 강화

- [x] `frontend/src/components/NewsletterCalendar.jsx` — 지난 평일 중 뉴스레터 없는 날 `.missing-newsletter` 음영 처리
- [x] `frontend/src/components/NewsletterCalendar.jsx` — 빈 날짜 클릭 시 `triggerDateSync(date)` 호출
- [x] `frontend/src/components/NewsletterCalendar.jsx` — 날짜별 동기화 중 로딩 표시
- [x] `frontend/src/components/MainLayout.jsx` — 발신자 0개 감지 시 온보딩 오버레이 표시
- [x] `frontend/src/components/MainLayout.jsx` — 페이지 접속 시 백그라운드 2일 동기화 (기존 데이터 있을 때)
- [x] 헤더에 사용자 프로필 표시 (사진/로그아웃 버튼)

---

## 사전 준비 사항 (수동 작업 필요)

- [ ] Google Cloud Console: OAuth 2.0 웹 앱 자격증명 생성
  - 승인된 리다이렉트 URI: `http://localhost:3000/auth/callback`
  - 필요 스코프: `openid`, `email`, `profile`, `https://www.googleapis.com/auth/gmail.readonly`
- [ ] `.env` 파일에 실제 값 입력: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET_KEY`, `TOKEN_ENCRYPTION_KEY`
- [ ] (개발 중) Google Cloud Console 테스트 사용자 등록

Q의 지침에 따라 Claude Code - Claude Opus 4.6이 2026-02-24에 생성했습니다.
