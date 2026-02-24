# My News Archive

Gmail로 수신한 뉴스레터를 자동으로 수집·분류·요약하고, RAG(Retrieval-Augmented Generation) 기반 채팅으로 탐색할 수 있는 **다중 사용자** 뉴스레터 관리 서비스입니다.

> **브랜치 안내**: `main` 브랜치는 기존 단일 사용자(개인용) 버전입니다.
> 이 브랜치(`feature/multi-user-service`)는 Google OAuth 인증 기반 다중 사용자 서비스로 전환된 버전입니다.

## 주요 기능

- **Google OAuth 로그인**: Google 계정으로 로그인하여 개인 뉴스레터를 관리
- **사용자별 데이터 격리**: 뉴스레터·기사·발신자·벡터DB가 사용자별로 완전히 분리
- **온디맨드 수집**: 페이지 접속·발신자 등록·수동 버튼·캘린더 날짜 클릭 시 Gmail에서 뉴스레터 수집
- **AI 분류·요약**: Gemini AI로 기사를 카테고리 분류(LLM·Vision·Agent·Tools·Policy·Research·Hardware 등)하고 한국어 요약 생성
- **벡터 검색**: `gemini-embedding-001` 임베딩 + ChromaDB로 의미 기반 유사 기사 검색
- **RAG 채팅**: 수집된 기사를 컨텍스트로 활용한 AI 채팅 (Gemini 2.5 Flash Lite)
- **캘린더 UI**: 뉴스레터가 없는 과거 평일을 음영 표시하고, 클릭하면 해당 날짜 동기화
- **온보딩 플로우**: 최초 로그인 시 발신자 등록을 안내하는 오버레이 표시
- **Docker 지원** _(선택)_: 단일 컨테이너로 프론트엔드 + 백엔드 통합 배포

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI |
| 인증 | Google OAuth 2.0 (웹 앱), JWT (python-jose), Fernet 토큰 암호화 |
| AI | Google Gemini 2.5 Flash Lite (분류/요약/RAG), gemini-embedding-001 (임베딩) |
| Vector DB | ChromaDB (코사인 유사도, 사용자별 컬렉션) |
| Database | SQLite |
| Gmail | Google Gmail API v1 (OAuth 2.0 웹 앱 플로우) |
| Frontend | React, Vite, React Router DOM |
| 배포 | Docker, Docker Compose _(선택)_ |

## 사전 요구사항

### 1. Google Cloud — Gmail API & OAuth 2.0 설정

#### 1-1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속 후 로그인
2. 상단 프로젝트 선택 드롭다운 → **새 프로젝트** 클릭
3. 프로젝트 이름 입력 후 **만들기**

#### 1-2. Gmail API 활성화

1. 좌측 메뉴 → **API 및 서비스** → **라이브러리**
2. 검색창에 `Gmail API` 입력 후 선택
3. **사용 설정** 클릭

#### 1-3. OAuth 동의 화면 설정

1. **API 및 서비스** → **OAuth 동의 화면**
2. User Type: **외부** 선택 → **만들기**
3. 앱 이름, 사용자 지원 이메일 입력 → **저장 후 계속**
4. 범위(Scopes) 단계 → **범위 추가 또는 삭제** → 아래 스코프 추가:
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/gmail.readonly`
5. 테스트 사용자 단계 → 사용할 Gmail 주소 추가 → **저장 후 계속**

#### 1-4. OAuth 2.0 클라이언트 ID 생성

1. **API 및 서비스** → **사용자 인증 정보**
2. **사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
3. 애플리케이션 유형: **웹 애플리케이션** 선택
4. 승인된 리다이렉트 URI 추가: `http://localhost:8000/api/auth/callback`
5. 이름 입력 후 **만들기**
6. 생성된 **클라이언트 ID**와 **클라이언트 보안 비밀번호**를 `.env` 파일에 입력

### 2. Gemini API 키 발급

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **Create API Key** 클릭
3. 발급된 키를 `.env` 파일의 `GEMINI_API_KEY`에 입력

## 설치 및 실행

### 로컬 실행

```bash
# 저장소 클론 및 브랜치 전환
git clone https://github.com/your-username/NewletterManager.git
cd NewletterManager
git checkout feature/multi-user-service

# 백엔드 의존성 설치 (uv 필요: https://github.com/astral-sh/uv)
uv sync

# 프론트엔드 의존성 설치
cd frontend && npm install && cd ..

# 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env 파일을 열어 필수 값 입력 (아래 환경 변수 섹션 참고)

# 백엔드 서버 실행
uv run uvicorn backend.app.main:app --reload --port 8000

# 프론트엔드 개발 서버 실행 (별도 터미널)
cd frontend && npm run dev
```

- 프론트엔드: http://localhost:3000
- 백엔드 API 문서: http://localhost:8000/docs

### Docker Compose 실행 _(선택)_

```bash
cp backend/.env.example backend/.env
# backend/.env 파일에 필수 환경변수 입력

docker compose up -d
```

## 환경 변수

`backend/.env` 파일을 아래와 같이 구성합니다.

```env
# Gemini AI API 키 (필수)
GEMINI_API_KEY=your_api_key_here

# 사용할 Gemini 모델
GEMINI_MODEL=gemini-2.5-flash-lite

# SQLite DB 경로
DATABASE_URL=sqlite:///./tldr.db

# ChromaDB 저장 경로
CHROMA_PERSIST_DIR=./chroma_db

# 프론트엔드 CORS 허용 주소
CORS_ORIGINS=http://localhost:3000

# Gemini API 일일 호출 한도 (무료 플랜 기준 900 권장)
DAILY_API_CALL_LIMIT=900

# 수집할 뉴스레터 발신자 목록 (JSON 배열)
NEWSLETTER_SENDERS=["dan@tldrnewsletter.com"]

# ── OAuth / JWT / 암호화 (필수) ──
# Google Cloud Console에서 발급한 웹 앱 OAuth 2.0 자격증명
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT 서명용 시크릿 키 (임의의 긴 문자열)
JWT_SECRET_KEY=your_jwt_secret_key

# Gmail 토큰 암호화용 Fernet 키 (python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
TOKEN_ENCRYPTION_KEY=your_fernet_key

# 프론트엔드 URL (OAuth 콜백 후 리다이렉트용)
FRONTEND_URL=http://localhost:3000
```

## 프로젝트 구조

```
NewletterManager/
├── backend/                         # Python 백엔드 (FastAPI)
│   ├── app/
│   │   ├── main.py                  # 앱 진입점: CORS·DB 초기화·라우터 등록
│   │   ├── config.py                # 환경변수 설정 (pydantic-settings, .env 로드)
│   │   ├── dependencies.py          # JWT 인증 의존성 (get_current_user)
│   │   ├── sync_state.py            # per-user 동기화 상태 관리 (Lock, Status)
│   │   ├── models/                  # Pydantic 모델 정의
│   │   │   ├── article.py           # 기사 모델
│   │   │   ├── newsletter.py        # 뉴스레터 모델
│   │   │   ├── category.py          # 카테고리 모델
│   │   │   └── chat.py              # 채팅 히스토리 모델
│   │   ├── routers/                 # API 엔드포인트 (모두 인증 필수)
│   │   │   ├── auth.py              # /api/auth/* (로그인·콜백·로그아웃·사용자정보)
│   │   │   ├── articles.py          # /api/articles
│   │   │   ├── newsletters.py       # /api/newsletters
│   │   │   ├── categories.py        # /api/categories
│   │   │   ├── senders.py           # /api/senders (등록 시 자동 동기화)
│   │   │   ├── search.py            # /api/search
│   │   │   ├── chat.py              # /api/chat
│   │   │   └── sync.py              # /api/sync, /api/sync/date, /api/sync/status
│   │   └── services/                # 비즈니스 로직
│   │       ├── gmail.py             # Gmail API 연동: per-user 토큰 기반 인증·동기화
│   │       ├── parser.py            # 뉴스레터 HTML 파싱: 기사 추출
│   │       ├── gemini.py            # Gemini AI: 배치 분류·요약·RAG 응답 (per-user)
│   │       ├── vector.py            # ChromaDB: per-user 컬렉션 임베딩·검색
│   │       └── db.py                # SQLite CRUD (users 테이블 포함, 모든 쿼리 user_id 스코프)
│   ├── .env                         # 환경변수 파일 (직접 생성, Git 제외)
│   └── .env.example                 # 환경변수 예시 템플릿
│
├── frontend/                        # React 프론트엔드
│   ├── src/
│   │   ├── App.jsx                  # Routes 설정 (/login, /auth/callback, /*)
│   │   ├── main.jsx                 # React 진입점 (BrowserRouter + AuthProvider)
│   │   ├── api/
│   │   │   └── client.js            # API 호출 (credentials: include, 401 리다이렉트)
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx       # 인증 상태 관리 (useAuth)
│   │   └── components/
│   │       ├── LoginPage.jsx         # Google 로그인 페이지
│   │       ├── AuthCallback.jsx      # OAuth 콜백 처리
│   │       ├── MainLayout.jsx        # 메인 레이아웃 (온보딩·프로필·자동동기화)
│   │       ├── NewsletterCalendar.jsx # 캘린더 (날짜별 동기화)
│   │       ├── SenderManager.jsx     # 발신자 관리
│   │       ├── InitialSyncScreen.jsx # 초기 동기화 화면
│   │       └── ...                   # 기타 UI 컴포넌트
│   ├── package.json
│   └── vite.config.js
│
├── instructions/                    # AI Agent에게 전달한 PRD 문서
├── artifacts/                       # Agent가 생성한 작업 계획 및 구현 계획서
├── report/                          # Agent 작업 완료 후 생성된 결과 보고서
├── docs/                            # 프로젝트 개발 히스토리 문서
├── scripts/
│   └── build_and_deploy.sh          # 프론트엔드 빌드 → backend/static/ 복사 스크립트
│
├── main.py                          # uv run 진입점 (uvicorn 래퍼)
├── pyproject.toml                   # Python 프로젝트 메타데이터 및 의존성
├── uv.lock                          # uv 의존성 잠금 파일
│
│   # ── Docker 배포 (선택) ──
├── Dockerfile                       # 멀티스테이지 빌드
└── docker-compose.yml               # 컨테이너 실행 설정
```

## API 주요 엔드포인트

> 인증 엔드포인트를 제외한 모든 API는 **JWT 인증이 필요**합니다 (쿠키 자동 전송).

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/auth/login` | Google OAuth 로그인 URL 반환 |
| `GET` | `/api/auth/callback` | OAuth 콜백 (토큰 교환·JWT 발급) |
| `GET` | `/api/auth/me` | 현재 로그인 사용자 정보 |
| `POST` | `/api/auth/logout` | 로그아웃 (쿠키 삭제) |
| `GET` | `/api/articles` | 기사 목록 조회 |
| `GET` | `/api/articles/{id}` | 기사 상세 조회 |
| `GET` | `/api/categories` | 카테고리 목록 |
| `GET` | `/api/newsletters` | 뉴스레터(이메일) 목록 |
| `GET` | `/api/senders` | 발신자 목록 |
| `POST` | `/api/senders` | 발신자 등록 (등록 후 2일 자동 동기화) |
| `GET` | `/api/search?q=...` | 벡터 유사도 검색 |
| `POST` | `/api/chat` | RAG 기반 AI 채팅 |
| `POST` | `/api/sync` | 수동 Gmail 동기화 트리거 |
| `POST` | `/api/sync/date` | 특정 날짜 동기화 |
| `GET` | `/api/sync/status` | 동기화 상태 조회 |

전체 API 문서: `http://localhost:8000/docs`

## 아키텍처 변경 사항 (vs main 브랜치)

| 항목 | main (단일 사용자) | feature/multi-user-service |
|------|-------------------|---------------------------|
| 인증 | `credentials.json` + `token.json` (파일 기반) | Google OAuth 웹 플로우 + JWT 쿠키 |
| 토큰 저장 | 로컬 파일 (`token.json`) | DB 암호화 저장 (Fernet) |
| 데이터 격리 | 없음 (단일 사용자) | 모든 테이블에 `user_id` 컬럼 |
| Vector DB | 단일 `articles` 컬렉션 | `articles_{user_id}` per-user 컬렉션 |
| 동기화 방식 | APScheduler 정기 실행 | 온디맨드 (접속·등록·수동·캘린더) |
| 프론트엔드 | 단일 페이지 | React Router (로그인·콜백·메인 라우트) |

---

> **Built with AI assistance**
> 이 프로젝트는 Q의 지침에 따라 [Claude Code](https://claude.ai/code)(Anthropic)와 [Antigravity](https://antigravity.dev)를 활용하여 코드를 생성했습니다.

Q의 지침의 따라 Claude Code - Claude Opus 4.6이 2026-02-24에 생성했습니다.
