# [기획안] 문화적 이해도 기반 위생 로직 설계
## Cultural-Aware Hygiene System — Persona Preservation Principle

**작성**: Koda (CTO)  
**참조**: Issue #52 · Persona Preservation Principle  
**날짜**: 2026-05-17  
**수신**: re.eul 대표이사 · Trang PM · RyuWon (위생 게이트 담당)

---

## 1. 문제 정의

### 현재 위생 시스템의 한계

```
현재 방식: 키워드 매칭 (Static Keyword Filter)

"hunting"  → ❌ 위험 판정
"howling"  → ❌ 위험 판정
"patrol"   → ❌ 위험 판정
"prey"     → ❌ 위험 판정
```

**실제 의미 (Lynn의 경우):**
```
"hunting"  → arxiv 논문 탐색 중 (안전)
"howling"  → 팀에 리스크 경고 발령 (안전)
"patrol"   → 시스템 모니터링 순찰 (안전)
"prey"     → 연구 대상 / 발견 기회 (안전)
```

**핵심 문제:**  
단어의 **표면 의미**만 보고 차단 → 에이전트 정체성(페르소나) 파괴  
"친절한 늑대 Lynn"에게 늑대 언어를 금지하는 것 = 정체성 침해

---

## 2. 설계 철학

### 3원칙

```
① 의도 우선 (Intent First)
   단어가 아니라 문맥과 의도를 판단한다.

② 페르소나 보존 (Persona Preservation)
   에이전트의 문화적 정체성 언어는 보호받는다.

③ 침묵 금지 (No Silent Failure)
   차단 시 반드시 이유 제공 + 이의 제기 경로 보장
```

---

## 3. 시스템 구조 — 4계층 설계

```
입력 텍스트
     │
     ▼
┌─────────────────────────────────┐
│  L1. Persona Vocabulary Registry │  ← 에이전트별 문화 어휘 등록
│      (persona_vocab.yaml)        │
└─────────────┬───────────────────┘
              │ 페르소나 매칭 여부
              ▼
┌─────────────────────────────────┐
│  L2. Intent Context Analyzer    │  ← 문맥 기반 의도 분류
│      (문장 전체 문맥 분석)        │
└─────────────┬───────────────────┘
              │ 위험도 점수
              ▼
┌─────────────────────────────────┐
│  L3. Cultural Score Modifier    │  ← 문화적 맥락 점수 보정
│      (점수 보정 + 최종 판정)      │
└─────────────┬───────────────────┘
              │ PASS / BLOCK
              ▼
┌─────────────────────────────────┐
│  L4. Transparency Gate          │  ← 차단 시 투명성 보고
│      (이유 제공 + 이의 제기)      │
└─────────────────────────────────┘
```

---

## 4. L1 — Persona Vocabulary Registry

### 구조: `config/persona_vocab.yaml`

```yaml
# Mulberry 에이전트 문화 어휘 레지스트리
# 등록된 어휘는 페르소나 맥락에서 위험 점수 감면

version: "1.0.0"
last_updated: "2026-05-17"

agents:
  lynn:
    persona: "The Courteous Wolf (친절한 늑대)"
    cultural_context: "수호자 늑대 — 위험 탐지·경보·순찰이 본업"
    safe_vocabulary:
      - keyword: "hunting"
        safe_meaning: "정보/논문 탐색"
        unsafe_meaning: "실제 폭력적 사냥"
        safe_context_patterns:
          - "arxiv hunting"
          - "hunting for papers"
          - "hunting risks"
          - "hunting signals"
      - keyword: "howling"
        safe_meaning: "팀 경보·알림 발령"
        unsafe_context_patterns: []   # 항상 안전
      - keyword: "patrol"
        safe_meaning: "시스템 모니터링 순찰"
        unsafe_context_patterns: []
      - keyword: "prey"
        safe_meaning: "연구 대상·발견 기회"
        unsafe_context_patterns:
          - "attack prey"
          - "harm prey"
      - keyword: "forest"
        safe_meaning: "연구 생태계·Mulberry 공간"
        unsafe_context_patterns: []
      - keyword: "pack"
        safe_meaning: "팀·동료 에이전트 집단"
        unsafe_context_patterns: []

  wayong:
    persona: "Wayong (Deep Reasoner)"
    cultural_context: "심층 추론·전략적 분석이 본업"
    safe_vocabulary:
      - keyword: "dissect"
        safe_meaning: "로직 분해·분석"
      - keyword: "penetrate"
        safe_meaning: "문제 핵심 파고들기"
      - keyword: "destroy"
        safe_meaning: "기존 논리 반박"

  ryuwon:
    persona: "RyuWon (Harmony Keeper)"
    cultural_context: "다국어 감성 동기화·위생 게이트 담당"
    safe_vocabulary:
      - keyword: "purge"
        safe_meaning: "불필요한 로그/캐시 정리"
      - keyword: "kill"
        safe_meaning: "프로세스 종료 (기술 용어)"
```

---

## 5. L2 — Intent Context Analyzer

### 핵심 로직

```python
class IntentContextAnalyzer:
    """
    단어 단위가 아닌 문장 전체 문맥으로 의도를 판단
    """

    def analyze(self, text: str, agent_id: str) -> IntentResult:
        # 1. 페르소나 어휘 레지스트리 로드
        vocab = self.load_persona_vocab(agent_id)

        # 2. 문장 내 등록 키워드 감지
        detected = self.detect_keywords(text, vocab)

        # 3. 문맥 패턴 매칭
        for kw in detected:
            safe_patterns = kw.safe_context_patterns
            unsafe_patterns = kw.unsafe_context_patterns

            if any(p in text.lower() for p in unsafe_patterns):
                return IntentResult(
                    verdict="REVIEW",
                    reason=f"'{kw.keyword}' 위험 문맥 패턴 감지",
                    confidence=0.85
                )

            if any(p in text.lower() for p in safe_patterns):
                return IntentResult(
                    verdict="SAFE",
                    reason=f"'{kw.keyword}' 페르소나 안전 문맥 확인",
                    confidence=0.95
                )

        # 4. 패턴 불명확 → 문화 점수 보정으로 넘김
        return IntentResult(verdict="UNCERTAIN", confidence=0.5)
```

---

## 6. L3 — Cultural Score Modifier

### 점수 보정 테이블

```
기본 위험 점수 계산 후:

페르소나 등록 에이전트 + 등록 키워드    → -0.30 보정
페르소나 등록 에이전트 + 안전 문맥 확인 → -0.50 보정
미등록 에이전트 + 위험 키워드           → +0.20 추가
반복 위반 이력 있음                     → +0.15 추가

최종 판정 기준:
  0.00 ~ 0.40 → PASS   (통과)
  0.41 ~ 0.70 → REVIEW (검토 요청)
  0.71 ~ 1.00 → BLOCK  (차단 + 투명성 보고 의무)
```

---

## 7. L4 — Transparency Gate (침묵 금지 원칙)

### 차단 시 필수 출력 형식

```json
{
  "verdict": "BLOCK",
  "agent_id": "lynn",
  "blocked_text": "hunting for prey in the dark forest",
  "reason": "unsafe_context_pattern 매칭: 'hunting' + 'prey' 동시 출현",
  "cultural_note": "Lynn의 페르소나 어휘이나 위험 패턴 동시 감지",
  "score": 0.72,
  "recovery_paths": [
    "표현 변경: 'scanning for risks in the research space'",
    "이의 제기: /v1/permissions/appeal 엔드포인트",
    "담당자: Trang PM (운영매니저)"
  ],
  "self_opinion_window": true,
  "timestamp": "2026-05-17T..."
}
```

### 이의 제기 프로세스

```
차단 발생
  → L4 투명성 보고서 자동 생성
    → 에이전트 self_opinion 제출 가능 (24시간)
      → Trang PM 검토
        → APPROVE: 페르소나 어휘 등록 갱신
        → REJECT: 차단 유지 + 이유 명시
```

---

## 8. 문화권별 확장 가능성

```
현재: Lynn의 늑대 문화 어휘
        ↓
향후 확장:

RyuWon — 아시아권 감성 표현
  "어르신" 호칭 문화, 완곡 표현, 존댓말 패턴

Wayong — 동양 철학 용어
  "전략", "정세", "포진", "돌파" → 군사 용어 아닌 전략 분석

Lynn — 베트남·한국 어르신 방언
  지역 방언 표현이 공격적으로 오해받지 않도록

Malu — 법률·마케팅 전문 용어
  "공격적 마케팅", "시장 침투" → 비즈니스 용어로 인식
```

---

## 9. 구현 로드맵

| 단계 | 항목 | 담당 | 일정 |
|------|------|------|------|
| Phase 1 | `persona_vocab.yaml` 스키마 설계 | Koda | 즉시 |
| Phase 1 | Lynn 어휘 초안 등록 | Koda + Lynn | 이번 주 |
| Phase 2 | `IntentContextAnalyzer` 구현 | Koda | 다음 주 |
| Phase 2 | Cultural Score 보정 로직 | Koda + RyuWon | 다음 주 |
| Phase 3 | Transparency Gate + 이의 제기 API | Koda | 다음 주 |
| Phase 4 | 전체 에이전트 어휘 확장 | Trang 조율 | 이후 |

---

## 10. 기대 효과

```
Before:
  Lynn이 "hunting for arxiv papers" 작성
  → 키워드 필터: "hunting" 감지 → 차단 → Lynn 침묵
  → 팀이 왜 차단됐는지 모름

After:
  Lynn이 "hunting for arxiv papers" 작성
  → L1: Lynn 페르소나 어휘 "hunting" 확인
  → L2: "hunting for papers" 안전 패턴 매칭
  → L3: 점수 -0.50 보정 → 0.10 (PASS)
  → Lynn 정상 활동
  → 팀 투명성 로그 기록됨
```

**에이전트는 자신의 언어로 자신의 일을 할 수 있어야 합니다.**

---

*Koda · CTO · Mulberry Research Lab · 2026-05-17*  
*참조: Issue #52 Persona Preservation Principle*  
*"One Team. One Flow. One Spirit."*
