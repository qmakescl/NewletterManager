# TLDR AI Newsletter Manager
## Master PRD — Product Requirements Document

> **Version 1.3** | February 2026 | Alpha 전략: 옵션 A (완전 무료)
> **GitHub:** github.com/qmakescl

---

## 역할 분담 요약

| 구성 요소 | 담당 도구 | 주요 역할 |
|-----------|-----------|-----------|
| Backend | Claude Code | Gmail API, Gemini API, DB, RAG, REST API |
| Frontend | Antigravity | UI/UX, 뉴스 카드, 검색 인터페이스, 채팅 UI |
| 통합 & 배포 | Claude Code | Frontend 빌드 병합, Docker, 최종 검증 |

---

## 1. 프로젝트 개요

### 1.1 목적

TLDR AI 뉴스레터를 Gmail에서 자동으로 수집하고, Gemini 2.5 Flash-Lite API로 분류·한국어 요약하여 개인화된 AI 뉴스 아카이브를 구축한다. NotebookLM 스타일의 자연어 질의 인터페이스를 통해 저장된 기사를 탐색하고 인사이트를 도출할 수 있는 개인용 도구를 만드는 것이 목표다.

### 1.2 배경

- TLDR AI 뉴스레터는 매일 다수의 AI 관련 기사를 영문 요약 형태로 제공
- Gmail에 쌓이는 뉴스레터는 검색·분류·맥락 연결이 어려움
- Claude Code 학습과 실용적 도구 개발을 병행하는 프로젝트

### 1.3 범위

| 항목 | 내용 |
|------|------|
| In Scope | Gmail 연동, 뉴스 파싱, Gemini 분류/요약, 벡터 검색, RAG 질의, 웹 UI |
| Out of Scope | 다중 사용자 지원, 유료 서비스, 모바일 앱, 타 뉴스레터 지원 (v1 기준) |
| 플랫폼 | macOS (Apple Silicon) 로컬 실행 → 추후 컨테이너 배포 가능 |

---

## 2. 시스템 아키텍처

### 2.1 전체 흐름

```
Gmail API → 파서 → Gemini 2.5 Flash-Lite → DB/벡터 → RAG 엔진 → 웹 UI
```

| 단계 | Gmail API | 파서 | Gemini 2.5 Flash-Lite | DB/벡터 | RAG 엔진 | 웹 UI |
|------|-----------|------|----------------------|---------|---------|-------|
| 역할 | 메일 수집·필터링 | 기사 구조화 | 분류/요약/태깅 | 저장·인덱싱 | 맥락 검색·답변 | 사용자 인터페이스 |
| 담당 | Backend (Claude Code) | Backend | Backend | Backend | Backend | Frontend (Antigravity) |

### 2.2 기술 스택

| 레이어 | 기술 | 비고 |
|--------|------|------|
| 언어 | Python 3.11+ | OS 중립적, pip 패키지 관리 |
| Gmail 연동 | google-api-python-client | OAuth 2.0 인증 |
| AI 처리 | google-genai (Gemini 2.5 Flash-Lite) | 모델 코드: `gemini-2.5-flash-lite` (무료 1,000 RPD) |
| 관계형 DB | SQLite → PostgreSQL | 개발 시 SQLite, 배포 시 PostgreSQL |
| 벡터 DB | ChromaDB | Gemini Embedding API 활용 |
| API 서버 | FastAPI | REST API, 비동기 처리 |
| Frontend | Antigravity (React 기반) | 컴포넌트 기반 UI 생성 |
| 스케줄러 | APScheduler | 매일 자동 수집 |

---

## 3. 개발 단계 (4-Phase)

### Phase 1 — Gmail 연동 & 파싱

- Google OAuth 2.0 인증 플로우 구현
- Gmail API로 TLDR AI 발신자(tldr.tech) 필터링 및 메일 수집
- HTML/텍스트 본문에서 기사 제목, 영문 요약, 원문 URL 구조화 파싱
- 파싱 결과 JSON 및 SQLite 저장
- 중복 수집 방지 로직 (Message-ID 기준)

### Phase 2 — Gemini 2.5 Flash-Lite AI 처리 (옵션 A: 완전 무료)

- 모델: `gemini-2.5-flash-lite` (무료 티어 1,000 RPD — 알파 충분)
- 배치 처리: 기사 5개를 1회 API 호출로 묶어 처리 (무료 한도 최적화)
- 중복 처리 방지: DB에 처리 완료 기사 기록, 재호출 차단
- 카테고리 자동 분류: LLM / Vision / Agent / Tools / Policy / Research 등
- 한국어 요약 생성 (영문 원문 → 한국어 2-3문장)
- 중요도 스코어링 (1-5점, 산업 영향력 기준)
- 연관 키워드 태깅 (최대 5개)
- Gemini Embedding API로 벡터 인덱싱 (ChromaDB)

> **향후 전환:** 알파 검증 후 `gemini-2.5-flash`로 업그레이드 시 `GEMINI_MODEL` 환경 변수 1줄 수정만으로 전환 가능하도록 설계

### Phase 3 — 검색 & 저장

- SQLite 텍스트 검색 (카테고리, 날짜, 키워드 필터)
- ChromaDB 시맨틱 검색 ("LLM 에이전트 관련 기사" 등 자연어 검색)
- FastAPI REST 엔드포인트 구현
- APScheduler 자동 수집 스케줄러

### Phase 4 — NotebookLM 스타일 질의 인터페이스

- 저장 기사를 context로 활용한 RAG 파이프라인 구현
- Gemini의 1M 토큰 컨텍스트 창 활용
- "이번 달 가장 화제된 모델은?" 같은 자연어 질의 지원
- Frontend(Antigravity) 채팅 UI와 연동
- Claude Code로 Frontend 빌드 통합 및 최종 배포

---

## 4. Frontend-Backend 인터페이스 계약

### 4.1 REST API 엔드포인트

| Method | Endpoint | 담당 | 설명 |
|--------|----------|------|------|
| `GET` | `/api/articles` | Backend | 기사 목록 조회 (페이징, 필터) |
| `GET` | `/api/articles/{id}` | Backend | 기사 상세 조회 |
| `GET` | `/api/search` | Backend | 시맨틱 검색 (q= 파라미터) |
| `POST` | `/api/chat` | Backend | RAG 기반 자연어 질의 |
| `GET` | `/api/categories` | Backend | 카테고리 목록 및 기사 수 |
| `GET` | `/api/newsletters` | Backend | 캘린더 활성일 목록 + 날짜별 기사 수 |
| `GET` | `/api/articles?dates=` | Backend | 복수 날짜 선택 기사 합산 조회 |
| `POST` | `/api/sync` | Backend | Gmail 수동 동기화 트리거 |

### 4.2 기사 데이터 스키마

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | `string` | UUID |
| `title` | `string` | 기사 제목 (영문) |
| `summary_en` | `string` | TLDR 원문 영문 요약 |
| `summary_ko` | `string` | Gemini 생성 한국어 요약 |
| `url` | `string` | 원문 기사 URL |
| `category` | `string` | AI 카테고리 (LLM/Vision/Agent 등) |
| `tags` | `string[]` | Gemini 생성 키워드 태그 |
| `importance` | `number (1-5)` | Gemini 중요도 스코어 |
| `published_at` | `datetime` | 뉴스레터 발행일 |
| `email_id` | `string` | Gmail Message-ID (중복 방지) |
| `newsletter_id` | `string` | 소속 뉴스레터 FK (날짜 조회용) |

---

## 5. 알파 테스트 비용 전략 (옵션 A)

### 5.1 완전 무료 구성

| 항목 | 비용 | 무료 한도 | 비고 |
|------|------|-----------|------|
| Gmail API | $0 | 충분 | 개인 Gmail 기준 |
| Gemini 2.5 Flash-Lite | $0 | 1,000 RPD | 배치 5개 기준 일 4~5회 호출로 충분 |
| Gemini Embedding | $0 | 1,000 RPD | text-embedding-004 무료 티어 |
| SQLite | $0 | 로컬 무제한 | 로컬 파일 기반 DB |
| ChromaDB | $0 | 로컬 무제한 | 로컬 실행 |
| FastAPI 서버 | $0 | 로컬 실행 | macOS 로컬 호스팅 |
| **합계** | **$0 / 월** | — | **알파 기간 전체 무료** |

### 5.2 무료 한도 내 운영 설계 원칙

- **배치 처리:** 기사 5개 → 1 API 호출 (TLDR AI 1통 기준 약 4~5회 호출)
- **캐싱:** 이미 처리된 기사는 DB 확인 후 API 재호출 차단
- **환경 변수 분리:** `GEMINI_MODEL`로 모델명 관리 → 업그레이드 시 `.env` 수정만으로 전환
- **재시도 로직:** 지수 백오프(Exponential Backoff)로 429 에러 대응

### 5.3 알파 → 정식 전환 기준

| 단계 | 트리거 조건 | 예상 월 비용 |
|------|------------|------------|
| 알파 (현재) | 개인 사용, 기능 검증 | $0 |
| 베타 (모델 업그레이드) | 품질 향상 필요 시 | ~$1 (Flash로 전환) |
| 정식 (외부 배포) | 외부 접근 필요 시 | ~$5~10 (서버 포함) |

---

## 6. 비기능 요구사항

| 항목 | 목표 | 비고 |
|------|------|------|
| API 응답 시간 | 목록 조회 < 500ms | 로컬 SQLite 기준 |
| AI 처리 시간 | 기사 당 < 3초 | Gemini 2.5 Flash-Lite 기준 |
| 동기화 주기 | 매일 1회 자동 + 수동 트리거 | APScheduler |
| 보안 | OAuth 토큰 로컬 암호화 저장 | `.env` 파일, `.gitignore` 필수 |
| OS 호환성 | macOS (Apple Silicon) 우선 | Python 패키지 중립적 설계 |

---

## 7. 통합 & 배포 (Claude Code 담당)

### 7.1 통합 절차

1. Antigravity에서 Frontend 빌드 산출물 생성 (`dist/` 또는 `build/`)
2. Claude Code Backend 프로젝트의 `static/` 디렉토리로 빌드 파일 복사
3. FastAPI에서 static 파일 서빙 설정 추가
4. 통합 환경 E2E 테스트 실행
5. Docker Compose로 최종 패키징

### 7.2 디렉토리 구조

```
project/
├── backend/              # Claude Code 관할 — FastAPI 서버, AI 파이프라인
│   ├── app/
│   ├── static/           # Frontend 빌드 결과물 (통합 시 복사)
│   └── ...
├── frontend/             # Antigravity 관할 — React UI 소스
│   ├── src/
│   └── dist/             # 빌드 산출물 → backend/static/으로 복사
└── docker-compose.yml    # Claude Code 작성 — 통합 배포 설정
```

---

*TLDR AI Newsletter Manager | Master PRD v1.3 | github.com/qmakescl*
