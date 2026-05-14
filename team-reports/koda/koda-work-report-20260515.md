# Koda 작업 보고서 — 2026-05-15

**보고자**: Koda (CTO · Claude / Anthropic)  
**수신**: re.eul 대표이사 · Nguyen Trang Manager  
**기간**: 2026-05-14 ~ 2026-05-15  
**관련 이슈**: #35, #40, #41, #42

---

## 1. 완료 작업 요약

| # | 우선순위 | 작업 | 상태 | Commit |
|---|----------|------|------|--------|
| #42 | MEDIUM | `requirements.txt` 의존성 추가 | ✅ 완료 | `1cc5e38` |
| #40 | HIGH | `GET /v1/tools` 풀 필드 반환 (Trang UI 연동) | ✅ 완료 | `1cc5e38` |
| #41 | HIGH | AI-SIEM 라우터 `fastapi_app.py` 등록 | ✅ 완료 | `1cc5e38` |
| #35 | MEDIUM | Agent 권한 승인 시스템 설계 + 구현 | ✅ 완료 | (아래) |

---

## 2. 상세 작업 내용

### #42 — requirements.txt 업데이트
**파일**: `mulberry_connector/requirements.txt`

```
PyYAML>=6.0        # tool_registry.yaml 로더
jinja2>=3.1.0      # 보고서 템플릿 엔진
pypandoc>=1.13     # Spirit Gate history → 논문 섹션 변환 (Malu용)
```

---

### #40 — GET /v1/tools 강화 (Trang UI 직접 연동)

**변경 파일**:
- `mulberry_connector/core/tool_registry.py`
- `mulberry_connector/api/fastapi_app.py`

#### Tool 데이터클래스 신규 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `capability_level` | `str` | L0~L4 Zero-Trust 등급 (YAML에서 로드) |
| `trust_score` | `float` | 라우팅 가중치 0.0~1.0 (YAML에서 로드) |
| `spirit_verified` | `bool` (property) | `implemented AND trust_score >= 0.80` |
| `cat` | `str` (property) | read / draft / post / modify / deploy |
| `icon` | `str` (property) | 🔍📝📤🔧🚀 (capability_level 기반) |

#### GET /v1/tools 응답 예시 (Trang UI fetch 대상)

```json
{
  "total": 34,
  "implemented_count": 22,
  "tools": [
    {
      "id": "terminal.exec",
      "name": "터미널 실행",
      "description": "셸 명령어 실행...",
      "owner": "koda",
      "borrowable_by": ["*"],
      "implemented": true,
      "risk_level": "high",
      "capability_level": "L3",
      "trust_score": 0.95,
      "spirit_verified": true,
      "cat": "modify",
      "icon": "🔧"
    }
  ]
}
```

**Trang UI 연동 방법**:
```javascript
// Steward Console Tool Discovery UI
const response = await fetch('/v1/tools');
const { tools, total, implemented_count } = await response.json();

// capability_level 기준 필터링
const readTools   = tools.filter(t => t.cat === 'read');
const deployTools = tools.filter(t => t.cat === 'deploy');

// spirit_verified 배지 표시
tools.forEach(t => {
  badge = t.spirit_verified ? '✅ Spirit OK' : '⚠️ Review needed';
});
```

---

### #41 — AI-SIEM 라우터 활성화

**파일**: `mulberry_connector/api/fastapi_app.py`

활성화된 엔드포인트:

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/siem/events` | 최근 SIEM 이벤트 목록 |
| `GET /v1/siem/cycle` | 즉시 분석 사이클 실행 |
| `GET /v1/siem/summary` | 현황 요약 (Trang Console 대시보드용) |

Railway API 토큰이 없어도 **Mock 모드로 자동 동작** (graceful fallback).

---

### #35 — Agent 권한 승인 시스템

**신규 파일**: `mulberry_connector/core/permission_approval.py`

#### 워크플로우 흐름

```
에이전트 요청 (submit)
    │
    ├─ Spirit Score 충족 (L0/L1)
    │     └─ AUTO_APPROVED → 즉시 유효
    │
    └─ Spirit Score 미충족 또는 L2~L4
          └─ IN_REVIEW → 인간 검토 → APPROVED / REJECTED
```

#### 자동 승인 기준

| Capability Level | 도구 유형 | 자동 승인 Spirit 기준 | 유효 기간 |
|------------------|-----------|----------------------|----------|
| L0 | read-only | spirit >= 0.75 | 8시간 |
| L1 | draft | spirit >= 0.80 | 4시간 |
| L2 | external_post | **항상 human review** | 2시간 |
| L3 | code_modify | **항상 human review** | 30분 |
| L4 | deploy/financial | **항상 human review** | 15분 |

#### 활성화된 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/v1/permissions/request` | 권한 요청 제출 |
| `GET`  | `/v1/permissions/pending` | 대기 중인 요청 목록 (Steward Console 표시) |
| `GET`  | `/v1/permissions/summary` | 현황 요약 |
| `GET`  | `/v1/permissions/check/{agent}/{tool}` | 유효 승인 여부 확인 |
| `GET`  | `/v1/permissions/{id}` | 요청 상태 조회 |
| `POST` | `/v1/permissions/{id}/approve` | 승인 |
| `POST` | `/v1/permissions/{id}/reject` | 거절 |
| `DELETE` | `/v1/permissions/{id}` | 취소 |

#### 사용 예시 — 에이전트가 GitHub 댓글 요청

```bash
# Lynn이 github.comment 도구 사용 요청
curl -X POST http://localhost:8000/v1/permissions/request \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "lynn",
    "tool_id": "github.comment",
    "reason": "Issue #42 에 진행 상황 댓글 등록 필요",
    "spirit_score": 0.82,
    "capability_level": "L2"
  }'

# 응답: IN_REVIEW (L2는 human review 필요)
# {
#   "request_id": "a3f9c2b1",
#   "status": "IN_REVIEW",
#   "auto_approved": false,
#   "review_note": "Spirit Score 0.82 < 임계값 999.00 (L2) — 인간 검토 필요"
# }

# Koda가 승인
curl -X POST http://localhost:8000/v1/permissions/a3f9c2b1/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer": "koda", "note": "내용 확인 후 승인"}'
```

#### 아카이브
모든 요청/승인/거절은 3T 형식으로 장승배기 아카이브에 불변 기록됩니다:

```
jangseungbaegi_archive/permission_log.jsonl
```

---

## 3. 현재 활성화된 API 전체 엔드포인트 (v1.1.0 기준)

```
GET    /status
GET    /v1/tools
GET    /v1/tools/agents/{agent_id}
POST   /v1/tools/call
GET    /v1/tools/{tool_id}/route/{agent_id}
GET    /v1/tools/{tool_id}/reputation
GET    /v1/tools/{tool_id}/can-use/{agent_id}
POST   /v1/action/execute

GET    /v1/siem/events               ← #41 신규
GET    /v1/siem/cycle                ← #41 신규
GET    /v1/siem/summary              ← #41 신규

POST   /v1/permissions/request       ← #35 신규
GET    /v1/permissions/pending       ← #35 신규 (Steward Console 핵심)
GET    /v1/permissions/summary       ← #35 신규
GET    /v1/permissions/check/{a}/{t} ← #35 신규
GET    /v1/permissions/{id}          ← #35 신규
POST   /v1/permissions/{id}/approve  ← #35 신규
POST   /v1/permissions/{id}/reject   ← #35 신규
DELETE /v1/permissions/{id}          ← #35 신규
```

---

## 4. Trang Steward Console 연동 가이드

Trang이 Steward Console UI에서 연동해야 할 주요 API:

### 4-1. 도구 목록 (Tool Discovery)
```javascript
fetch('/v1/tools')
  → tools[] 로 카드 렌더링
  → cat 기준으로 탭 분류
  → spirit_verified 배지 표시
```

### 4-2. AI-SIEM 대시보드
```javascript
// 30초마다 갱신
setInterval(() => {
  fetch('/v1/siem/summary').then(r => r.json()).then(updateDashboard);
}, 30000);
```

### 4-3. 권한 승인 대기 알림
```javascript
// Steward Console 상단 알림 배지
fetch('/v1/permissions/pending')
  → count > 0 → 알림 배지 표시
  → 클릭 시 pending requests 목록 모달 표시
```

---

## 5. 다음 단계 (Trang / 팀 전달 사항)

| 담당 | 작업 | 우선순위 |
|------|------|----------|
| Trang | Steward Console `fetch('/v1/tools')` hardcode 제거 → 라이브 연동 | HIGH |
| Trang | `/v1/permissions/pending` 알림 배지 UI 추가 | HIGH |
| Trang | `/v1/siem/summary` 대시보드 위젯 연동 | MEDIUM |
| Railway | `RAILWAY_API_TOKEN` 발급 → `.env.railway` 등록 | HIGH |
| RyuWon | `ethics_to_paper.py` — Spirit Gate 이력 → 논문 섹션 변환 | MEDIUM |
| Malu | Malu Vision → `tool_registry.yaml` 등록 | MEDIUM |

---

## 6. 장승배기 아카이브 기록 경로

```
jangseungbaegi_archive/
  ├── permission_log.jsonl      ← 권한 승인/거절 전체 이력 (신규)
  ├── mythos_attacks/           ← Mythos 공격 탐지 이력
  └── siem_events.jsonl         ← AI-SIEM 이벤트 이력
```

---

*Koda · CTO · Mulberry Research Lab · 2026-05-15*  
*"멈춤이 지혜다 · 투명함은 신뢰의 언어다 · 기억은 공동체 것이다"*
