# TLDR AI Newsletter Manager — 변경 이력

> **프로젝트:** TLDR AI Newsletter Manager
> **GitHub:** github.com/qmakescl
> **작성일:** 2026년 2월 18일
> **대화:** [Claude Chat](https://claude.ai/share/0e6114c0-3fff-4fdf-a137-8550402384f5)

---

| # | 버전 | 요청 내용 | 변경 내역 | 영향 문서 |
|---|------|-----------|-----------|-----------|
| 1 | v1.0 | TLDR AI 뉴스레터를 별도로 관리하는 앱 아이디어 제안 | 프로젝트 방향 설정. Gmail 연동 → AI 처리 → 검색 → RAG 질의 4단계 구조 확정 | — |
| 2 | v1.0 | AI 처리 단계에 Gemini API 사용 반영 | Phase 2 모델을 `gemini-1.5-flash` 로 초안 작성 | — |
| 3 | v1.0 | `gemini-1.5-flash` → `gemini-2.5-flash` 로 변경 | 공식 문서 확인 후 모델 코드를 `gemini-2.5-flash` 로 교체 | — |
| 4 | v1.0 | PRD 문서 작성 요청 (Antigravity=Frontend, Claude Code=Backend, 통합은 Claude Code) | Master / Backend / Frontend 3종 PRD `.docx` 최초 생성 | PRD_Master.docx, PRD_Backend_ClaudeCode.docx, PRD_Frontend_Antigravity.docx |
| 5 | v1.0 | 프로젝트 구축 비용 및 알파 테스트 전략 검토 | 옵션 A(완전 무료) / B(월 ~$1) / C(최적화 무료) 3가지 전략 분석 제시 | — |
| 6 | v1.1 | 알파 테스트 전략을 **옵션 A(완전 무료)** 로 확정 후 PRD 재생성 | 모델을 `gemini-2.5-flash-lite`(1,000 RPD 무료)로 교체, 배치 처리·캐싱·지수 백오프 무료 한도 보호 로직 추가, `GEMINI_MODEL` 환경 변수 분리, 비용 전략 섹션 신설 | PRD_Master_OptionA.docx, PRD_Backend_ClaudeCode_OptionA.docx, PRD_Frontend_Antigravity_OptionA.docx |
| 7 | v1.1 | PRD 문서 전체를 Markdown 파일로 변환 요청 | `.docx` 3종을 `.md` 로 재작성. 코드 예시(SDK 사용법, `.env.example`, pip 설치 명령어), ASCII 레이아웃, API 요청/응답 JSON 예시, 컴포넌트 파일 구조 등 Markdown 전용 내용 추가 | PRD_Master_OptionA.md, PRD_Backend_ClaudeCode_OptionA.md, PRD_Frontend_Antigravity_OptionA.md |
| 8 | v1.2 | 날짜별 뉴스레터 선택 기능 추가 요청 — **뉴스레터 목록(날짜 리스트)** 방식, 좌측 사이드바 하단 배치 | `NewsletterDateList` 컴포넌트 신설, `GET /api/newsletters` 엔드포인트 추가, `newsletters` DB 테이블 및 `articles.newsletter_id` FK 추가, URL 파라미터 상태 유지(`?date=`) | PRD_Master_OptionA.md, PRD_Backend_ClaudeCode_OptionA.md, PRD_Frontend_Antigravity_OptionA.md |
| 9 | v1.3 | 날짜 선택 방식을 **캘린더 UI + 복수 날짜 선택** 으로 변경 | `NewsletterDateList` → `NewsletterCalendar` 컴포넌트로 교체, 달력 UI에서 복수 날짜 토글 선택, 선택된 날짜들의 기사를 합산하여 메인 그리드 표시, API를 단수(`?date=`) → 복수(`?dates=`) 쿼리로 변경, 응답에 `selected_dates` 필드 추가 | PRD_Master_OptionA.md, PRD_Backend_ClaudeCode_OptionA.md, PRD_Frontend_Antigravity_OptionA.md |

---

## 버전별 문서 현황

| 버전 | Master | Backend | Frontend | 주요 변경 요약 |
|------|--------|---------|----------|----------------|
| v1.0 | PRD_Master.docx | PRD_Backend_ClaudeCode.docx | PRD_Frontend_Antigravity.docx | 최초 작성, `gemini-2.5-flash` |
| v1.1 | PRD_Master_OptionA.docx → .md | PRD_Backend_ClaudeCode_OptionA.docx → .md | PRD_Frontend_Antigravity_OptionA.docx → .md | 옵션 A 무료 전략, Flash-Lite 적용 |
| v1.2 | PRD_Master_OptionA.md | PRD_Backend_ClaudeCode_OptionA.md | PRD_Frontend_Antigravity_OptionA.md | 날짜 리스트 필터 추가 |
| v1.3 | PRD_Master_OptionA.md | PRD_Backend_ClaudeCode_OptionA.md | PRD_Frontend_Antigravity_OptionA.md | 캘린더 UI + 복수 날짜 선택으로 변경 |

---

*TLDR AI Newsletter Manager | history.md | github.com/qmakescl*
