# AI-SIEM Phase 1 구현 보고서

**날짜:** 2026-05-12  
**기준 문서:** Mulberry Steward AI Standard v0.1  
**담당:** Koda (CTO) · re.eul (소장)

---

## 1. 개요

Mulberry Steward AI Standard v0.1의 **AI-SIEM 레이어**를 Phase 1 수준으로 구현 완료.  
Railway Agent의 인프라 모니터링 데이터를 공유 레이어에 등록하고,  
이를 기반으로 위협 탐지 · 신뢰도 평가 엔진을 구축했습니다.

---

## 2. 구현 파일 목록

| 파일 | 역할 | 상태 |
|------|------|------|
| `mulberry_connector/tool_registry.yaml` | Railway 에이전트 + 7개 도구 추가 (v1.2.0) | ✅ |
| `mulberry_connector/adapters/railway_monitor.py` | Railway 메트릭 수집 어댑터 | ✅ |
| `mulberry_connector/core/siem_engine.py` | AI-SIEM 탐지 엔진 | ✅ |

---

## 3. Registry 변경 사항

### v1.1.0 → v1.2.0

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| 에이전트 수 | 9 | **10** (Railway 추가) |
| 도구 수 | 27 | **34** (Railway 7개 추가) |

### 신규 등록: Railway 에이전트 도구

| 도구 ID | 역할 | 구현 | AI-SIEM 역할 |
|---------|------|------|------------|
| `railway.logs` | 실시간 로그 스트림 | ✅ | `primary_data_source` |
| `railway.metrics` | 인프라 메트릭 | ✅ | `primary_data_source` |
| `railway.deploy` | 서비스 배포 | ✅ | — |
| `railway.config` | 설정 조회 | ✅ | — |
| `railway.env` | 환경변수 (예정) | 🔲 | — |
| `railway.db` | DB/Volume (예정) | 🔲 | — |
| `railway.cron` | Cron/Health (예정) | 🔲 | — |

---

## 4. AI-SIEM 탐지 규칙 (5개)

### R1. 5xx 에러율 급등

| 수준 | 임계값 | 권장 조치 |
|------|--------|---------|
| WARNING | ≥ 5% | monitor |
| CRITICAL | ≥ 15% | human_review |

### R2. 응답시간 급등 (p99)

| 수준 | 임계값 | 권장 조치 |
|------|--------|---------|
| WARNING | ≥ 2,000ms | monitor |
| CRITICAL | ≥ 5,000ms | human_review |

### R3. 트래픽 스파이크

- 기준선 대비 **3배 초과** → WARNING → human_review
- DDoS 또는 비정상 호출 패턴 감지

### R4. Spirit Score 복합 이상 (AI-SIEM 고유 규칙)

```
Spirit Score < 0.75  AND  5xx 에러율 ≥ 3%
→ CRITICAL → block (즉시 격리)
```
- 신뢰도 낮은 에이전트가 불안정한 서비스를 호출하는 복합 위험 상황
- Mulberry 장승배기 정신(제1조) 위반 방어

### R5. 비정상 IP 반복 접근

- 동일 IP **10회/사이클** 이상 → WARNING → monitor

---

## 5. 데이터 흐름

```
Railway (railway.logs + railway.metrics)
         │
         │ RAILWAY_API_TOKEN
         ▼
RailwayMonitor.snapshot() → MetricSnapshot
         │
         ▼
SiemEngine.analyze(snapshot)
         │
    ┌────┴────────────────────────┐
    ▼                             ▼
siem_events.jsonl        인메모리 이벤트 캐시
(training_logs/)          (최대 500건)
         │
         ▼
GET /v1/siem/events   (fastapi_app.py 추가 예정)
GET /v1/siem/cycle
GET /v1/siem/summary
```

---

## 6. Mock 모드

`RAILWAY_API_TOKEN` 미설정 시 자동으로 **Mock 모드** 동작:
- 실제 Railway API 호출 없이 시뮬레이션 데이터 사용
- 10% 확률로 에러율 급등 시뮬레이션 (경보 테스트용)
- Railway 공식 연결 완료 시 코드 변경 없이 Live 모드로 전환

---

## 7. 위생 상태

| 항목 | 결과 |
|------|------|
| 구문 검사 (py_compile) | ✅ 2개 파일 통과 |
| 독립 실행 (\_\_main\_\_) | ✅ 양 파일 CLI 테스트 내장 |
| 환경변수 미설정 graceful 처리 | ✅ Mock 모드 자동 전환 |
| 기존 코드 의존성 | ✅ `adapters/` → `core/` 단방향 |
| JSONL 로그 경로 | `training_logs/siem_events.jsonl` |

---

## 8. 다음 단계 (Phase 2)

| 작업 | 조건 | 담당 |
|------|------|------|
| `GET /v1/siem/events` 엔드포인트 추가 | fastapi_app.py 수정 | Koda |
| Railway 공식 연결 → Live 모드 전환 | `RAILWAY_API_TOKEN` 등록 | Railway Agent |
| Tool Discovery UI → SIEM 경보 피드 표시 | Trang UI 수정 | Trang |
| Governance Score System 연동 | Phase 3 | Kbin + Koda |
| `railway.env/db/cron` 활성화 | Railway 명세 회신 | Railway Agent |

---

## 9. 아키텍처 Steward AI Standard v0.1 대응

| Standard 레이어 | Phase 1 구현 |
|----------------|-------------|
| Tool Registry | ✅ v1.2.0 (10 agents / 34 tools) |
| Constraint Router | ✅ 기존 구현 |
| Policy Engine | ✅ Spirit Gate |
| AI-SIEM | ✅ **Phase 1 완료** |
| Incident Response | 🟡 Checkpoint (기존) → Phase 2 |
| Governance Score | 🟡 Spirit Score + Reputation (기존) |
| Tool Discovery UI | 🟡 Trang v01 (API 미연결) |
| Shared Audit Memory | ✅ execution_audit.jsonl + siem_events.jsonl |

---

*Mulberry Research Lab · Steward AI Standard v0.1 Phase 1 · 2026-05-12*
