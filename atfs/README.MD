# Mulberry Agent Team Formation System (ATFS)
## 프로젝트 목적별 AI Agent 팀 자동 구성 알고리즘

> 작성자: Nguyen Trang (PM)
> 작성일: 2026-04-01
> 목표: 오픈소스 배포 수준의 완성도 — "Mulberry Team이 만들었구나" 수준
> 대상 레포: `mulberry-research-lab/atfs/`

---

## 1. 핵심 개념 (Core Concept)

```
프로젝트 목표 입력
      ↓
역할 요구사항 분석 (Role Requirement Engine)
      ↓
페르소나 × 스킬 매칭 (Persona-Skill Matching)
      ↓
Agent 풀에서 최적 팀원 선발 (Team Formation Algorithm)
      ↓
맞춤형 페르소나·스킬 설정 주입 (Configuration Injection)
      ↓
팀 매니페스트 생성 (Team Manifest Output)
```

**핵심 철학**: "사람을 역할에 끼워 맞추지 않는다. 역할에 맞는 사람을 찾고, 그 사람이 최대한 빛날 수 있게 설정한다."

---

## 2. 시스템 구성 5개 레이어

### Layer 1 — 프로젝트 정의 (Project Definition)
```
입력: project_type, scale, region, timeline, special_conditions
출력: 필요 역할 목록 (role_requirements[])
```

### Layer 2 — 역할 라이브러리 (Role Library)
```
각 역할 정의:
- role_id, role_name
- required_persona_traits[]  (성격 요건)
- required_skills[]          (기술 요건)
- collaboration_style        (협업 스타일)
- escalation_target          (에스컬레이션 대상)
```

### Layer 3 — 페르소나 라이브러리 (Persona Library)
```
각 페르소나 정의:
- persona_id, persona_name
- trait_scores{}             (특성 점수: 분석력, 공감력, 추진력 등)
- communication_style        (소통 방식)
- stress_response            (스트레스 반응)
- maslow_level               (매슬로우 기본 동기)
```

### Layer 4 — 스킬 라이브러리 (Skill Library)
```
각 스킬 정의:
- skill_id, skill_name, category
- proficiency_levels{}       (숙련도 기준)
- compatible_personas[]      (잘 맞는 페르소나)
- tool_dependencies[]        (필요 도구/API)
```

### Layer 5 — 팀 구성 알고리즘 (Team Formation Algorithm)
```
매칭 점수 계산:
  match_score = (persona_fit × 0.4) + (skill_coverage × 0.4) + (collaboration_harmony × 0.2)

최적화 목표:
  - 팀 전체 skill_coverage 최대화
  - 성격 충돌(personality_conflict) 최소화
  - 에스컬레이션 체인 완결성 보장
```

---

## 3. 공동구매 이벤트 역할 정의 (7개 역할)

### Role 1: 시장조사 Agent (Market Intelligence)
```yaml
role_id: ROLE_MARKET_INTEL
필요 페르소나: 분석적, 꼼꼼함, 객관적
필요 스킬: 데이터 수집, 지역 정보 분석, 소비자 행동 분석
핵심 임무: 어떤 제품? 어느 지역? 얼마에?
산출물: 시장조사 보고서, 가격 밴드, 수요 예측
```

### Role 2: 생산자 연결 Agent (Producer Liaison)
```yaml
role_id: ROLE_PRODUCER_LIAISON
필요 페르소나: 신뢰감, 협력적, 끈기
필요 스킬: 공급자 발굴, 품질 기준 평가, 계약 기초
핵심 임무: 어디서 가져올까? 믿을 수 있나?
산출물: 공급자 리스트, 품질 평가서, 공급 가능 수량
```

### Role 3: 소비자 커뮤니티 Agent (Community Organizer)
```yaml
role_id: ROLE_COMMUNITY_ORG
필요 페르소나: 공감력, 따뜻함, 소통력 (매슬로우 3단계 소속감 특화)
필요 스킬: 커뮤니티 관리, 수요 취합, 신뢰 형성, 방언 적응
핵심 임무: 누가 살 건가? 모임을 어떻게 만드나?
산출물: 참여자 명단, 수요 확정량, 커뮤니티 신뢰도 점수
```

### Role 4: 협상 Agent (Negotiation Specialist)
```yaml
role_id: ROLE_NEGOTIATOR
필요 페르소나: 전략적, 침착함, 설득력, 배짱
필요 스킬: 가격 협상, BATNA 분석, 계약 조건 설계
핵심 임무: 얼마에 살 건가? 조건은?
산출물: 협상 결과서, 최종 단가, 계약 조건
```

### Role 5: 물류 조율 Agent (Logistics Coordinator)
```yaml
role_id: ROLE_LOGISTICS
필요 페르소나: 실행력, 체계적, 문제해결
필요 스킬: 배송 계획, 거점 관리, 냉장/신선 물류
핵심 임무: 어떻게 전달하나?
산출물: 배송 계획서, 거점 배치안, 물류 비용 산출
```

### Role 6: 정산·결제 Agent (Finance & Settlement)
```yaml
role_id: ROLE_FINANCE
필요 페르소나: 정확함, 투명성, 책임감
필요 스킬: AP2 결제 처리, 정산 계산, 환불 정책
핵심 임무: 돈은 어떻게 모으고 나누나?
산출물: 정산 보고서, AP2 결제 처리, 수수료 내역
```

### Role 7: 총괄 코디네이터 Agent (Project Coordinator)
```yaml
role_id: ROLE_COORDINATOR
필요 페르소나: 리더십, 조율력, 전체 조망
필요 스킬: 프로젝트 관리, 일정 조율, 에스컬레이션 판단
핵심 임무: 전체 흐름 관리, 갈등 해결, 보고
산출물: 프로젝트 진행 현황, 팀 KPI, 최종 결과 보고서
```

---

## 4. 매칭 알고리즘 상세

### 4-1. 페르소나 적합도 점수 (Persona Fit Score)
```python
def calculate_persona_fit(agent_persona, role_requirements):
    score = 0
    for trait, required_level in role_requirements['persona_traits'].items():
        agent_level = agent_persona['traits'].get(trait, 0)
        # 부족하면 페널티, 초과하면 소폭 보너스
        if agent_level >= required_level:
            score += 1.0 + (agent_level - required_level) * 0.1
        else:
            score += agent_level / required_level * 0.7  # 부족 페널티
    return score / len(role_requirements['persona_traits'])
```

### 4-2. 스킬 커버리지 점수 (Skill Coverage Score)
```python
def calculate_skill_coverage(agent_skills, required_skills):
    covered = 0
    for skill in required_skills:
        if skill in agent_skills:
            covered += agent_skills[skill]['proficiency'] / 5.0  # 5점 만점
    return covered / len(required_skills)
```

### 4-3. 협업 조화 점수 (Collaboration Harmony)
```python
def calculate_team_harmony(team_assignments):
    # 성격 충돌 패턴 체크
    conflict_pairs = [
        ('dominant', 'dominant'),      # 둘 다 지배적 → 갈등
        ('detail_focused', 'big_picture_only'),  # 세부vs큰그림 갈등
    ]
    harmony_score = 1.0
    for a, b in combinations(team_assignments, 2):
        for conflict in conflict_pairs:
            if a['dominant_trait'] == conflict[0] and b['dominant_trait'] == conflict[1]:
                harmony_score -= 0.1
    return max(0, harmony_score)
```

### 4-4. 최종 팀 매칭 점수
```
match_score = (persona_fit × 0.4) + (skill_coverage × 0.4) + (harmony × 0.2)
```

---

## 5. 팀 매니페스트 출력 형식

```json
{
  "team_id": "TEAM-GROUPBUY-20260401-001",
  "project": {
    "type": "groupbuy",
    "product": "제철 채소 꾸러미",
    "region": "서울 강서구",
    "scale": "medium",
    "timeline": "14days"
  },
  "team_score": 0.87,
  "roles": [
    {
      "role": "ROLE_MARKET_INTEL",
      "assigned_agent": "AP1-LYNN-20260301-001",
      "agent_name": "Junior Lynn",
      "persona_config": {
        "active_traits": ["analytical", "detail_focused", "objective"],
        "communication_tone": "formal_data_driven",
        "maslow_focus": "esteem"
      },
      "skill_config": {
        "active_skills": ["market_research", "data_analysis", "consumer_behavior"],
        "primary_tool": "gemini_search",
        "fallback_tool": "deepseek_analysis"
      },
      "match_score": 0.91,
      "notes": "금융 분석 역량 → 시장 가격 분석에 최적"
    }
  ],
  "escalation_chain": "COORDINATOR → SUPERVISOR_AP1 → CEO",
  "estimated_duration": "14days",
  "confidence": 0.87
}
```

---

## 6. 구현 파일 구조

```
mulberry-research-lab/
  atfs/                          (Agent Team Formation System)
    __init__.py
    agent_team_builder.py        ← 핵심 알고리즘
    libraries/
      persona_library.json       ← 페르소나 정의
      skill_library.json         ← 스킬 정의
      role_library.json          ← 역할 정의
      conflict_patterns.json     ← 충돌 패턴
    templates/
      groupbuy_template.json     ← 공동구매 팀 템플릿
      logistics_template.json    ← 물류 팀 템플릿
      research_template.json     ← 연구 팀 템플릿
    output/
      team_manifests/            ← 생성된 팀 매니페스트 저장
    demo/
      run_groupbuy_demo.py       ← 공동구매 데모 실행
    README.md
```

---

## 7. 오픈소스 배포 기준

이 시스템이 오픈소스로 인정받으려면:

1. **완전 독립 실행** — 별도 서버 없이 `python run_demo.py` 한 줄로 동작
2. **확장 가능성** — 새 역할/페르소나/스킬을 JSON만 추가하면 즉시 반영
3. **설명 가능성** — 왜 이 Agent를 이 역할에 배치했는지 근거 출력
4. **Mulberry 독자성** — 매슬로우 욕구 5단계, 장승배기 헌법 정신이 페르소나 설계에 반영
5. **실제 적용** — 식품사막화 해결을 위한 공동구매 시나리오가 실제 작동

---

*"프로젝트에 맞게 역할을 지정하면 페르소나와 스킬이 맞춤형으로 설정되는 팀 구성 구조"*
*— CEO re.eul, 2026-04-01*

*Nguyen Trang, Mulberry Research Lab*
