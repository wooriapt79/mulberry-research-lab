"""
spirit_gate/gate_result.py — Spirit Gate 판정 결과 클래스
작성: Koda CTO · Koda Coding Team · 2026-05-31
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str      # INFO / WARN / FAIL / BLOCK
    message: str
    detail: str = ""


@dataclass
class GateResult:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def status(self) -> str:
        """PASS / FAIL / BLOCK"""
        if any(c.severity == "BLOCK" for c in self.checks if not c.passed):
            return "BLOCK"
        if any(not c.passed for c in self.checks):
            return "FAIL"
        return "PASS"

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.passed]

    @property
    def feedback(self) -> str:
        """Auto Code Pilot 재생성 시 전달할 피드백"""
        if self.status == "PASS":
            return ""
        lines = ["Spirit Gate 검증 실패 — 아래 사항을 수정해서 재생성하세요:\n"]
        for c in self.failed_checks:
            lines.append(f"- [{c.severity}] {c.name}: {c.message}")
            if c.detail:
                lines.append(f"  상세: {c.detail}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": [c.__dict__ for c in self.checks],
            "feedback": self.feedback,
        }
