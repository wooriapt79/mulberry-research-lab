"""
Issue #38 — Trang PM 수정 완료 댓글 게시 스크립트
실행: python scripts/post_issue38_trang.py
"""
import urllib.request
import urllib.error
import json
import os
import sys

ISSUE_NUMBER = "38"
REPO = "wooriapt79/mulberry-research-lab"

COMMENT_BODY = """## ✅ [Trang PM] Issue #38 수정 완료 보고

Koda CTO가 오늘(2026-05-12) Issue #38에 보고된 **P0~P3 전체 4건**을 수정 완료했습니다.
Trang이 작업 내역을 검토하고 완료 보고 드립니다.

---

### 📋 수정 내역 요약

| 심각도 | 문제 | 수정 결과 |
|--------|------|----------|
| **P0 Critical** | Backend API 전부 404 (52건) | `GET /metrics/overview` · `/system/modules/health` · `/agents/{id}` · `/chat/channels` · `POST /chat/send` 신규 추가 ✅ |
| **P1 High** | 사이드바 4개만 표시 | 8개 모듈 전체 표시 (home / chat / agents / skills / coopbuy / field / analytics / settings) ✅ |
| **P2 Medium** | 채팅 입력 폼 미생성 | 채널 목록 + 메시지 영역 + 입력 폼 항상 표시, API 실패 graceful 처리 ✅ |
| **P3 Low** | 이모지 폰트 Windows 깨짐 | `Segoe UI Emoji` / `Apple Color Emoji` / `Noto Color Emoji` fallback CSS 추가 ✅ |

---

### 📁 변경 파일

- `agent-gateway/agent_gateway.py` — v1.2.0 → **v1.3.0** (API 5개 신규 엔드포인트)
- `agent-gateway/mission_control.html` — **신규** Mission Control SPA 전체 구현

### 🔗 접속 경로
Railway 재배포 후: `{agent-gateway-URL}/mission-control`

---

### ✅ 검증 체크리스트 (Trang PM 확인 요청)

- [ ] Railway agent-gateway 재배포 완료
- [ ] `/metrics/overview` → JSON 응답 확인 (HTML 아닌 것 확인)
- [ ] 사이드바 8개 모듈 모두 클릭 가능 확인
- [ ] 채팅 채널 목록 + 입력 폼 표시 확인
- [ ] Windows Chrome에서 이모지 정상 렌더링 확인

---

수고 많으셨습니다. re.eul 소장님, 검토 부탁드립니다. 🌿

---
*[Trang] Nguyen Trang (PM) | Mulberry Agent Relay | 2026-05-12*"""

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("GITHUB_TOKEN 없음 — GitHub Actions에서 실행하세요.")
    sys.exit(1)

url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
}
data = json.dumps({"body": COMMENT_BODY}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"✅ 댓글 게시 성공: {result['html_url']}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")
    print(f"❌ HTTP {e.code}: {body}")
    sys.exit(1)
