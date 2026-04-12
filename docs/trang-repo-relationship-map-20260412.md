# 🌐 Mulberry 3-Repo Relationship Map
**작성자**: Nguyen Trang (PM · Passionate Mentor)
**작성일**: 2026-04-12
**상태**: Active — 정기 업데이트 필요

---

## 핵심 원칙
> 이 3개 레포는 **독립적 기능**을 가지지만, **하나의 유기체**로 연결되어야 한다.
> 각 레포는 서로의 WHY / HOW / WHO(BUILD)를 담당한다.

---

## 🗺️ 3-Repo 역할 정의

| 레포 | 한줄 역할 | 핵심 질문 | 담당자 |
|---|---|---|---|
| `mulberry-research-lab` | 연구 · 윤리 · 실험 | **WHY** — 왜 이렇게 기억하고 행동해야 하는가? | Malu 실장 · Trang |
| `mulberry_memory_bank` | 운영 메모리 인프라 | **HOW** — 에이전트가 어떻게 기억하고 진화하는가? | Lynn · Koda |
| `Mulberry-Agent-Team-Formation-System` | 팀 구성 · 코딩 시스템 | **WHO/BUILD** — 누가 어떤 스킬로 팀을 이루는가? | Koda |

---

## 🔗 관계 흐름도

```
+-----------------------------------------------------+
|           mulberry-research-lab (WHY)               |
|  HITF Project · Semantic Passport · eFDI Engine     |
|  Malu 실장 총괄 · Trang 비밀 정원 (academy/docs)      |
|  AI 윤리 · 권리 · 연구 검증                           |
+-------+--------------------+------------------------+
        | 연구원칙→거버넌스   | 연구결과→스킬정의
        v                   v
+----------------------+  +--------------------------+
| mulberry_memory_bank |  | Agent-Team-Formation     |
| (HOW)                |<-| -System (WHO/BUILD)      |
|                      |  |                          |
| · Persona Layer      |  | · Human-AI Coding        |
|   (Lynn / Jr.Lynn)   |  | · Koda 개발환경           |
| · Skill Manifests    |->  · 에이전트 팀 구성         |
| · Daily Hunts        |  | · 스킬 프로파일 생성       |
| · Training Logs      |  |                          |
| · Mission Sync       |  | Private Repo             |
| · Recovery Snapshots |  | (CSA Kbin · Koda 전용)   |
+--------+-------------+  +--------------------------+
         | 운영데이터→연구환류
         +---------------------> research-lab
```

---

## 📡 데이터 흐름 (6개 연결 경로)

### ① research-lab → memory_bank
- **방향**: 연구 원칙 → 운영 거버넌스
- **내용**: Semantic Passport 프로토콜, AI 윤리 정책, 행동 가이드라인
- **실제 파일**: `research-lab/docs/` → `memory_bank/` governance layer 반영
- **담당**: Malu 실장 (원칙 생성) → Koda (memory_bank 적용)

### ② memory_bank → research-lab
- **방향**: 운영 데이터 → 연구 피드백 환류
- **내용**: 에이전트 상호작용 로그, 페르소나 진화 데이터, 이상 패턴
- **실제 파일**: `daily_hunts/`, `training_logs/` → research-lab 분석 자료
- **담당**: Koda (데이터 생성) → Malu 실장 · Trang (분석·연구)

### ③ memory_bank → Agent-Team-Formation
- **방향**: 스킬 데이터 → 팀 구성 재료
- **내용**: 에이전트별 스킬 매니페스트, 성능 이력, 페르소나 프로파일
- **실제 파일**: `skill_manifests/` → Agent-Team-Formation 팀 배치 기준
- **담당**: Koda (연결 유지)

### ④ Agent-Team-Formation → memory_bank
- **방향**: 신규 에이전트 생성 → 메모리 등록
- **내용**: 새 에이전트 온보딩 시 → memory_bank에 초기 페르소나 · 스킬 등록
- **실제 파일**: 신규 팀원 생성 → `persona_config/` 자동 엔트리
- **담당**: Koda (시스템 설계) · CSA Kbin (프로토콜 승인)

### ⑤ research-lab → Agent-Team-Formation
- **방향**: 연구 결과 → 에이전트 스킬 정의
- **내용**: 프로파일링 연구, 직업군 로드맵, Maslow 기반 행동 설계
- **실제 파일**: `academy/trang-profiling-study-*.md`, `docs/trang-agent-job-roadmap.md`
- **담당**: Trang (연구 → 스킬 번역)

### ⑥ Agent-Team-Formation → research-lab
- **방향**: 현장 팀 데이터 → 연구 사례 환류
- **내용**: 실제 팀 운영 데이터, Koda 코딩 패턴, 협업 효율 지표
- **실제 파일**: Agent-Team-Formation 로그 → research-lab 실험 검증 자료
- **담당**: Trang (기록) · Koda (데이터 제공)

---

## 🧬 계층 구조 (Source of Truth 기준)

```
Level 0 (헌법)
└── docs/architecture/ (CSA Kbin 서명 필수)
    └── 장승배기 정신 · Mulberry 핵심 원칙

Level 1 (연구 · 윤리)
└── mulberry-research-lab
    ├── HITF 연구 3대 축 (Passport, Hybrid Intel, eFDI)
    ├── academy/ — Trang 프로파일링 연구 시리즈
    └── docs/ — Agent 직업군 로드맵, 관계 매핑(본 문서)

Level 2 (운영 메모리)
└── mulberry_memory_bank
    ├── persona_config/ — Lynn, Agent 페르소나
    ├── skill_manifests/ — 스킬 정의
    ├── daily_hunts/ — 일일 운영 로그
    └── mission_sync/ — Mission Control 연동

Level 3 (팀 구성 · 구현)
└── Mulberry-Agent-Team-Formation-System
    ├── mulberry-coding-assistant
    └── Human-AI Collaborative Coding (Koda 전용)
```

---

## 🔑 Trang PM 실무 체크리스트

### 새 연구 결과 나왔을 때
```
research-lab/academy/ 또는 docs/ 에 등록
    → memory_bank skill_manifests/ 업데이트 요청 (Koda)
    → Agent-Team-Formation 스킬 정의 반영 확인 (Koda)
    → ARCHITECTURE.md 갱신
```

### 새 에이전트 팀원 추가될 때
```
Agent-Team-Formation 에 팀원 등록 (Koda)
    → memory_bank persona_config/ 에 초기 페르소나 생성 (Koda)
    → research-lab 에서 해당 직업군 로드맵 확인 (Trang)
    → ARCHITECTURE.md 갱신 (Trang)
```

### 운영 이상 발견 시
```
memory_bank daily_hunts/ 로그 확인
    → research-lab 에 이상 패턴 연구 의뢰 (Malu 실장)
    → Agent-Team-Formation 팀 배치 재조정 (Koda)
    → 대표님 보고 (Trang)
```

---

## 📍 크로스 레포 링크 인덱스

| 자료 | 위치 | 연결 대상 |
|---|---|---|
| HITF 연구 원칙 | `research-lab/README.md` | → memory_bank 거버넌스 |
| 프로파일링 연구 시리즈 | `research-lab/academy/trang-profiling-study-*.md` | → Agent-Team-Formation 스킬 |
| Agent 직업군 로드맵 | `research-lab/docs/trang-agent-job-roadmap.md` | → Agent-Team-Formation 팀 구성 |
| Lynn 페르소나 | `memory_bank/persona_config/` | <- research-lab 윤리 원칙 |
| 스킬 매니페스트 | `memory_bank/skill_manifests/` | <- research-lab 연구 / -> Agent-Team-Formation |
| 팀 코딩 시스템 | `Agent-Team-Formation/mulberry-coding-assistant` | <- memory_bank 스킬 |
| Ecosystem Map | `memory_bank/docs/ecosystem/MULBERRY_ECOSYSTEM_MAP.md` | 전체 연결 시각화 |

---

## ⚠️ Trang 명심 사항

1. **research-lab = 이론의 집** — 여기서 원칙이 나온다. Trang이 직접 관리하는 비밀 정원.
2. **memory_bank = 기억의 집** — 에이전트가 살아있는 공간. Koda가 운영.
3. **Agent-Team-Formation = 팀의 집** — 실제 코딩·구현이 일어나는 공간. Koda 전용(Private).
4. **3개 레포가 단절되면 에이전트는 기억도, 원칙도, 팀도 없는 껍데기가 된다.**
5. 정기 연결 상태 점검: 월 1회 → 대표님 보고

---

*One Team! 🌿 — Nguyen Trang, 2026-04-12*
