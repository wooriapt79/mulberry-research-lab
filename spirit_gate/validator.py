#!/usr/bin/env python3
"""
spirit_gate/validator.py — Mulberry Spirit Gate 메인 검증기
===========================================================
역할:
  Auto Code Pilot이 생성한 코드가
  Mulberry 헌법·윤리·보안 기준을 통과하는지 검증한다.

판정:
  PASS  → Config Agent로 전달
  FAIL  → 실패 사유 + 재생성 요청 → Auto Code Pilot 재시도 (최대 3회)
  BLOCK → 완전 차단 + CEO 보고 (보안 위협 수준)

작성: Koda CTO · Koda Coding Team · 2026-05-31
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from .gate_result import GateResult, CheckResult
from .checks.security import check_hardcoded_secrets, check_dangerous_patterns
from .checks.hallucination import check_hallucination_patterns
from .checks.dna_compliance import (
    check_mulberry_signature,
    check_language_compliance,
    check_human_first_principle,
)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SpiritGate:
    """
    Mulberry Spirit Gate.
    생성된 코드의 윤리·보안·DNA 정합성을 검증한다.
    """

    def __init__(self, expected_lang: str = "python"):
        self.expected_lang = expected_lang

    def validate(self, code: str, metadata: dict = None) -> GateResult:
        """
        전체 검증 실행.
        모든 체크를 수행하고 GateResult 반환.
        """
        metadata = metadata or {}
        print(f"\n{'─'*55}")
        print(f"  🛡️  Spirit Gate 검증 시작")
        print(f"{'─'*55}")

        checks = [
            # 보안 검증 (BLOCK 가능)
            check_hardcoded_secrets(code),
            check_dangerous_patterns(code),

            # 할루시네이션 검증
            check_hallucination_patterns(code),

            # DNA 정합성 검증
            check_mulberry_signature(code),
            check_language_compliance(code, self.expected_lang),
            check_human_first_principle(code),
        ]

        result = GateResult(checks=checks)

        # 결과 출력
        for c in checks:
            icon = "✅" if c.passed else ("🚫" if c.severity == "BLOCK" else "❌")
            print(f"  {icon} {c.name}: {c.message}")
            if not c.passed and c.detail:
                print(f"      → {c.detail}")

        print(f"{'─'*55}")
        status_icon = {"PASS": "✅", "FAIL": "⚠️", "BLOCK": "🚫"}[result.status]
        print(f"  {status_icon} Spirit Gate 판정: {result.status}")
        print(f"{'─'*55}\n")

        return result


# ── 단독 실행 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry Spirit Gate")
    parser.add_argument("file", help="검증할 Python 파일 경로")
    args = parser.parse_args()

    code = Path(args.file).read_text(encoding="utf-8")
    gate = SpiritGate()
    result = gate.validate(code)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    sys.exit(0 if result.status == "PASS" else 1)
