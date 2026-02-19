# My Newsletter Manager

Gmail로 수신한 뉴스레터를 자동으로 수집·분류·요약하고, RAG(Retrieval-Augmented Generation) 기반 채팅으로 탐색할 수 있는 개인용 뉴스레터 관리 시스템입니다.

## 주요 기능

- **자동 수집**: Gmail API를 통해 매일 지정 시각에 뉴스레터를 자동 수신
- **AI 분류·요약**: Gemini AI로 기사를 카테고리 분류(LLM·Vision·Agent·Tools·Policy·Research·Hardware 등)하고 한국어 요약 생성
- **벡터 검색**: `gemini-embedding-001` 임베딩 + ChromaDB로 의미 기반 유사 기사 검색
- **RAG 채팅**: 수집된 기사를 컨텍스트로 활용한 AI 채팅 (Gemini 2.5 Flash Lite)
- **REST API**: FastAPI 기반 백엔드 (`/api/articles`, `/api/search`, `/api/chat` 등)
- **Docker 지원** _(선택)_: 단일 컨테이너로 프론트엔드 + 백엔드 통합 배포

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, APScheduler |
| AI | Google Gemini 2.5 Flash Lite (분류/요약/RAG), gemini-embedding-001 (임베딩) |
| Vector DB | ChromaDB (코사인 유사도) |
| Database | SQLite |
| Gmail | Google Gmail API v1 (OAuth 2.0) |
| 배포 | Docker, Docker Compose _(선택)_ |

## 사전 요구사항

### 1. Google Cloud — Gmail API & OAuth 2.0 설정

Gmail에서 이메일을 읽으려면 Google Cloud 프로젝트에서 OAuth 2.0 인증을 설정해야 합니다.

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
4. 범위(Scopes) 단계 → **범위 추가 또는 삭제** → `https://www.googleapis.com/auth/gmail.readonly` 추가
5. 테스트 사용자 단계 → 본인 Gmail 주소 추가 → **저장 후 계속**

#### 1-4. OAuth 2.0 클라이언트 ID 생성

1. **API 및 서비스** → **사용자 인증 정보**
2. **사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
3. 애플리케이션 유형: **데스크톱 앱** 선택
4. 이름 입력 후 **만들기**
5. 생성된 클라이언트 정보에서 **JSON 다운로드** → 파일 이름을 `credentials.json`으로 저장

#### 1-5. credentials.json 배치

```
backend/
└── credentials.json   ← 다운로드한 파일을 여기에 배치
```

> **최초 실행 시**: 서버가 시작되면 브라우저가 열리며 Google 계정 로그인 및 권한 동의를 요청합니다.
> 완료되면 `backend/token.json`이 자동 생성되며, 이후 재인증 없이 사용할 수 있습니다.

### 2. Gemini API 키 발급

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **Create API Key** 클릭
3. 발급된 키를 `.env` 파일의 `GEMINI_API_KEY`에 입력

## 설치 및 실행

### 로컬 실행 (uv)

```bash
# 저장소 클론
git clone https://github.com/your-username/NewletterManager.git
cd NewletterManager

# 의존성 설치 (uv 필요: https://github.com/astral-sh/uv)
uv sync

# 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env 파일을 열어 GEMINI_API_KEY 입력

# credentials.json 배치 (사전 요구사항 참고)
# backend/credentials.json

# 서버 실행
uv run uvicorn backend.app.main:app --reload --port 8000
```

서버 시작 후 http://localhost:8000 에서 프론트엔드, http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

### Docker Compose 실행 _(선택)_

`Dockerfile`과 `docker-compose.yml`은 컨테이너 환경 배포를 위한 **선택적 옵션**입니다.
로컬 `uv` 실행만으로도 모든 기능을 사용할 수 있습니다.

```bash
# credentials.json 배치 후
cp backend/.env.example backend/.env
# backend/.env 파일에 GEMINI_API_KEY 입력

docker compose up -d
```

> **주의**: Docker 환경에서는 최초 실행 전에 **로컬에서 한 번 실행하여 `token.json`을 먼저 생성**해두어야 합니다.
> OAuth 인증은 브라우저가 필요한 대화형 과정이므로 컨테이너 내부에서 직접 수행할 수 없습니다.
> 생성된 `backend/token.json`은 Docker 컨테이너에 마운트됩니다.

## 환경 변수

`backend/.env` 파일을 아래와 같이 구성합니다.

```env
# Gemini AI API 키 (필수)
GEMINI_API_KEY=your_api_key_here

# 사용할 Gemini 모델
GEMINI_MODEL=gemini-2.5-flash-lite

# Gmail OAuth 인증 파일 경로
GMAIL_CREDENTIALS_PATH=./credentials.json

# SQLite DB 경로
DATABASE_URL=sqlite:///./tldr.db

# ChromaDB 저장 경로
CHROMA_PERSIST_DIR=./chroma_db

# 자동 동기화 시각 (24시간제, 기본: 매일 07:00)
SYNC_SCHEDULE_HOUR=7

# 프론트엔드 CORS 허용 주소
CORS_ORIGINS=http://localhost:3000

# Gemini API 일일 호출 한도 (무료 플랜 기준 900 권장)
DAILY_API_CALL_LIMIT=900

# 수집할 뉴스레터 발신자 목록 (JSON 배열)
NEWSLETTER_SENDERS=["dan@tldrnewsletter.com"]
```

## 프로젝트 구조

```
NewletterManager/
├── backend/                         # Python 백엔드 (FastAPI)
│   ├── app/
│   │   ├── main.py                  # 앱 진입점: CORS·DB 초기화·스케줄러·라우터 등록
│   │   ├── config.py                # 환경변수 설정 (pydantic-settings, .env 로드)
│   │   ├── models/                  # SQLite 테이블 정의
│   │   │   ├── article.py           # 기사 모델 (제목·URL·요약·카테고리·태그 등)
│   │   │   ├── newsletter.py        # 뉴스레터(이메일) 모델
│   │   │   ├── category.py          # 카테고리 모델
│   │   │   └── chat.py              # 채팅 히스토리 모델
│   │   ├── routers/                 # API 엔드포인트
│   │   │   ├── articles.py          # GET /api/articles, GET /api/articles/{id}
│   │   │   ├── newsletters.py       # GET /api/newsletters
│   │   │   ├── categories.py        # GET /api/categories
│   │   │   ├── search.py            # GET /api/search (벡터 유사도 검색)
│   │   │   ├── chat.py              # POST /api/chat (RAG 채팅)
│   │   │   └── sync.py              # POST /api/sync (수동 동기화 트리거)
│   │   └── services/                # 비즈니스 로직
│   │       ├── gmail.py             # Gmail API 연동: 이메일 수집·증분 동기화
│   │       ├── parser.py            # 뉴스레터 HTML 파싱: 기사 추출
│   │       ├── gemini.py            # Gemini AI: 배치 분류·요약·RAG 응답 생성
│   │       ├── vector.py            # ChromaDB: 임베딩 생성(배치)·저장·유사도 검색
│   │       └── db.py                # SQLite CRUD 헬퍼
│   ├── static/                      # 프론트엔드 빌드 산출물 (서버 기동 시 자동 서빙)
│   ├── credentials.json             # Google OAuth 클라이언트 파일 (직접 배치, Git 제외)
│   ├── token.json                   # OAuth 액세스 토큰 (최초 인증 후 자동 생성, Git 제외)
│   ├── .env                         # 환경변수 파일 (직접 생성, Git 제외)
│   └── .env.example                 # 환경변수 예시 템플릿
│
├── frontend/                        # React 프론트엔드
│   ├── src/
│   │   ├── App.jsx                  # 루트 컴포넌트
│   │   ├── main.jsx                 # React 진입점
│   │   ├── api/                     # 백엔드 API 호출 모듈
│   │   ├── components/              # UI 컴포넌트
│   │   └── styles/                  # 전역 스타일
│   ├── dist/                        # 빌드 산출물 (npm run build)
│   ├── package.json
│   └── vite.config.js
│
├── instructions/                    # AI Agent에게 전달한 PRD 문서
│   ├── PRD_Master_OptionA.md        # 전체 시스템 설계 지침
│   ├── PRD_Backend_ClaudeCode_OptionA.md   # 백엔드 구현 지침 (Claude Code용)
│   └── PRD_Frontend_Antigravity_OptionA.md # 프론트엔드 구현 지침 (Antigravity용)
│
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
│   # ── Docker 배포 (선택) ──────────────────────────────────────────────────
├── Dockerfile                       # 멀티스테이지 빌드: 프론트엔드(Node) + 백엔드(Python)
└── docker-compose.yml               # 컨테이너 실행 설정 (볼륨·환경변수·포트 매핑)
```

## API 주요 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/articles` | 기사 목록 조회 |
| `GET` | `/api/articles/{id}` | 기사 상세 조회 |
| `GET` | `/api/categories` | 카테고리 목록 |
| `GET` | `/api/newsletters` | 뉴스레터(이메일) 목록 |
| `GET` | `/api/search?q=...` | 벡터 유사도 검색 |
| `POST` | `/api/chat` | RAG 기반 AI 채팅 |
| `POST` | `/api/sync` | 수동 Gmail 동기화 트리거 |

전체 API 문서: `http://localhost:8000/docs`

---

> **Built with AI assistance**
> 이 프로젝트는 Q의 지침에 따라 [Claude Code](https://claude.ai/code)(Anthropic)와 [Antigravity](https://antigravity.dev)를 활용하여 코드를 생성했습니다.
