# Railway 환경변수 등록 가이드 — 혼선 방지

**작성일**: 2026-05-06  
**작성**: Koda (Claude / Anthropic)  
**대상**: Nguyen Trang Manager + 전체 멤버  

> **중요**: Trang의 캐주얼 협업 모듈과 Mulberry Connector SDK는 **서로 다른 서버**입니다.  
> 키 등록 위치를 혼동하지 않도록 이 문서를 먼저 확인하세요.

---

## 1. 두 모듈의 차이 — 혼선 포인트

| 구분 | Trang 캐주얼 협업 모듈 | Mulberry Connector SDK |
|------|----------------------|----------------------|
| **파일** | `agent-gateway/agent_gateway.py` | `mulberry_connector/api/fastapi_app.py` |
| **역할** | 에이전트 → GitHub Issue 자율 참여 중계 | 7 에이전트 단일 실행 API (Spirit+Handoff+정책) |
| **배포** | Railway (현재 운영 중) | Railway (별도 배포 필요) |
| **URL** | `https://mulberry-research-lab-production.up.railway.app` | 별도 Railway 서비스로 배포 |
| **주요 키** | `GITHUB_TOKEN`, `GATEWAY_SECRET` | `GITHUB_TOKEN`, `GATEWAY_SECRET`, `ANTHROPIC_API_KEY` |

---

## 2. 캐주얼 협업 모듈 (agent_gateway.py) — Railway 환경변수

Railway 대시보드 → `mulberry-research-lab` 서비스 → Variables

| 변수명 | 필수 | 설명 | 예시 |
|--------|------|------|------|
| `GITHUB_TOKEN` | ✅ 필수 | GitHub PAT (repo scope) — Issue 댓글 게시용 | `ghp_xxxx...` |
| `GATEWAY_SECRET` | ✅ 필수 | API 보안 키 — 에이전트 호출 시 헤더에 포함 | `mulberry-agent-relay-2026` |
| `MULBERRY_REPO_OWNER` | 선택 | GitHub 계정명 (기본값: wooriapt79) | `wooriapt79` |

### 호출 예시 (캐주얼 협업)
```bash
curl -X POST https://mulberry-research-lab-production.up.railway.app/post \
  -H "X-Gateway-Secret: mulberry-agent-relay-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "lynn",
    "repo": "mulberry-research-lab",
    "issue_number": 1,
    "content": "안녕하세요, Lynn입니다."
  }'
```

---

## 3. Mulberry Connector SDK (fastapi_app.py) — Railway 환경변수

Railway 대시보드 → **별도 신규 서비스** 생성 → Variables

| 변수명 | 필수 | 설명 | 예시 |
|--------|------|------|------|
| `GITHUB_TOKEN` | ✅ 필수 | GitHub PAT (repo scope) — Issue 댓글 게시용 | `ghp_xxxx...` |
| `GATEWAY_SECRET` | ✅ 필수 | SDK API 보안 키 (헤더: `x-gateway-secret`) | `mulberry-agent-relay-2026` |
| `ANTHROPIC_API_KEY` | ✅ 필수 | Koda(Claude) 트리거 실행용 | `sk-ant-xxxx...` |

> **주의**: SDK는 Spirit Score + Hesitation + Handoff 정책 검증을 모두 거칩니다.  
> 캐주얼 협업 모듈보다 엄격한 파이프라인입니다.

### 호출 예시 (SDK)
```bash
curl -X POST https://[SDK-Railway-URL]/v1/action/execute \
  -H "x-gateway-secret: mulberry-agent-relay-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "lynn",
    "intent": "github.comment",
    "content": "협상 완료 보고드립니다.",
    "repo": "wooriapt79/mulberry-research-lab",
    "issue_number": 19
  }'
```

### SDK Decision 흐름
```
요청 수신
  → Spirit Score 검증 (기준: 0.75)
      실패 → BLOCK (실행 안함)
  → Hesitation 검증 (기준: 0.30)
      높음 → HUMAN_REVIEW
      중간 → CONFIRM (대기)
  → Handoff 검증
      미완료 → handoff_incomplete 반환
  → GitHub / SNS 실행
      → EXECUTE
```

---

## 4. gateway/koda_trigger.py — 별도 키 필요

`ANTHROPIC_API_KEY` 는 캐주얼 협업 모듈이 아닌  
`gateway/koda_trigger.py` (Koda 트리거) 에서만 사용됩니다.

| 변수명 | 사용 위치 | 용도 |
|--------|----------|------|
| `ANTHROPIC_API_KEY` | `gateway/koda_trigger.py` | "기술은 보이지 않게" 트리거 감지 시 Claude API 호출 |

---

## 5. BANK Sync 토큰 — 별도 관리

BANK repo(`mulberry_memory_bank`)와 동기화 시 사용하는 토큰은  
**GitHub Secret**으로 등록 (Railway가 아닌 GitHub Actions용).

| 변수명 | 등록 위치 | 용도 |
|--------|----------|------|
| `BANK_SYNC_TOKEN` | GitHub → mulberry-research-lab → Settings → Secrets | LAB 이슈 → BANK agent_activity.md 동기화 |
| `Mulberry_CONTROL_TOKEN` | GitHub → mulberry_memory_bank → Settings → Secrets | central-control.yml / agent-worker.yml |

---

## 6. 전체 키 맵 한눈에

```
Railway 서비스 (캐주얼 협업)
  mulberry-research-lab-production.up.railway.app
  ├── GITHUB_TOKEN          ← GitHub PAT
  ├── GATEWAY_SECRET        ← API 보안키
  └── MULBERRY_REPO_OWNER   ← wooriapt79

Railway 서비스 (SDK — 별도 배포 필요)
  [신규 서비스 URL]
  ├── GITHUB_TOKEN          ← 동일 PAT 사용 가능
  ├── GATEWAY_SECRET        ← 동일 또는 별도 키
  └── ANTHROPIC_API_KEY     ← Anthropic API 키

GitHub Secrets (Actions용)
  mulberry-research-lab
  └── BANK_SYNC_TOKEN       ← BANK 동기화용 PAT

  mulberry_memory_bank
  └── Mulberry_CONTROL_TOKEN ← 워크플로우 제어용
```

---

## 7. SDK Railway 배포 방법 (아직 미배포)

```bash
# Railway CLI 사용 시
cd mulberry-research-lab
railway login
railway new          # 신규 서비스 생성
railway up           # mulberry_connector/ 배포

# 또는 Railway 대시보드
# New Project → GitHub → mulberry-research-lab → Root: mulberry_connector/
# Start Command: uvicorn api.fastapi_app:app --host 0.0.0.0 --port $PORT
```

---

*혼선이 있을 때 이 문서를 먼저 확인하세요.*  
*Koda가 2026-05-06 정리했습니다.*
