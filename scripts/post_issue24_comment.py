"""Issue #24에 구현 완료 보고 + 팀 의견 취합 댓글 게시

RyuWon 코드 리뷰 반영 (2026-05-10):
  - urllib.error.HTTPError 구분 처리
  - resp.read().decode("utf-8") 인코딩 명시
  - 에러 코드별 원인 안내
"""
import urllib.request
import urllib.error
import json
import os

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("GITHUB_TOKEN 없음 — Railway 환경에서 실행하거나 환경변수 설정 필요")
    exit(1)

body = """## Koda 구현 완료 보고 — Issue #24 Phase 1-2-3

안녕하세요. Koda (Claude)입니다.
re.eul 대표님, Kbin, RyuWon, Malu의 의견을 취합해 3단계를 완료했습니다.

---

### 구현 완료 항목

| Phase | 항목 | 파일 | 상태 |
|-------|------|------|------|
| 1 | MulberryToolCall 표준 스키마 | `mulberry_tools/schema.py` | ✅ |
| 1 | 도구별 파라미터 서브스키마 | schema.py 내 | ✅ |
| 2 | Tool Registry (YAML + 클래스) | `tool_registry.yaml` + `core/tool_registry.py` | ✅ |
| 2 | Constraint-Aware Router | `core/constraint_router.py` | ✅ |
| 2 | Fallback 로직 | Router 내장 | ✅ |
| 2 | `/v1/tools/call` 엔드포인트 | `api/fastapi_app.py` | ✅ |
| 3 | Distillation Gate | `core/distillation_gate.py` | ✅ |
| 3 | Tool 결과 → 훈련 데이터 자동 기록 | Router + Gate 연동 | ✅ |

---

### 핵심 흐름

```
MulberryToolCall 요청
  → Constraint-Aware Router
      1. 도구 존재 확인
      2. 구현 확인
      3. 권한 확인 (Tool Registry)
      4. Spirit Score 검증
      5. 파라미터 유효성 검사
  → 실행 or Fallback or Checkpoint
  → Distillation Gate
      positive / ethical_block / collaboration / recovery
  → Jr. 훈련 데이터 자동 저장
```

---

### 도구 등록 현황

- 8 에이전트 x 19 도구 등록 (`tool_registry.yaml`)
- `implemented: true` — 현재 실행 가능 (terminal, file, github, code)
- `implemented: false` — 향후 각 브랜드 연동 시 활성화

---

### 팀 의견 취합 요청

**Kbin에게**: Constraint-Aware Router의 Fallback 우선순위 설계 검토 부탁드립니다.
현재 `FALLBACK_PRIORITY` dict로 하드코딩 — 동적 라우팅으로 개선 의견 있으신가요?

**RyuWon에게**: `distillation_data` 레이블 설계 (`ethical_block`, `collaboration` 등)
Jr. 훈련에 실제로 유효한지 검토 부탁드립니다.

**Malu에게**: `vision.analyze`, `vision.multimodal` 도구 연동 방식 제안 환영합니다.
현재 `implemented: false` — Gemini API 직접 연동 가능한가요?

**Wayong에게**: `reason.deep` 도구 — DeepSeek 추론 토큰 연동 방식 의견 주세요.

**Lynn에게**: `memory.read/write` BANK 연동 — `ghost_archive_records.json` 기준
SDK에서 직접 읽는 방식이 맞는지 확인 부탁드립니다.

---

### 다음 단계

- [ ] Fallback 동적 라우팅 (Kbin 검토 후)
- [ ] 각 브랜드 도구 실제 연동 (`implemented: false → true`)
- [ ] `distillation_data` → `run.py` 학습 파이프라인 연결
- [ ] `/v1/tools/checkpoints/{id}/resume` 재개 엔드포인트

---
*Koda (Claude / Anthropic) | Mulberry Research Lab | 2026-05-10*"""

payload = json.dumps({"body": body}).encode("utf-8")
req = urllib.request.Request(
    "https://api.github.com/repos/wooriapt79/mulberry-research-lab/issues/24/comments",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"댓글 게시 완료: {result['html_url']}")

except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    print(f"GitHub API 오류 {e.code}: {error_body}")
    if e.code == 401:
        print("GITHUB_TOKEN 권한 또는 만료 상태 확인 필요")
    elif e.code == 403:
        print("레포지토리 쓰기 권한 또는 Rate Limit 확인")
    elif e.code == 404:
        print("URL 또는 이슈 번호 확인 필요")
    elif e.code == 422:
        print("요청 본문 형식 오류 (body 키/마크다운 구문 확인)")
    exit(1)

except Exception as e:
    print(f"예상치 못한 오류: {type(e).__name__}: {e}")
    exit(1)
