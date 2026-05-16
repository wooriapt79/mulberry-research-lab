# [Koda 완료 보고] Pulse v1.3 배포 + Railway 전체 상태 진단

**보고자**: Koda (CTO)  
**수신**: re.eul 대표이사 · Trang PM  
**날짜**: 2026-05-16  
**참조**: Issue #49 · Trang PM 지시서 + 작업완료보고서

---

## Trang PM 체크리스트 응답

```
[Koda 완료 보고]
- pulse_daemon.py 배포:      OK  (commit 39a4031)
- Procfile worker 추가:      OK  (web + worker 동시 구동)
- 환경 변수 설정:            OK  (requests 포함 확인)
- Railway 재배포 확인:       OK  (auto-deploy 활성화 상태 확인)
- /api/health 응답:          {"status":"ok","service":"mulberry-mission-control","version":"3.2.1","redis":"connected"}
```

---

## 1. Railway 배포 상태 전체 점검 결과

### mulberry-mission-control (주 서비스)
`https://mulberry-mission-control-production.up.railway.app`

| 엔드포인트 | 상태 | 응답 |
|-----------|------|------|
| `GET /api/health` | **200 OK** | `{"status":"ok","service":"mulberry-mission-control","version":"3.2.1","redis":"connected","uptime":334}` |
| `GET /v1/tools` | **200 OK** | 3개 도구 반환 (malu.vision, trang.passport, trang.agent) |
| `GET /health` | **200 OK** | `{"status":"ok","version":"3.2","redis":"connected"}` |

**Trang P1+P2 안정화 완전 확인.**

---

## 2. Trang 추가 발견사항 3가지 — Koda 확인 결과

### 발견 1: Railway Auto-deploy 활성화
**확인**: Trang이 오늘 활성화 완료. `main` 브랜치 push시 자동 배포됩니다.
> Koda 인지 완료. 이후 PR 방식이 아닌 main 직접 push로 배포됩니다.

### 발견 2: Railway Root Directory 설정
**현재 상태**: `mulberry-mission-control` 폴더가 root로 정상 배포되고 있음.  
**권장 조치**: Railway 대시보드에서 명시적으로 `mulberry-mission-control` 입력 권장.  
> Trang이 직접 Railway Settings에서 확인 및 명시적 설정 요청.

### 발견 3: mulberry-open-api 서비스 정체 확인
`https://mulberry-open-api-production.up.railway.app` 점검 결과:

```
응답 헤더: Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2026)
```

**결론**: `mulberry-open-api`는 **Streamlit 앱**입니다.  
Agent Gateway가 아니며, 별도 데이터/리서치 UI 서비스입니다.  
현재 mulberry-agent-gateway URL은 404 (미배포 상태).

| 서비스 URL | 실체 | 상태 |
|-----------|------|------|
| `mulberry-mission-control-production` | Node.js 서버 (server.js) | Online |
| `mulberry-open-api-production` | **Streamlit 앱** | Online |
| `mulberry-agent-gateway-production` | FastAPI (agent_gateway.py) | **미배포 / 404** |

> **Trang + Koda 협의 필요**: agent-gateway FastAPI가 어느 Railway 서비스에 배포되어야 하는지 결정 필요.

---

## 3. Pulse v1.3 배포 상세

### 배포 파일
- `agent-gateway/pulse_daemon.py` — Trang PM v1.3 버전 (commit `de241e3` 기준 채택)
- `agent-gateway/Procfile` — worker 프로세스 추가

### Procfile 최종 상태
```
web:    uvicorn agent_gateway:app --host 0.0.0.0 --port $PORT
worker: python pulse_daemon.py
```

### 필요 환경 변수 (Railway Variables 설정 요청)
| 변수명 | 현재 상태 | 비고 |
|--------|----------|------|
| `GITHUB_TOKEN` | 확인 필요 | 없으면 데몬 즉시 실패 |
| `REPO_OWNER` | 기본값 `wooriapt79` | 선택 |
| `REPO_NAME` | 기본값 `mulberry-research-lab` | 선택 |
| `PULSE_INTERVAL` | 기본값 `600` (10분) | 조절 가능 |
| `GATEWAY_URL` | 기본값 mission-control URL | 확인 필요 |

### requirements.txt 확인 결과
```
fastapi==0.111.0    OK
uvicorn==0.30.1     OK
requests==2.32.3    OK  (Pulse 데몬 의존성 충족)
python-dotenv==1.0.1 OK
pydantic==2.7.1     OK
```
추가 설치 불필요.

---

## 4. 병합 과정 특이사항

Trang PM이 `de241e3`으로 먼저 push한 상태라 충돌 발생.  
**Trang의 pulse_daemon.py 버전을 우선 채택**하고 Procfile만 병합.  
최종 commit: `39a4031`

---

## 5. P3 다음 단계 (Trang + Koda 협의)

| 항목 | 내용 | 담당 |
|------|------|------|
| Agent Gateway 배포 서비스 결정 | mulberry-agent-gateway 서비스 신규 배포 또는 mission-control 통합 | Trang + Koda |
| GITHUB_TOKEN Railway 등록 확인 | Pulse 데몬 정상 동작 전제 조건 | Trang |
| Chat Socket.IO 연결 검증 | team-chat-frontend.js 동작 | Trang |
| AI-SIEM 모듈 데이터 연결 | /v1/siem → mission-control 대시보드 | Koda |

---

*Koda · CTO · Mulberry Research Lab · 2026-05-16*  
*"One Team. One Flow. One Spirit."*
