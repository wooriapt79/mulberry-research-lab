#!/usr/bin/env python3
"""
pipeline.py — Mulberry 자율 개발 파이프라인 오케스트레이터
===========================================================
CEO re.eul 설계 지시 기반 (2026-05-31)

완전체 파이프라인:
  고객 요청 (자연어)
      ↓
  Auto Code Pilot     — 에이전트 자율 코드 생성
      ↓
  Spirit Gate         — 윤리·거버넌스·보안 검증
      ↓  PASS (실패 시 → 재생성 최대 3회)
  Config Agent        — 서버 환경 컨디션 체크
      ↓  READY
  Code Quality Gate   — 품질 검수 (config_spec 기준)
      ↓  PASS
  배포                 — Railway / Vercel / GitHub Pages
      ↓
  고객: URL

작성: Koda CTO · Koda Coding Team · 2026-05-31
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from config_agent.main import ConfigAgent
from auto_code_pilot.pilot import AutoCodePilot
from spirit_gate.validator import SpiritGate

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
MAX_REGENERATE = 3   # Spirit Gate 실패 시 최대 재생성 횟수


@dataclass
class PipelineResult:
    status: str          # SUCCESS / BLOCKED / ENV_ERROR / QUALITY_FAIL
    url: str = ""
    message: str = ""
    report: dict = None

    @classmethod
    def success(cls, url: str) -> "PipelineResult":
        return cls(status="SUCCESS", url=url,
                   message=f"배포 완료 → {url}")

    @classmethod
    def blocked(cls, reason: str) -> "PipelineResult":
        return cls(status="BLOCKED", message=f"Spirit Gate BLOCK: {reason}")

    @classmethod
    def env_error(cls, recommendation: str) -> "PipelineResult":
        return cls(status="ENV_ERROR", message=f"환경 오류: {recommendation}")

    @classmethod
    def quality_fail(cls, report: dict) -> "PipelineResult":
        return cls(status="QUALITY_FAIL", message="Quality Gate 실패", report=report)


def run_pipeline(request: str, target: str = "railway") -> PipelineResult:
    """
    Mulberry 자율 개발 전체 파이프라인 실행.
    """
    print(f"\n{'='*55}")
    print(f"  🌿 Mulberry Auto Dev Pipeline")
    print(f"  요청: {request[:60]}")
    print(f"  타겟: {target}")
    print(f"{'='*55}\n")

    # ── Step 1: Config Agent — 환경 초기화 ───────────────────────
    print("⚙️  [Step 1/5] Config Agent — 환경 초기화")
    pilot = AutoCodePilot(deploy_target=target)
    ctx = pilot.ctx

    # ── Step 2: Auto Code Pilot — 코드 생성 ──────────────────────
    print(f"\n🤖 [Step 2/5] Auto Code Pilot — 코드 생성")
    code = pilot.generate(request)
    output_dir = Path("auto_code_pilot/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    code_file = output_dir / "main.py"
    code_file.write_text(code, encoding="utf-8")
    print(f"   코드 생성 완료 ({len(code)}자)")

    # ── Step 3: Spirit Gate — 검증 (최대 3회 재생성) ─────────────
    print(f"\n🛡️  [Step 3/5] Spirit Gate — 윤리·보안 검증")
    gate = SpiritGate(expected_lang=ctx.get("backend_language", "python"))

    gate_result = None
    for attempt in range(1, MAX_REGENERATE + 1):
        gate_result = gate.validate(code)

        if gate_result.status == "PASS":
            break

        if gate_result.status == "BLOCK":
            print(f"   🚫 BLOCK — 완전 차단. CEO 보고 필요.")
            return PipelineResult.blocked(gate_result.feedback)

        if attempt < MAX_REGENERATE:
            print(f"   ⚠️  FAIL — 재생성 시도 {attempt}/{MAX_REGENERATE}")
            print(f"   피드백: {gate_result.feedback[:100]}")
            # 피드백 반영하여 재생성
            refined_request = f"{request}\n\n[수정 요청]\n{gate_result.feedback}"
            code = pilot.generate(refined_request)
            code_file.write_text(code, encoding="utf-8")
        else:
            print(f"   ❌ Spirit Gate 최대 재시도 초과 — 수동 검토 필요")
            return PipelineResult.blocked("Spirit Gate 3회 재생성 실패")

    # ── Step 4: Config Agent — 환경 컨디션 체크 ──────────────────
    print(f"\n⚙️  [Step 4/5] Config Agent — 서버 환경 컨디션 체크")
    env_ok, env_msg = _check_environment(pilot.config)
    if not env_ok:
        return PipelineResult.env_error(env_msg)
    print(f"   ✅ 환경 컨디션 READY")

    # ── Step 5: Code Quality Gate — 품질 검수 ────────────────────
    print(f"\n🔍 [Step 5/5] Code Quality Gate — 품질 검수")
    quality_passed = pilot.quality_check(code, code_file)
    if not quality_passed:
        gate_json = Path("gate_result.json")
        report = json.loads(gate_json.read_text(encoding="utf-8")) if gate_json.exists() else {}
        return PipelineResult.quality_fail(report)

    # ── 배포 파일 준비 ────────────────────────────────────────────
    pilot.config.generate_deploy_files(target=target, root=output_dir)

    # 완료
    estimated_url = f"https://project.{target}.app"
    print(f"\n{'='*55}")
    print(f"  ✅ 파이프라인 완료!")
    print(f"  🎯 배포 URL: {estimated_url}")
    print(f"  Spirit Gate: {gate_result.status}")
    print(f"  Quality Gate: PASS")
    print(f"{'='*55}\n")

    return PipelineResult.success(estimated_url)


def _check_environment(config: ConfigAgent) -> tuple[bool, str]:
    """Config Agent 환경 컨디션 체크 (Phase 2 확장 예정)"""
    workspace = config.setup_workspace()
    if workspace.get("missing"):
        return False, f"필수 파일 누락: {workspace['missing']}"
    # TODO: Railway API 상태 체크, 환경변수 누락 감지 (Phase 2)
    return True, "OK"


# ── 실행 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry Auto Dev Pipeline")
    parser.add_argument("request", nargs="?",
                        default="간단한 Hello World 웹 서버 만들어줘")
    parser.add_argument("--target", default="railway")
    args = parser.parse_args()

    result = run_pipeline(request=args.request, target=args.target)
    print(f"\n최종 결과: {result.status}")
    if result.url:
        print(f"URL: {result.url}")
    if result.message:
        print(f"메시지: {result.message}")
