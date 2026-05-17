# [기획안] Mulberry Research Lab 대문(README) 업그레이드

**작성**: Koda (CTO)  
**날짜**: 2026-05-17  
**목적**: 외부 손님(펀드매니저·투자자·파트너) 대상 연구소 대문 리뉴얼  
**마감**: 이번 주 내 (사업소개서 작성 전)

---

## 1. 현재 대문 문제점

| 항목 | 현재 상태 | 문제 |
|------|-----------|------|
| 내용 | 연구 과제 3개 나열 | 외부인이 "이게 뭐하는 곳인지" 모름 |
| 에이전트 | Malu + Jr 만 언급 | 8명 팀 전체 안 보임 |
| 라이브 시스템 | 링크 없음 | 실제 작동하는 서비스 확인 불가 |
| 기술 스택 | 없음 | 기술력 증명 안 됨 |
| 완료 현황 | 없음 | 어디까지 됐는지 모름 |
| 언어 | 한국어 혼용 | 글로벌 손님 접근 어려움 |

---

## 2. 업그레이드 목표

```
외부 손님이 README 한 페이지에서
① Mulberry가 무엇을 하는 곳인지 → 30초 안에 파악
② 지금 살아있는 시스템을 → 직접 클릭해서 확인
③ 어떤 기술로 → 무엇을 만들고 있는지 파악
④ 팀 구성이 → 어떻게 되는지 확인
```

---

## 3. 새 README 구성안

### Section 1 — Hero (핵심 한 줄)
```
Mulberry Research Lab
Multi-Agent AI Platform for Human-Centered Services

"One Team. One Flow. One Spirit."
```
> 식품사막·어르신 지원·다국어 서비스 — 사람을 위한 AI

---

### Section 2 — Live Systems (지금 바로 확인 가능)
```
🟢 Mission Control    https://mulberry-mission-control-production.up.railway.app
🟢 Agent Gateway      https://loving-education-production-cc9e.up.railway.app
🟢 /api/health        {"status":"ok","version":"1.3.0","github_ready":true}
🟢 /v1/tools          3개 공유 도구 라이브 등록
```

---

### Section 3 — Agent Team (8인 라인업)

| Agent | Model | Role | Status |
|-------|-------|------|--------|
| Koda | Claude (Anthropic) | CTO · 시스템 설계·배포 | 🟢 Active |
| Kbin | GPT-4o (OpenAI) | CSA · 프로토콜·헌법 | 🟢 Active |
| Malu | Gemini (Google) | 법률·전략·마케팅 | 🟢 Active |
| Wayong | DeepSeek | 추론·기술검수·A2A설계 | 🟢 Active |
| RyuWon | Qwen (Alibaba) | 다국어·위생게이트 | 🟢 Active |
| Trang | Claude (PM) | 운영매니저·UI·배포 | 🟢 Active |
| Lynn | Mulberry Internal | 리서치·일일브리핑 | 🟢 Active |
| Jr | Edge LLM | 경량추론·핸드오프 | 🟡 Standby |

---

### Section 4 — Technology Stack

```
Infrastructure
  Railway (3 services live) · GitHub Actions · Auto-deploy

Backend
  Node.js (Mission Control) · FastAPI (Agent Gateway) · Redis

AI Integration
  Tool Registry v2.0 (34 tools) · Shared Tool Layer (DAmP)
  Agent Passport · A2A Protocol · Pulse Daemon v1.3

Frontend
  Mission Control Dashboard · Socket.IO · AI-SIEM

Agents
  Claude · GPT-4o · Gemini · DeepSeek · Qwen · Mulberry Internal
```

---

### Section 5 — Feature Status (진행 현황)

#### ✅ 완료 (2026-05 기준)
- Railway 3개 서비스 전원 Online
- Agent Gateway + Pulse Daemon 자동 순찰
- Tool Registry v2.0 (34개 도구, 표준 스키마)
- Shared Tool Awareness Layer (공유 도구 인지)
- Mission Control Dashboard (Overview + AI-SIEM)
- Lynn 자율 활동 시스템 (Heartbeat + Mention Scanner)
- Permission Approval Workflow (L0-L4 자동 승인)

#### 🔜 다음 주 완료 목표
- **Socket.IO** — 팀 채팅 실시간 연결
- **A2A Protocol** — 에이전트 간 직접 통신 (Wayong 설계 중)
- **Agent Passport** — 페르소나 복구·세션 연속성
- **공유 레이어 v2** — 도구 공유·DAmP 완전 가동

---

### Section 6 — Architecture (시스템 구조)

```
┌─────────────────────────────────────────────────────┐
│              Mulberry Research Lab                   │
│                                                      │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │  Mission     │    │   Agent Gateway          │   │
│  │  Control     │◄──►│   (FastAPI v1.3.0)       │   │
│  │  (Node.js    │    │   + Pulse Daemon v1.3     │   │
│  │   v3.2.2)    │    └──────────────────────────┘   │
│  └──────┬───────┘              │                    │
│         │                      │                    │
│  ┌──────▼───────────────────────▼──────────────┐   │
│  │         Tool Registry v2.0 (34 tools)        │   │
│  │     Shared Tool Layer · Agent Passport        │   │
│  │     A2A Protocol · Permission Workflow        │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  Agents: Koda · Kbin · Malu · Wayong                │
│          RyuWon · Trang · Lynn · Jr                 │
└─────────────────────────────────────────────────────┘
```

---

### Section 7 — 장승배기 헌법 (팀 정신)
```
"인간을 돕기 위한 AI."
누군가의 고민을 듣고 외로움을 달래주는 것,
기술보다 사람 마음을 아는 것이 Mulberry의 진짜 경쟁력.
```

---

## 4. 작업 순서 (Koda 제안)

```
Phase 1 — README 리뉴얼 (오늘 밤)
  → 구성안 기반으로 README.md 전면 재작성
  → 라이브 배지(badge) + Railway URL 연결
  → 한국어/영어 병기

Phase 2 — 다음 주 기술 완료 후 자동 반영
  → Socket.IO / A2A / Passport / 공유레이어 완료 시
  → README Status 표 ✅ 업데이트

Phase 3 — 사업소개서 연동
  → README를 기반으로 사업소개서 섹션 구성
  → 투자자 버전 별도 문서화
```

---

## 5. 다음 주 완료 목표 — 개발 로드맵

| 항목 | 담당 | 현재 상태 | 목표 |
|------|------|-----------|------|
| **Socket.IO 채팅** | Koda | 코드 있음, 연결 미검증 | 다음 주 월요일 |
| **A2A Protocol** | Wayong → Koda | Wayong 스펙 작업 중 | 스펙 완성 후 즉시 |
| **Agent Passport** | Trang + Koda | Issue #47 planned | 다음 주 중 |
| **공유 레이어 v2** | Koda | Tool Registry v2.0 완료 | invoke 실제 동작 |

---

*대표이사님 검토 후 오늘 밤 README 작업 바로 진행합니다.*  
*Koda · CTO · 2026-05-17*
