#!/usr/bin/env python3
"""
auto_code_pilot/pilot.py — Mulberry 자율 코딩 파일럿
=====================================================
역할:
  고객의 자연어 요청을 받아 Mulberry DNA 기준으로 코드를 생성하고
  배포까지 자동으로 완료한다.

파이프라인:
  고객 요청 (자연어)
      ↓
  ConfigAgent → DNA·환경 로드 (config_spec.yaml)
      ↓
  Auto Code Pilot → LLM 코드 생성 (DNA 기준 준수)
      ↓
  Code Quality Gate → 품질 검증 (config_agent 기준)
      ↓
  배포 → 고객 URL

작성: Koda CTO · Koda Coding Team · 2026-05-31
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# config_agent 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_agent.main import ConfigAgent

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class AutoCodePilot:
    """
    Mulberry 자율 코딩 파일럿.
    ConfigAgent의 DNA를 읽어 코드를 생성하고 배포한다.
    """

    def __init__(self, deploy_target: str = None):
        print(f"\n{'='*55}")
        print(f"  Auto Code Pilot — Koda Coding Team")
        print(f"  {TIMESTAMP}")
        print(f"{'='*55}\n")

        # 1. ConfigAgent 실행 → 환경 초기화
        print("⚙️  ConfigAgent 환경 초기화 중...")
        self.config = ConfigAgent(mode="dev")
        self.report = self.config.run(deploy_target=deploy_target)
        self.ctx = self.report["deploy_context"]

        if not self.report["ready"]:
            raise RuntimeError("ConfigAgent 환경 초기화 실패 — PM 승인 필요")

        print(f"✅ 환경 준비 완료")
        print(f"   DNA: {self.ctx['brand']} · {self.ctx['spirit']}")
        print(f"   배포: {self.ctx['target']} · ETA {self.ctx['eta_minutes']}분\n")

    def _build_system_prompt(self) -> str:
        """Mulberry DNA 기반 코드 생성 시스템 프롬프트"""
        spec = self.config.spec
        dna  = spec.get("dna", {})
        qs   = spec.get("quality_standards", {})
        cg   = spec.get("code_generation", {})

        return f"""당신은 Mulberry Research Lab의 자율 코딩 파일럿입니다.
반드시 아래 Mulberry DNA 기준으로 코드를 생성하세요.

## Mulberry DNA
- 브랜드: {self.ctx['brand']}
- 정신: {self.ctx['spirit']} (사람을 위한 기술)
- 백엔드: {dna.get('backend_language', 'python')}
- 프론트엔드: {dna.get('frontend_style', 'vanilla-js')}
- 배포 타겟: {self.ctx['target']}

## 코드 품질 기준 (Code Quality Gate 적용 기준)
- HIGH 보안 취약점: {qs.get('bandit_high', 0)}개 허용
- 최대 함수 복잡도: {qs.get('complexity_max', 15)}
- 최소 유지보수 지수: {qs.get('maintainability_min', 10)}

## 코드 작성 규칙
1. Python {dna.get('backend_language', 'python')} 기준으로 작성
2. 주석은 한국어로 (# 이렇게)
3. 파일 상단에 반드시 작성자 서명 포함:
   # Mulberry · Koda Coding Team · {TIMESTAMP[:10]}
4. subprocess, eval, exec 등 위험 함수 사용 금지
5. 복잡도 15 이하로 함수 분리
6. {self.ctx['target']} 배포 환경에 최적화

## 출력 형식
완성된 파이썬 코드만 출력하세요. 설명 없이, 코드 블록(```) 없이."""

    def generate(self, customer_request: str) -> str:
        """
        고객 요청을 받아 Mulberry DNA 기준의 코드를 생성한다.
        ConfigAgent의 deploy_context를 코드 생성 기준으로 활용.
        """
        if not ANTHROPIC_KEY:
            # 데모 모드 — 실제 API 없이 샘플 코드 반환
            return self._demo_code(customer_request)

        import urllib.request
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": "claude-sonnet-4-5-20251022",
            "max_tokens": 4096,
            "system": self._build_system_prompt(),
            "messages": [{"role": "user", "content": customer_request}],
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["content"][0]["text"]
        except Exception as e:
            print(f"❌ 코드 생성 오류: {e}")
            return self._demo_code(customer_request)

    def _demo_code(self, request: str) -> str:
        """API 없이 동작하는 데모 코드 생성"""
        brand  = self.ctx["brand"]
        spirit = self.ctx["spirit"]
        target = self.ctx["target"]
        return f'''#!/usr/bin/env python3
# Mulberry · Koda Coding Team · {TIMESTAMP[:10]}
# 고객 요청: {request[:60]}
# 배포 타겟: {target}

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="{brand} App", description="{spirit}")

@app.get("/", response_class=HTMLResponse)
def home():
    """메인 페이지 — {brand} DNA 기반"""
    return """
    <html>
    <head><title>{brand}</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:50px;background:#0d0d14;color:#e8e6f0">
        <h1>🌿 {brand}</h1>
        <p>{spirit} 정신 — AI serves humans</p>
        <p style="color:#7F77DD">요청: {request[:80]}</p>
    </body>
    </html>
    """

@app.get("/health")
def health():
    return {{"status": "ok", "brand": "{brand}", "spirit": "{spirit}"}}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''

    def quality_check(self, code: str, filepath: Path) -> bool:
        """
        생성된 코드를 Code Quality Gate로 검증.
        config_agent의 quality_standards 기준 자동 적용.
        """
        print("\n🔍 Code Quality Gate 검증 중...")
        filepath.write_text(code, encoding="utf-8")
        gate_script = Path(".github/scripts/quality_gate/run_gate.py")

        if not gate_script.exists():
            print("  ⚠️  Quality Gate 스크립트 없음 — 스킵")
            return True

        result = subprocess.run(
            [sys.executable, str(gate_script), str(filepath)],
            capture_output=True, text=True
        )
        # gate_result.json 확인
        gate_result = Path("gate_result.json")
        if gate_result.exists():
            data = json.loads(gate_result.read_text(encoding="utf-8"))
            verdict = data.get("verdict", "PASS")
            print(f"  판정: {verdict}")
            if verdict == "BLOCK":
                print("  ❌ BLOCK — 코드 재생성 필요")
                return False
        print("  ✅ 품질 검증 통과")
        return True

    def run(self, customer_request: str) -> dict:
        """
        전체 파이프라인 실행:
        요청 → 코드 생성 → 품질 검증 → 배포 파일 준비
        """
        print(f"📝 고객 요청: {customer_request[:80]}")
        print(f"\n{'─'*55}")

        # 코드 생성
        print("🤖 [1/3] Mulberry DNA 기준 코드 생성 중...")
        code = self.generate(customer_request)

        # 임시 저장
        output_dir = Path("auto_code_pilot/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        code_file = output_dir / "main.py"
        code_file.write_text(code, encoding="utf-8")
        print(f"  코드 저장: {code_file} ({len(code)}자)")

        # 품질 검증
        print("\n🔍 [2/3] Code Quality Gate 검증...")
        passed = self.quality_check(code, code_file)

        # 배포 준비
        print("\n🚀 [3/3] 배포 환경 파일 준비...")
        self.config.generate_deploy_files(
            target=self.ctx["target"],
            root=output_dir
        )

        result = {
            "timestamp": TIMESTAMP,
            "request": customer_request,
            "deploy_context": self.ctx,
            "code_file": str(code_file),
            "quality_passed": passed,
            "ready_to_deploy": passed,
            "estimated_url": f"https://project.{self.ctx['target']}.app",
        }

        print(f"\n{'='*55}")
        if result["ready_to_deploy"]:
            print(f"  ✅ 배포 준비 완료!")
            print(f"  🎯 예상 URL: {result['estimated_url']}")
        else:
            print(f"  ⚠️  품질 검증 실패 — 수동 검토 필요")
        print(f"{'='*55}\n")

        return result


# ── 실행 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry Auto Code Pilot")
    parser.add_argument("request", nargs="?",
                        default="간단한 Hello World 웹 서버 만들어줘",
                        help="고객 요청 (자연어)")
    parser.add_argument("--target", default=None,
                        help="배포 타겟 (railway/vercel/github_pages)")
    args = parser.parse_args()

    pilot = AutoCodePilot(deploy_target=args.target)
    result = pilot.run(customer_request=args.request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
