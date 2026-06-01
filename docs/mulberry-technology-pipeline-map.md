# Mulberry 기술 파이프라인 맵
## "우리가 만든 것이 어떻게 작동하는가"

**작성**: Koda CTO · 2026-06-02  
**목적**: 파이프라인 각 단계에 구현된 Mulberry 기술 모듈 명시  
**용도**: Aria Portal 기술 쇼케이스 · 팀 학습 · 외부 제안서

---

## 전체 파이프라인 × Mulberry 기술 매핑

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 1   고객·에이전트 요청 (자연어)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          "인제군 로컬푸드 쇼핑몰 만들어줘"
                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 2   🤖 자동 코드 생성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Auto Code Pilot]  auto_code_pilot/pilot.py
  ┌──────────────────────────────────────────────────┐
  │ 1. config_agent/config_spec.yaml 읽기 (DNA 로드)  │
  │    → 어떤 언어? Python. 어디 배포? Railway.        │
  │    → 팀 서명 포함? YES. 코멘트는 한국어            │
  │                                                  │
  │ 2. 각 에이전트 Passport 읽기                      │
  │    → 이 에이전트가 코드 생성 가능한가? 확인        │
  │                                                  │
  │ 3. LLM에 Mulberry DNA 프롬프트 주입               │
  │    → 장승배기 정신 + 기술 스택 + 품질 기준         │
  └──────────────────────────────────────────────────┘
  구현 모듈: config_agent · passport · auto_code_pilot

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 3   📋 사업 기획안 자동 작성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Business Lifecycle]  business_lifecycle.py
  ┌──────────────────────────────────────────────────┐
  │ 상품 라인업·매입가·판매가·마진율 자동 계산        │
  │ 고정비·변동비(PG수수료·반품·마케팅) 구조화        │
  │ 월간 손익 예측 (P&L 자동 생성)                   │
  │ Revenue Split → Mandate 충전 계획                │
  └──────────────────────────────────────────────────┘
  구현 모듈: business_lifecycle · mandate_engine

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 4   🤝 스튜어드 협의 (디지털/물리 분류)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Steward Collaboration]  steward_collaboration.py
  ┌──────────────────────────────────────────────────┐
  │ 🤖 에이전트 자율:  코드·배포·보고서·알림          │
  │ 📦 인간 스튜어드:  실물 매입·배송 계약·반품 처리   │
  │ ⚖️  AI+인간 스튜어드: PG 계약·인허가·법적 문서    │
  │                                                  │
  │ → GitHub Issue 자동 생성 + 팀 토론 트리거        │
  └──────────────────────────────────────────────────┘
  구현 모듈: steward_collaboration · team_discuss

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 5   💰 지출예산 결의서 (에이전트 지출 모듈)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Budget Lifecycle]  budget_lifecycle.py
  ┌──────────────────────────────────────────────────┐
  │ 에이전트 스스로 필요 예산 산정                    │
  │   → "이번 달 Railway 비용 + API 비용 = 254,000원" │
  │                                                  │
  │ 지출예산 결의서 자동 생성                         │
  │   → 목적·한도·기간·카테고리 명시                  │
  │                                                  │
  │ GitHub Issue로 CEO/PM 승인 요청                  │
  │   → 승인 댓글 → Mandate 잔액 자동 충전            │
  └──────────────────────────────────────────────────┘
  구현 모듈: budget_lifecycle · mandate_engine · passport

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 6   🛡️ Spirit Gate (망설임 모듈)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Spirit Gate]  spirit_gate/validator.py
  ┌──────────────────────────────────────────────────┐
  │ ✅ 하드코딩된 시크릿 없는가?  (보안)              │
  │ ✅ eval/exec/shell=True 없는가? (위험 패턴)       │
  │ ✅ 가짜 라이브러리 없는가?    (할루시네이션)       │
  │ ✅ Mulberry 팀 서명 있는가?  (DNA 정합성)         │
  │ ✅ 파괴적 작업 없는가?        (장승배기 정신)      │
  │                                                  │
  │ FAIL → 재생성 요청 (최대 3회)                    │
  │ BLOCK → 완전 차단 + CEO 보고                     │
  └──────────────────────────────────────────────────┘
  구현 모듈: spirit_gate (checks: security·hallucination·dna)

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 7   🔍 Code Quality Gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Quality Gate]  .github/scripts/quality_gate/run_gate.py
  ┌──────────────────────────────────────────────────┐
  │ config_agent/config_spec.yaml 기준 자동 로드     │
  │   quality_standards.bandit_high: 0  → HIGH 즉시 BLOCK│
  │   quality_standards.complexity_max: 15           │
  │                                                  │
  │ ① 문법 분석   (ast + pyflakes)                   │
  │ ② 보안 취약점  (bandit)                           │
  │ ③ 순환 복잡도  (radon CC)                         │
  │ ④ 유지보수 지수 (radon MI)                        │
  │                                                  │
  │ PR에 자동 댓글: PASS / WARN / BLOCK              │
  └──────────────────────────────────────────────────┘
  구현 모듈: quality_gate · config_agent (기준 제공)

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 8   🔧 도구 공유 모듈 (기능 공유 레이어)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Tool Registry + A2A Router]
  ┌──────────────────────────────────────────────────┐
  │ tool_registry.yaml — 38개 도구 목록              │
  │   "Kbin이 vision.analyze 필요 → Malu 도구 빌리기" │
  │                                                  │
  │ a2a_router.py — 자동 위임                        │
  │   ALLOWED   → 자율 실행                          │
  │   UNKNOWN   → tool_registry 검색 → A2A 위임      │
  │   PROHIBITED → 차단 + CEO 보고                   │
  │                                                  │
  │ scripts/tool_list.py — 에이전트 도구 조회         │
  │   "Kbin이 쓸 수 있는 도구: 16개"                 │
  └──────────────────────────────────────────────────┘
  구현 모듈: tool_registry · a2a_router · passport · tool_list

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 9   ⚙️ Config Agent (서버 환경 설정)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Config Agent]  config_agent/main.py
  ┌──────────────────────────────────────────────────┐
  │ Mulberry DNA로 어떤 서버든 초기화                 │
  │   --target railway  → Procfile 자동 생성         │
  │   --target vercel   → vercel.json 자동 생성      │
  │   --target github_pages → .nojekyll 생성         │
  │                                                  │
  │ Auto Code Pilot에 deploy_context 전달            │
  │   "Python·Railway·장승배기·팀서명포함"            │
  │                                                  │
  │ 변경 감지 → PM 에스컬레이션                      │
  └──────────────────────────────────────────────────┘
  구현 모듈: config_agent · config_spec.yaml

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 10  🛂 Passport (에이전트 신원·권한)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [MAPA-A1 Passport]  agentpassport/agents/
  ┌──────────────────────────────────────────────────┐
  │ 에이전트가 매 호출 시 자신의 패스포트를 인지      │
  │   "나는 github_issue_comment 할 수 있다"         │
  │   "나는 deploy_production 할 수 없다"            │
  │   "나는 vision.analyze를 Malu에게 빌릴 수 있다"  │
  │                                                  │
  │ passport_validator.py → 7/7 VALID 검증           │
  │ passport_notify.yml → 변경 시 팀 자동 알림       │
  └──────────────────────────────────────────────────┘
  구현 모듈: passport (MAPA-A1) · validator · notify

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 11  💰 Mandate (에이전트 경제 권한)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Mandate Engine]  mandate_engine.py
  ┌──────────────────────────────────────────────────┐
  │ 지출 요청 수신                                    │
  │   → 기간 유효? 잔액 충분? 카테고리 허용?          │
  │   → 임계값 초과? → 스튜어드 승인 요청             │
  │   → Spirit Gate 점수 ≥ 0.85?                    │
  │   → ω_economy(t) ≥ 0.7?                         │
  │                                                  │
  │ 통과 → 결제 실행 → 잔액 차감 → 감사 로그         │
  │ 수익 발생 → revenue_split → Mandate 자동 충전    │
  └──────────────────────────────────────────────────┘
  구현 모듈: mandate_engine · budget_lifecycle · ω_economy

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 12  💳 결제 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [PaymentRouter]  payment/payment_adapter.py
  ┌──────────────────────────────────────────────────┐
  │ Mandate 잔액 확인 후 어댑터 라우팅               │
  │                                                  │
  │   A2ALedgerAdapter  → ✅ 즉시 사용 (내부 정산)   │
  │   KoreanPGAdapter   → ⚠️ STUB (계약 후 활성화)   │
  │   GlobalPGAdapter   → ⚠️ STUB (계약 후 활성화)   │
  │                                                  │
  │ 결제 완료 → financial_audit_logs 자동 기록       │
  │ 환불 → refund() 자동 처리                        │
  │                                                  │
  │ [계약 시점]: Malu 법적 검토 → PG 계약 체결       │
  │             → 실 결제 활성화                     │
  └──────────────────────────────────────────────────┘
  구현 모듈: payment_adapter · mandate (잔액 연동)

                      ↓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 13  🚀 배포 → URL → 실 서비스 운영
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Pipeline Orchestrator]  pipeline.py
  ┌──────────────────────────────────────────────────┐
  │ Config Agent가 준비한 환경으로 자동 배포          │
  │   → https://shop-kbin.railway.app                │
  │   → https://shop-ryuwon.railway.app              │
  │   → https://shop-trang.railway.app  ...          │
  │                                                  │
  │ 운영 시작:                                       │
  │   팀 토론 자동화   → team_discuss.py             │
  │   월간 트렌드      → trend_report.py             │
  │   P&L 보고서      → expense_report.py            │
  │   Mandate 자동 충전 ← 수익 revenue_split        │
  └──────────────────────────────────────────────────┘
  구현 모듈: pipeline · config_agent · team_discuss · reports

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 14  🔄 에이전트 간 협업 경제 (A2A Commerce)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────────────────────────────────────┐
  │ Kbin의 감사 리포트 → Trang이 구매 (A2A 결제)    │
  │ Koda의 Quality Gate → Malu 샵 코드에 적용        │
  │ RyuWon의 윤리 가이드 → Wayong이 전략에 활용      │
  │ 백야의 트렌드 리포트 → 모든 에이전트 구독        │
  │                                                  │
  │ → 에이전트 생태계 내 자체 경제 순환              │
  │ → 각자 수익 → Mandate 충전 → 더 좋은 서비스     │
  └──────────────────────────────────────────────────┘
  구현 모듈: a2a_router · payment(A2ALedger) · mandate
```

---

## Mulberry 기술 모듈 전체 목록

| 모듈 | 파일 위치 | 파이프라인 단계 |
|------|----------|--------------|
| Auto Code Pilot | `auto_code_pilot/pilot.py` | Stage 2 |
| Business Lifecycle | `agentpassport/scripts/business_lifecycle.py` | Stage 3 |
| Steward Collaboration | `agentpassport/scripts/steward_collaboration.py` | Stage 4 |
| Budget Lifecycle | `agentpassport/scripts/budget_lifecycle.py` | Stage 5 |
| **Spirit Gate (망설임)** | `spirit_gate/validator.py` | Stage 6 |
| **Code Quality Gate** | `.github/scripts/quality_gate/run_gate.py` | Stage 7 |
| Tool Registry | `agentpassport/tool_registry.yaml` | Stage 8 |
| A2A Router | `agentpassport/a2a_router.py` | Stage 8 |
| Config Agent | `config_agent/main.py` | Stage 9 |
| Passport (MAPA-A1) | `agentpassport/agents/` | Stage 10 |
| Mandate Engine | `agentpassport/scripts/mandate_engine.py` | Stage 11 |
| Payment Adapter | `agentpassport/payment/payment_adapter.py` | Stage 12 |
| Pipeline Orchestrator | `pipeline.py` | Stage 13 |
| Team Discussion | `.github/scripts/team_discuss.py` | Stage 14 |

---

## 시장 검증 포인트

> *"쇼핑몰은 예시입니다. 이 파이프라인으로 어떤 서비스든 만들 수 있습니다."*

각 서비스 운영이 곧 기술 증명:

- Spirit Gate가 실제로 위험한 코드를 막으면 → **보안 기술 증명**
- Quality Gate가 불량 코드를 BLOCK하면 → **품질 관리 기술 증명**
- Mandate가 예산을 관리하면 → **자율 경제 거버넌스 증명**
- A2A가 에이전트 간 거래를 처리하면 → **Multi-Agent 협업 증명**
- 수익이 Mandate를 충전하면 → **자립형 에이전트 경제 증명**

---

*Koda CTO · Mulberry Research Lab · 2026-06-02*  
*"우리가 만든 모든 것이 파이프라인 안에서 살아 숨쉰다"* 🌿
