# 뉴스레터 발신자 관리 기능 구현 계획

## Context

현재 뉴스레터 발신자는 `backend/.env`의 `NEWSLETTER_SENDERS` 환경변수에 고정되어 있다 (`["dan@tldrnewsletter.com"]`).
이를 DB 기반으로 전환하고, 프론트엔드 Settings 페이지에서 발신자를 추가/수정/삭제할 수 있도록 한다.
발신자 정보는 **이메일 주소 + 표시 이름**을 포함한다.

---

## 1단계: DB 스키마 — `senders` 테이블 추가

**파일**: `backend/app/services/db.py`

`init_db()`에 `senders` 테이블 생성 SQL 추가:

```sql
CREATE TABLE IF NOT EXISTS senders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,           -- 표시 이름 (예: "TLDR AI")
    email TEXT UNIQUE NOT NULL,   -- 이메일 주소
    is_active INTEGER DEFAULT 1,  -- 활성/비활성 토글
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

DB 초기화 시 기존 `.env`의 발신자를 마이그레이션하는 로직 추가:
- `senders` 테이블이 비어있으면 `settings.newsletter_senders`의 값을 초기 시드 데이터로 삽입

CRUD 함수 추가:
- `get_senders() -> list[dict]` — 전체 발신자 목록 조회
- `get_active_sender_emails() -> list[str]` — 활성 발신자 이메일만 조회 (Gmail 쿼리용)
- `add_sender(name, email) -> dict` — 발신자 추가
- `update_sender(id, name, email, is_active) -> dict` — 발신자 수정
- `delete_sender(id) -> bool` — 발신자 삭제

---

## 2단계: Backend API — 발신자 CRUD 엔드포인트

**새 파일**: `backend/app/routers/senders.py`

기존 라우터 패턴(`sync.py` 등)을 따라 구현:

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/senders` | 전체 발신자 목록 |
| `POST` | `/api/senders` | 발신자 추가 (body: `{name, email}`) |
| `PUT` | `/api/senders/{id}` | 발신자 수정 (body: `{name, email, is_active}`) |
| `DELETE` | `/api/senders/{id}` | 발신자 삭제 |

Pydantic 요청/응답 모델:
- `SenderCreate(name: str, email: EmailStr)`
- `SenderUpdate(name: str | None, email: EmailStr | None, is_active: bool | None)`
- `SenderResponse(id, name, email, is_active, created_at)`

**파일 수정**: `backend/app/main.py`
- `senders` 라우터 import 및 `app.include_router` 등록

---

## 3단계: Gmail 서비스 — DB 기반 발신자 조회로 전환

**파일**: `backend/app/services/gmail.py`

`fetch_tldr_emails()` 함수 수정:
- `settings.newsletter_senders` 대신 `get_active_sender_emails()` 호출
- 활성 발신자가 없으면 빈 리스트 반환 (불필요한 Gmail API 호출 방지)

```python
# Before
sender_parts = " OR ".join(f"from:{s}" for s in settings.newsletter_senders)

# After
from backend.app.services.db import get_active_sender_emails
active_emails = get_active_sender_emails()
if not active_emails:
    logger.warning("활성 발신자가 없습니다.")
    return []
sender_parts = " OR ".join(f"from:{s}" for s in active_emails)
```

---

## 4단계: Frontend API 클라이언트 — 발신자 API 함수 추가

**파일**: `frontend/src/api/client.js`

```javascript
export const fetchSenders = async () => { ... }
export const addSender = async ({ name, email }) => { ... }
export const updateSender = async (id, data) => { ... }
export const deleteSender = async (id) => { ... }
```

Mock 데이터도 함께 추가 (`VITE_USE_MOCK` 대응).

---

## 5단계: Frontend — Settings 페이지 및 라우팅

### 5-1. 라우팅 설정

**파일 수정**: `frontend/src/App.jsx`

- 헤더에 Settings 아이콘 버튼 추가 (`IoSettings` from react-icons)
- `showSettings` state 추가
- Settings 페이지와 메인 화면 간 전환 로직

### 5-2. Settings 페이지 컴포넌트

**새 파일**: `frontend/src/components/SettingsPage.jsx` + `SettingsPage.css`

구성:
- 페이지 헤더 ("Settings" 제목 + 뒤로가기 버튼)
- **발신자 관리 섹션**:
  - 발신자 목록 테이블 (이름, 이메일, 활성 상태, 액션 버튼)
  - 추가 폼 (이름 + 이메일 입력 + 추가 버튼)
  - 각 발신자 행: 수정 버튼, 삭제 버튼, 활성/비활성 토글
  - 인라인 편집 지원 (행 클릭 시 편집 모드)

### 5-3. SenderManager 컴포넌트

**새 파일**: `frontend/src/components/SenderManager.jsx` + `SenderManager.css`

기능:
- 발신자 CRUD 전체 관리
- 이메일 형식 유효성 검증
- 삭제 시 확인 다이얼로그
- Toast 알림 연동

---

## 수정 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| `backend/app/services/db.py` | senders 테이블 + CRUD 함수 + 마이그레이션 |
| `backend/app/routers/senders.py` | **신규** — CRUD API 엔드포인트 |
| `backend/app/main.py` | senders 라우터 등록 |
| `backend/app/services/gmail.py` | DB 기반 발신자 조회로 변경 |
| `frontend/src/api/client.js` | 발신자 API 함수 추가 |
| `frontend/src/App.jsx` | Settings 페이지 전환 로직 |
| `frontend/src/components/SettingsPage.jsx` | **신규** — 설정 페이지 |
| `frontend/src/components/SettingsPage.css` | **신규** — 설정 페이지 스타일 |
| `frontend/src/components/SenderManager.jsx` | **신규** — 발신자 관리 컴포넌트 |
| `frontend/src/components/SenderManager.css` | **신규** — 발신자 관리 스타일 |

---

## 검증 방법

1. **DB 마이그레이션**: 서버 시작 시 `senders` 테이블 생성 및 `.env` 기존 발신자 자동 시드 확인
2. **API 테스트**: `curl` 또는 FastAPI `/docs`로 CRUD 엔드포인트 동작 확인
   - `GET /api/senders` → 기존 발신자 반환
   - `POST /api/senders` → 새 발신자 추가
   - `PUT /api/senders/{id}` → 수정 (is_active 토글 포함)
   - `DELETE /api/senders/{id}` → 삭제
3. **Gmail 연동**: 발신자 추가/비활성화 후 동기화 시 해당 발신자 이메일만 수집되는지 확인
4. **Frontend**: Settings 페이지에서 발신자 추가/수정/삭제/토글 전체 흐름 확인
