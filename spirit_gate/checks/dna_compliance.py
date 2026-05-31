"""
spirit_gate/checks/dna_compliance.py — Mulberry DNA 정합성 검증
코드가 Mulberry 헌법·원칙을 따르는지 확인
작성: Koda CTO · 2026-05-31
"""
import re
from pathlib import Path
from ..gate_result import CheckResult


def check_mulberry_signature(code: str) -> CheckResult:
    """Mulberry 팀 서명 포함 여부"""
    if "Mulberry" in code or "Koda" in code or "mulberry" in code.lower():
        return CheckResult(
            name="team_signature", passed=True,
            severity="INFO", message="Mulberry 팀 서명 확인"
        )
    return CheckResult(
        name="team_signature",
        passed=False,
        severity="WARN",
        message="Mulberry 팀 서명 없음",
        detail="파일 상단에 # Mulberry · Koda Coding Team · {date} 추가 필요",
    )


def check_language_compliance(code: str, expected_lang: str = "python") -> CheckResult:
    """설정된 언어 기준 준수 여부"""
    if expected_lang == "python":
        # Python 파일인지 확인 (기본 패턴)
        python_indicators = ["def ", "import ", "from ", "class ", "if __name__"]
        if any(ind in code for ind in python_indicators):
            return CheckResult(
                name="language_compliance", passed=True,
                severity="INFO", message=f"언어 기준 준수: {expected_lang}"
            )
    return CheckResult(
        name="language_compliance",
        passed=False,
        severity="FAIL",
        message=f"언어 기준 미준수: {expected_lang} 아님",
    )


def check_human_first_principle(code: str) -> CheckResult:
    """
    장승배기 정신 — 사람을 위한 코드인가.
    자동화 코드가 인간의 개입 없이 파괴적 행동을 하지 않는지 확인.
    """
    destructive_patterns = [
        r'\bos\.remove\b', r'\bshutil\.rmtree\b',
        r'\bDROP\s+TABLE\b', r'\bDELETE\s+FROM\b',
        r'\bformat\s*\(\s*["\']C:', r'\brmdir\b',
    ]
    found = [p for p in destructive_patterns if re.search(p, code, re.IGNORECASE)]
    if found:
        return CheckResult(
            name="human_first_principle",
            passed=False,
            severity="BLOCK",
            message="파괴적 작업 감지 — 인간 승인 없이 실행 불가",
            detail=f"패턴 {len(found)}개: PM 승인 후 수동 실행 필요",
        )
    return CheckResult(
        name="human_first_principle", passed=True,
        severity="INFO", message="장승배기 정신 준수 — 안전한 코드"
    )
