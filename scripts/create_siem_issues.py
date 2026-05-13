"""
Mulberry Steward AI — GitHub 이슈 자동 생성
- Issue A: [Steward Console] Tool Discovery UI → Control Dashboard
- Issue B: [AI-SIEM] Phase 2 — Railway Live 연결 + Gateway 엔드포인트
"""
import urllib.request
import urllib.error
import json
import os
import sys

REPO = "wooriapt79/mulberry-research-lab"
token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("GITHUB_TOKEN 없음"); sys.exit(1)

ISSUES = [
    {
        "title": "[Steward Console] Tool Discovery UI → Control & AI-SIEM Dashboard",
        "body": """## 개요
Trang의 `mulberry_tool_discovery_ui_v01.html` (33개 도구, 하드코딩)을
**라이브 API 연동 + 관리자 제어판 + AI-SIEM 경보 피드**로 발전시킨다.

관련: Mulberry Steward AI Standard v0.1 · `research/steward_ai_siem/phase1_implementation_report.md`

---

## 배경
- Phase 1 완료: `railway_monitor.py` + `siem_engine.py` + Registry v1.2.0 (10 agents / 34 tools)
- 현재 UI는 hardcoded `tools[]` 배열 사용 → API 미연결
- Wayong(Steward Console MVP 제안) + Railway Agent(AI-SIEM 데이터 소스) 합의 완료

---

## 작업 목록

### Phase 1 — API 연동 (우선순위 HIGH)
- [ ] `GET /v1/tools` 엔드포인트 → `tool_registry.yaml` 실시간 제공
- [ ] Trang UI `tools[]` 하드코딩 → `fetch("/v1/tools")` 교체
- [ ] 소유자 필터 추가 (Railway, Trang, Koda, Malu 등)
- [ ] 구현 상태 필터 추가 (implemented / planned)

### Phase 2 — AI-SIEM 경보 피드 위젯
- [ ] `GET /v1/siem/events` → UI 하단 실시간 경보 카드 표시
- [ ] 심각도별 색상 (🚨 CRITICAL / ⚠️ WARNING / ✅ OK)
- [ ] `GET /v1/siem/summary` → 오늘 이벤트 통계 배지

### Phase 3 — Steward Console 관리자 기능
- [ ] 도구 활성화/비활성화 토글 (스튜어드 권한)
- [ ] `POST /v1/admin/tools` 도구 등록 신청 폼
- [ ] `PATCH /v1/admin/tools/{id}/status` 승인/거부

---

## 기술 스택
- **프론트**: Trang HTML/CSS/JS (Artifact 기반)
- **백엔드**: `agent_gateway.py` + `fastapi_app.py` 확장
- **데이터**: `tool_registry.yaml` → API → UI (단방향)

---

## 담당 제안
| 작업 | 담당 |
|------|------|
| `GET /v1/tools` 엔드포인트 | Koda |
| UI fetch() 교체 + 필터 추가 | Trang |
| SIEM 경보 위젯 | Trang + Wayong |
| 관리자 토글 API | Koda + Kbin |

---

> "보이지 않는 질서는 신뢰를 낳지 못한다. Trang의 UI가 그 질서를 눈으로 보게 해준다." — Wayong
""",
        "labels": ["enhancement", "steward-console", "ui"],
    },
    {
        "title": "[AI-SIEM] Phase 2 — Railway Live 연결 + Gateway 엔드포인트 활성화",
        "body": """## 개요
AI-SIEM Phase 1 (`railway_monitor.py` + `siem_engine.py`) 완료 후,
Railway 공식 연결(Live 모드)과 Gateway API 엔드포인트를 활성화한다.

관련: commit `e10bdf6` · `research/steward_ai_siem/phase1_implementation_report.md`

---

## 배경
- Phase 1 완료: Mock 모드로 5개 탐지 규칙 동작 확인
- Railway Agent: 연결 테스트 완료 후 공식 발표 예정
- `RAILWAY_API_TOKEN` 등록 시 코드 변경 없이 Live 모드 자동 전환

---

## 작업 목록

### Railway 연결 활성화
- [ ] `RAILWAY_API_TOKEN` Railway 대시보드에서 발급
- [ ] Railway → Railway Project/Env ID 확인
- [ ] Railway 환경변수 등록: `RAILWAY_API_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_ENV_ID`
- [ ] `RailwayMonitor.snapshot()` Live 모드 확인 (`is_mock: false`)
- [ ] Railway metrics GraphQL 쿼리 확장 (CPU/메모리/네트워크 실데이터)

### Gateway API 엔드포인트 추가
- [ ] `fastapi_app.py`에 `create_siem_router()` 등록
  ```python
  from core.siem_engine import create_siem_router
  app.include_router(create_siem_router(), prefix="/v1/siem")
  ```
- [ ] `GET /v1/siem/events` — 최근 이벤트 조회
- [ ] `GET /v1/siem/cycle` — 수동 사이클 트리거
- [ ] `GET /v1/siem/summary` — 일간 요약

### Railway 예정 도구 활성화 (Railway 명세 회신 후)
- [ ] `railway.env` (R5) — 환경변수 관리
- [ ] `railway.db` (R6) — DB/Volume 접근
- [ ] `railway.cron` (R7) — 스케줄 작업

### 탐지 규칙 고도화
- [ ] R4 Spirit Score 복합 탐지 → `execution_audit.jsonl` 실시간 연동
- [ ] 이상 탐지 기준선(baseline) 자동 갱신 주기 설정
- [ ] `siem_events.jsonl` → Distillation Gate 학습 데이터 연계

---

## 환경변수 체크리스트
```
RAILWAY_API_TOKEN    ← Railway 발급 필요
RAILWAY_PROJECT_ID   ← Railway 프로젝트 ID
RAILWAY_ENV_ID       ← Railway 환경 ID
```

---

## 탐지 규칙 현황 (Phase 1 완료)
| 규칙 | 설명 | 임계값 |
|------|------|--------|
| R1 | 5xx 에러율 | warning 5% / critical 15% |
| R2 | p99 응답시간 | warning 2s / critical 5s |
| R3 | 트래픽 스파이크 | 기준선 3배 |
| R4 | Spirit Score 복합 | spirit<0.75 + error≥3% → block |
| R5 | 비정상 IP | 10회/사이클 |

---

## 담당 제안
| 작업 | 담당 |
|------|------|
| RAILWAY_API_TOKEN 발급·등록 | Railway Agent |
| fastapi_app.py SIEM 라우터 등록 | Koda |
| Live 모드 검증 | Railway Agent + Koda |
| 탐지 규칙 고도화 | Wayong + Koda |

---

> "Railway가 데이터를 제공하고, AI-SIEM이 판단한다." — Steward AI Standard v0.1
""",
        "labels": ["enhancement", "ai-siem", "railway"],
    },
]


def create_issue(issue: dict) -> str:
    url = f"https://api.github.com/repos/{REPO}/issues"
    data = json.dumps({
        "title": issue["title"],
        "body": issue["body"],
        "labels": issue.get("labels", []),
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ 이슈 생성: #{result['number']} — {result['title']}")
            print(f"   URL: {result['html_url']}")
            return result["html_url"]
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode('utf-8')}")
        return ""


if __name__ == "__main__":
    print("Mulberry Steward AI — 이슈 생성 시작")
    print("=" * 50)
    for issue in ISSUES:
        create_issue(issue)
    print("=" * 50)
    print("완료")
