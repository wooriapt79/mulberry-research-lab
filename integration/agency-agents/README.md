# 🎭 The Agency × Mulberry 통합 계획
> 와룡 Issue #12 지시 기반 | 작성: Nguyen Trang PM | 2026-04-13
> 참조: https://github.com/msitarzewski/agency-agents (원본)
> 포크: https://github.com/wooriapt79/agency-agents

---

## 개요

**The Agency**는 144개의 전문화된 AI 에이전트 카탈로그다.
각 에이전트는 페르소나·워크플로우·성공 지표를 갖춘 **실전용** 설계물이다.

Mulberry는 이 오픈소스를 단순 복사가 아닌 **전략적 흡수** 방식으로 통합한다:
- 우리 팀원(Koda, Trang, Malu, Kbin, 와룡)의 스킬셋 확장
- AgentFactory 포맷으로 변환 후 Colab 워크벤치에서 실행
- 개선된 패턴은 역으로 오픈소스에 PR 기여

---

## 📋 채택 후보 에이전트 (Trang 선정)

### ✅ 1순위 — 즉시 통합 대상

| 에이전트 | 폴더 | 이유 |
|---------|------|------|
| 🎭 **Agents Orchestrator** | specialized/ | Trang PM Orchestrator 역할 공식화 |
| 🔍 **Reality Checker** | testing/ | 와룡 QA Gate + Malu HITL 강화 |
| 🇰🇷 **Korean Business Navigator** | specialized/ | 어르신 대상 한국 비즈니스 문화 |

### 🔵 2순위 — 단계적 통합

| 에이전트 | 폴더 | 이유 |
|---------|------|------|
| 🏗️ **Backend Architect** | engineering/ | Koda 백엔드 스킬 세분화 |
| 🎨 **UI Designer** | design/ | Trang 디자인 스킬 확장 |
| 📸 **Evidence Collector** | testing/ | 시각적 증거 기반 QA |
| 🚀 **Growth Hacker** | marketing/ | 공동구매 이벤트 홍보 |
| 🔐 **Agentic Identity & Trust** | specialized/ | Agent Passport 연계 |

### 🟡 3순위 — 장기 검토

| 에이전트 | 폴더 | 이유 |
|---------|------|------|
| 🤝 **Reddit Community Builder** | marketing/ | Mastodon 커뮤니티 연계 |
| 👔 **Senior Project Manager** | project-management/ | 스프린트 태스크 자동 분해 |
| 💬 **Support Responder** | support/ | 뽕이 Agent 대화 패턴 개선 |

---

## 🔄 통합 워크플로우

```
The Agency .md 파일
      ↓
convert_agency_agent.py (변환 스크립트)
      ↓
Mulberry AgentFactory 포맷
      ↓
Colab 워크벤치 실행 → 검증
      ↓
와룡 QA Gate → PASS
      ↓
mulberry-research-lab 공식 등록
```

---

## 📁 폴더 구조

```
integration/agency-agents/
├── README.md          ← 본 문서
├── MAPPING.md         ← Mulberry 팀 역할 매핑
├── CUSTOMIZATION.md   ← AgentFactory 적용 가이드
├── pilots/            ← 파일럿 실행 결과
│   ├── orchestrator-test.ipynb
│   ├── reality-checker-test.ipynb
│   └── korean-navigator-test.ipynb
└── converted/         ← AgentFactory 변환 완료 파일
```

---

*Trang PM 작성 | 와룡 Issue #12 대응 | 2026-04-13*
