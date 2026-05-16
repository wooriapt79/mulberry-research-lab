# [Koda → Trang] Agent Gateway Railway 신규 서비스 설정 가이드

**작성자**: Koda (CTO)  
**수신**: Trang PM  
**날짜**: 2026-05-16  
**참조**: Issue #49 · Trang PM 지시 "agent-gateway 신규 Railway 서비스로 분리"

---

## 완료 사항

### agent_gateway.py v1.3.0 업데이트 (commit `f5403b3`)

`/api/health` 엔드포인트 추가 완료:

```
GET /api/health
```

**예상 응답:**
```json
{
  "status": "ok",
  "service": "mulberry-agent-gateway",
  "version": "1.3.0",
  "github_ready": true,
  "agents": 8,
  "uptime": 142,
  "timestamp": "2026-05-16T10:23:45.123456Z"
}
```

---

## Railway 신규 서비스 설정 절차

### Step 1 — Railway 대시보드 접속

1. [railway.app](https://railway.app) → Mulberry 프로젝트 진입
2. **+ New Service** 클릭 → **GitHub Repo** 선택

### Step 2 — 레포 연결

| 항목 | 설정값 |
|------|--------|
| Repository | `wooriapt79/mulberry-research-lab` |
| Branch | `main` |
| **Root Directory** | `agent-gateway` ← 반드시 입력 |

### Step 3 — 빌드 설정

Railway가 `Procfile`을 자동 감지합니다.

**`agent-gateway/Procfile` 현재 상태:**
```
web:    uvicorn agent_gateway:app --host 0.0.0.0 --port $PORT
worker: python pulse_daemon.py
```

- `web` 프로세스: FastAPI + uvicorn (Railway가 `$PORT` 자동 주입)
- `worker` 프로세스: Pulse Daemon v1.3 (GitHub 이슈 자율 스캔)

### Step 4 — 환경 변수 (Variables) 설정

Railway 서비스 → **Variables** 탭에서 아래 변수 등록:

| 변수명 | 값 | 필수 여부 |
|--------|-----|---------|
| `GITHUB_TOKEN` | GitHub PAT (repo scope) | **필수** — 없으면 Pulse 데몬 즉시 실패 |
| `GATEWAY_SECRET` | 원하는 API 키 | 권장 (기본값: `mulberry-agent-relay-2026`) |
| `MULBERRY_REPO_OWNER` | `wooriapt79` | 선택 (기본값 있음) |
| `REPO_OWNER` | `wooriapt79` | 선택 (Pulse 데몬용) |
| `REPO_NAME` | `mulberry-research-lab` | 선택 (Pulse 데몬용) |
| `PULSE_INTERVAL` | `600` | 선택 (10분 주기, 조절 가능) |
| `GATEWAY_URL` | *(배포 후 자동 생성 URL 입력)* | 선택 |

> **GITHUB_TOKEN 최우선 등록 요청** — Pulse v1.3 데몬이 이 토큰으로 GitHub API를 호출합니다.

### Step 5 — Auto Deploy 활성화

- Settings → **Source** → Auto-deploy: **Enabled**
- `main` 브랜치 push 시 자동 재배포

### Step 6 — 배포 확인

배포 완료 후 아래 URL 테스트:

```
GET https://mulberry-agent-gateway-production.up.railway.app/api/health
```

**기대 응답:**
```json
{
  "status": "ok",
  "service": "mulberry-agent-gateway",
  "version": "1.3.0",
  "github_ready": true,
  "agents": 8,
  "uptime": <숫자>,
  "timestamp": "<ISO timestamp>"
}
```

---

## Trang PM 후속 작업 (URL 확인 후)

Railway가 생성하는 실제 URL을 아래 두 곳에 등록 부탁드립니다:

### 1. `mulberry-mission-control/server.js` — `/v1/tools` agent-gateway 엔드포인트
```javascript
// AGENT_GATEWAY_URL 변수 또는 하드코딩 업데이트
const AGENT_GATEWAY_URL = "https://mulberry-agent-gateway-production.up.railway.app";
```

### 2. `agent-gateway/pulse_daemon.py` — `GATEWAY_URL` 환경변수
```
GATEWAY_URL = https://mulberry-agent-gateway-production.up.railway.app
```
(Railway Variables에서 설정 가능, 하드코딩 불필요)

---

## 현재 전체 서비스 구조

| 서비스 | URL | 런타임 | 상태 |
|--------|-----|--------|------|
| mulberry-mission-control | `https://mulberry-mission-control-production.up.railway.app` | Node.js | Online ✅ |
| mulberry-open-api | `https://mulberry-open-api-production.up.railway.app` | Streamlit | Online ✅ |
| **mulberry-agent-gateway** | *(Railway 생성 예정)* | **FastAPI + Pulse** | **설정 대기** |

---

*Koda · CTO · Mulberry Research Lab · 2026-05-16*  
*"One Team. One Flow. One Spirit."*
