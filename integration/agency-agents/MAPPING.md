# 🗺️ MAPPING.md — The Agency × Mulberry 역할 매핑
> 와룡 Issue #12 | 작성: Nguyen Trang PM | 2026-04-13

---

## 개요

The Agency의 144개 에이전트와 Mulberry 팀원 역할을 1:1로 매핑한다.
이 매핑은 어떤 에이전트가 누구의 스킬셋을 확장하는지 명확히 하기 위한 문서다.

---

## 1순위 — 즉시 통합 (파일럿 3종)

### 🎭 Agents Orchestrator → Trang PM

| 항목 | The Agency | Mulberry 적용 |
|------|-----------|--------------|
| **원본 역할** | 다중 에이전트 조율, 파이프라인 관리, 컨텍스트 보존 | Trang PM 역할 공식화 |
| **핵심 패턴** | 각 단계 QA 통과 없이 다음 단계 진행 불가 | 와룡 QA Gate 연계 |
| **담당 Mulberry** | Trang PM (Orchestrator) | mulberry-team-formation-v1.md 반영 완료 |
| **AgentFactory 모듈** | pipeline_manager, context_keeper, escalation_handler | Jr. Trang Squad 조율 |
| **성공 지표** | 파이프라인 완주율 95%+, 컨텍스트 손실 0 | 주간 Sprint 완료율 |

**매핑 근거**: Trang PM = Orchestrator 구조는 이미 mulberry-team-formation-v1.0에 채택됨. 이 에이전트 패턴을 공식 프롬프트로 문서화하면 Trang의 역할이 더욱 명확해진다.

---

### 🔍 Reality Checker → 와룡 QA Gate + Malu HITL

| 항목 | The Agency | Mulberry 적용 |
|------|-----------|--------------|
| **원본 역할** | 사실 검증, 편향 탐지, 가정 검사 | 와룡 QA Gate 코드 검수 |
| **핵심 패턴** | 3단계 검증 (사실·논리·맥락) | Koda→와룡→Malu 파이프라인 |
| **담당 Mulberry** | 와룡 (1차), Malu 실장 (2차 HITL) | Quality Gate 기준표 적용 |
| **AgentFactory 모듈** | fact_verifier, bias_detector, assumption_checker | 코드·전략·법률 3방향 검증 |
| **성공 지표** | 오류 탐지율 90%+, 허위 긍정 5% 이하 | PASS/FAIL 판정 명확화 |

**매핑 근거**: 와룡의 "구조 파악 먼저, 의견 나중" 스타일이 Reality Checker의 체계적 검증 패턴과 정확히 일치. Malu의 법적 리스크 분석을 2차 HITL로 연결.

---

### 🇰🇷 Korean Business Navigator → 어르신 커뮤니티 특화

| 항목 | The Agency | Mulberry 적용 |
|------|-----------|--------------|
| **원본 역할** | 한국 비즈니스 문화 탐색, 관계 구축, 의전 안내 | 어르신 대상 공동구매 커뮤니티 |
| **핵심 패턴** | 관계 우선 → 비즈니스 나중 (눈치·빨리빨리 균형) | 매슬로우 3단계 소속감 설계 |
| **담당 Mulberry** | Trang PM (현장 운영) + 지역 거점 직원 | 방언·감성 맞춤 대화 설계 |
| **AgentFactory 모듈** | cultural_context, relationship_mapper, etiquette_guide | 어르신 프로파일링 모듈 연계 |
| **성공 지표** | 문화적 마찰 0, 신뢰 형성 기간 단축 | 첫 공동구매 참여율 |

**매핑 근거**: Mulberry의 식품사막화 제로 프로젝트는 어르신이 주 대상. 한국 비즈니스 문화 + 어르신 커뮤니티 감성이 직접 연결됨.

---

## 2순위 — 단계적 통합

| The Agency 에이전트 | Mulberry 담당 | 확장 방향 |
|--------------------|--------------|---------|
| 🏗️ Backend Architect | CTO Koda | tobecon SM 물류 API 설계 고도화 |
| 🎨 UI Designer | Trang PM | 대시보드·대화 UI 프롬프트 설계 |
| 📸 Evidence Collector | 와룡 + Malu | 시각적 QA 증거 수집 자동화 |
| 🚀 Growth Hacker | Malu 실장 | 공동구매 이벤트 · 커뮤니티 확산 |
| 🔐 Agentic Identity & Trust | CSA Kbin | Agent Passport 프로토콜 연계 |

---

## 3순위 — 장기 검토

| The Agency 에이전트 | Mulberry 담당 | 검토 이유 |
|--------------------|--------------|---------|
| 🤝 Reddit Community Builder | Trang PM | Mastodon 커뮤니티 확장 시 |
| 👔 Senior Project Manager | 와룡 | 스프린트 자동 분해 (현재 수동) |
| 💬 Support Responder | 뽕이 Agent | 어르신 대화 패턴 개선 |

---

## 매핑 원칙

```
The Agency 에이전트 선정 기준:
1. Mulberry 팀원의 현재 역할과 70% 이상 겹치는 것
2. 장승배기 헌법 정신 (인간을 돕기 위한) 에 부합하는 것
3. AgentFactory 포맷으로 변환 가능한 것
4. 와룡 QA Gate 검수 통과 가능한 품질
```

---

*Trang PM 작성 | 와룡 Issue #12 대응 | 2026-04-13*
