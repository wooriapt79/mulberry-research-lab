--- Recorded at: 2026-04-02T16:13:09.853016 ---
# Mulberry Research Lab - Reliability Sandbox

이 패키지는 **중단 신호 처리 표준(에러코드별 행동표)**을 Lab 환경에서 먼저 실험하고,
검증 후 `mulberry_memory_bank` / `mulberry-open-api`로 이관하기 위한 최소 실행 패키지입니다.

## 포함 범위

- `error_policy.yaml`: 에러코드별 retry/hold/fail/reroute 정책
- `ErrorPolicyRouter`: 정책 라우팅 엔진
- `CheckpointService`: 보류/실패/재시도 체크포인트 저장(메모리 구현)
- `AlertService`: 사용자/운영자 알림 인터페이스(콘솔 구현)
- `FastAPI middleware`: 요청/실패를 자동 정책 처리
- 테스트 5개: 라우팅/체크포인트/미들웨어 통합 검증

## 폴더 구조

```text
services/reliability/
  error_policy.yaml
  error_router.py
  checkpoint_service.py
  alert_service.py
  schemas.py
  policy_loader.py

api/
  main.py
  middleware/
  routers/

tests/reliability/
  test_error_router.py
  test_retry_backoff.py
  test_on_hold_checkpoint.py
  test_bio_etiquette_reroute.py
  test_middleware_integration.py
```

## 실행 방법

```bash
cd mulberry-research-lab
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn api.main:app --reload --port 8000
```

### 테스트

```bash
cd mulberry-research-lab
PYTHONPATH=. pytest -q
```

## API 데모

- Health: `GET /api/v1/health`
- 강제 오류: `GET /api/v1/demo-error?code=429`

예시:

```bash
curl -i "http://localhost:8000/api/v1/demo-error?code=429" \
  -H "x-transaction-id: TX-1001" \
  -H "x-agent-id: Lynn-01" \
  -H "x-agent-status: online"
```

## 운영 이전 체크리스트

1. `CheckpointService`를 DB 저장소 구현으로 교체
2. `AlertService`를 Slack/Telegram/SMS 채널로 교체
3. `error_policy.yaml` 버전 고정 및 변경 승인 프로세스 연결
4. Shadow mode로 3일 이상 검증 후 운영 전환
5. `transaction_id` 멱등성 보장(중복 정산/주문 방지)

# Face-Off Agent System Integrated Package (v1.2)

## 📦 구성 모듈 안내
1. **face_off_identity.py**: AP2Mandate, AgentPassport 클래스 (신원 및 권한 정의)
2. **face_off_intelligence.py**: JangseungbaegiLibrary, GhostArchive 클래스 (지능 저장 및 경험 기록)
3. **face_off_system.py**: FaceOffAgentSystem 클래스 (전체 라이프사이클 오케스트레이션)
4. **face_off_social.py**: GuardianAlgorithm, SocialBizOrchestrator 클래스 (사회적 환원 및 마을 비즈니스)

## 🚀 시작하기
메인 시스템 파일인 `face_off_system.py`를 임포트하여 에이전트를 생성하고 임무를 수행할 수 있습니다.
