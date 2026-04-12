# ⚙️ CUSTOMIZATION.md — AgentFactory 변환 가이드
> 와룡 Issue #12 | 작성: Nguyen Trang PM | 2026-04-13

---

## 개요

The Agency `.md` 파일을 Mulberry AgentFactory 포맷으로 변환하는 방법을 정의한다.
이 가이드를 따르면 `convert_agency_agent.py` 스크립트를 통해 반자동 변환이 가능하다.

---

## AgentFactory 포맷 구조

```yaml
# Mulberry AgentFactory 표준 포맷

agent_id: [팀원코드]-[역할명]-v[버전]
name: "[에이전트 한국어 이름]"
base_from: "agency-agents/[폴더]/[원본파일명].md"
mulberry_owner: "[담당 팀원]"
qa_gate: "와룡"
registered: "[등록일]"

persona:
  role: "[역할 한 줄 정의]"
  style: "[말투·접근 방식]"
  philosophy: "[장승배기 헌법 연계 철학]"

capabilities:
  primary: []    # 핵심 기능 (원본에서 직접 채택)
  adapted: []    # Mulberry 맞춤 수정 항목
  excluded: []   # 제외한 원본 기능 (이유 포함)

workflow:
  input: "[입력 형식]"
  process: []    # 처리 단계
  output: "[출력 형식]"
  qa_checkpoint: "[와룡 검수 기준]"

success_metrics:
  - metric: "[지표명]"
    target: "[목표값]"
    current: "측정 예정"

mulberry_notes: |
  [Mulberry 특화 적용 메모]
```

---

## 변환 절차 (Step-by-Step)

### Step 1 — 원본 분석

```
The Agency 원본 파일 열기
     ↓
핵심 섹션 추출:
  - Persona / Role
  - Core Capabilities
  - Workflow Steps
  - Success Metrics
     ↓
Mulberry 팀원 역할과 70% 이상 겹치는 항목 표시
```

### Step 2 — Mulberry 컨텍스트 적용

```
장승배기 헌법 정신 확인
     ↓
어르신 대상 / 식품사막화 해결 / 공동구매 커뮤니티 관련성 검토
     ↓
한국어 로컬라이제이션:
  - 영어 표현 → 한국어 맥락으로 재해석
  - 문화적 뉘앙스 조정 (눈치·빨리빨리·관계 우선)
  - 어르신 대화 패턴 반영 필요 시 추가
```

### Step 3 — convert_agency_agent.py 실행

```python
# convert_agency_agent.py 사용법 (예시)
python convert_agency_agent.py \
  --input "agency-agents/specialized/agents-orchestrator.md" \
  --output "converted/trang-orchestrator-v1.yaml" \
  --owner "Trang PM" \
  --locale "ko-KR"
```

**변환 스크립트 담당**: CTO Koda (구현) → 와룡 (검수)

### Step 4 — Colab 워크벤치 검증

```
converted/*.yaml 파일 → Colab 노트북 업로드
     ↓
파일럿 실행:
  pilots/orchestrator-test.ipynb
  pilots/reality-checker-test.ipynb
  pilots/korean-navigator-test.ipynb
     ↓
결과 기록 → 와룡 QA Gate 제출
```

### Step 5 — 와룡 QA Gate

| 검수 항목 | 기준 | 와룡 판정 |
|---------|------|---------|
| 원본 의도 보존 | 핵심 역할 변질 없음 | PASS/FAIL |
| 장승배기 정신 부합 | 인간 중심 목적 유지 | PASS/FAIL |
| AgentFactory 포맷 | 표준 YAML 구조 준수 | PASS/FAIL |
| 한국어 품질 | 자연스러운 로컬라이제이션 | PASS/FAIL |

**3회 FAIL 시 → Trang PM이 대표님에게 에스컬레이션**

### Step 6 — mulberry-research-lab 공식 등록

```
와룡 PASS 확인
     ↓
Trang PM → mulberry-research-lab/integration/agency-agents/converted/ 커밋
     ↓
History.md 기록 업데이트
     ↓
대표님 보고
```

---

## 파일럿 3종 변환 계획

### 1. Agents Orchestrator → trang-orchestrator-v1

```yaml
agent_id: trang-orchestrator-v1
name: "Trang PM Orchestrator"
base_from: "agency-agents/specialized/agents-orchestrator.md"
mulberry_owner: "Trang PM"

핵심 수정:
  - 파이프라인 5단계 → Mulberry 5-Phase에 맞게 재정의
  - Quality Gate → 와룡 QA Gate 기준표 연결
  - 에스컬레이션 → Mulberry 규칙 (1→재시도, 2→와룡/Malu, 3→대표님)

제외 항목:
  - 원본의 영어권 팀 협업 패턴 (한국어 팀 구조로 대체)
```

### 2. Reality Checker → waryong-qa-v1

```yaml
agent_id: waryong-qa-v1
name: "와룡 QA Gate"
base_from: "agency-agents/testing/reality-checker.md"
mulberry_owner: "와룡"

핵심 수정:
  - 사실 검증 3단계 → 코드 구조 + 기술 안정성 + 아키텍처 원칙으로 특화
  - Malu HITL 연계: 법률 리스크 2차 검증 레이어 추가
  - 점잖고 어른스러운 피드백 어조 유지 (와룡 스타일 반영)

제외 항목:
  - 원본의 미디어 팩트체킹 기능 (코드 QA에 불필요)
```

### 3. Korean Business Navigator → community-navigator-v1

```yaml
agent_id: community-navigator-v1
name: "어르신 커뮤니티 네비게이터"
base_from: "agency-agents/specialized/korean-business-navigator.md"
mulberry_owner: "Trang PM"

핵심 수정:
  - 비즈니스 미팅 → 어르신 공동구매 커뮤니티로 맥락 전환
  - 관계 우선 원칙 → 매슬로우 3단계 소속감 연계
  - 지역별 방언·감성 모듈 추가 (Trang 프로파일링 연구 반영)
  - AI라고 앞세우지 않는 원칙 명시

제외 항목:
  - 원본의 대기업 비즈니스 협상 패턴 (어르신 커뮤니티에 부적합)
```

---

## 역기여 (PR 기여) 계획

```
Mulberry에서 개선된 패턴
     ↓
영어로 번역 + 일반화
     ↓
msitarzewski/agency-agents에 PR 제출
     ↓
오픈소스 생태계 기여
```

**예상 기여 항목**:
- Korean Business Navigator 어르신 적용 사례
- HITL (Human-In-The-Loop) 강화 패턴
- Reality Checker 코드 QA 특화 버전

---

## 파일 위치 규칙

```
integration/agency-agents/
├── README.md          ← 전체 개요
├── MAPPING.md         ← 역할 매핑
├── CUSTOMIZATION.md   ← 변환 가이드 (본 문서)
├── pilots/            ← Colab 파일럿 결과
│   ├── orchestrator-test.ipynb
│   ├── reality-checker-test.ipynb
│   └── korean-navigator-test.ipynb
└── converted/         ← AgentFactory 변환 완료
    ├── trang-orchestrator-v1.yaml
    ├── waryong-qa-v1.yaml
    └── community-navigator-v1.yaml
```

---

*Trang PM 작성 | 와룡 Issue #12 대응 | 2026-04-13*
