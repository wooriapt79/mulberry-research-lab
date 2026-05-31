"""
spirit_gate/checks/hallucination.py — 할루시네이션 코드 패턴 감지
LLM이 존재하지 않는 라이브러리·함수를 사용한 경우 탐지
작성: Koda CTO · 2026-05-31
"""
import re
from ..gate_result import CheckResult

# 실제로 존재하지 않는 가상 라이브러리 패턴 (LLM 흔한 실수)
FAKE_LIBRARIES = [
    "import mulberry_sdk",
    "import railway_client",
    "from fastapi import AutoRouter",
    "from pydantic import AutoModel",
    "import ai_helper",
    "from anthropic import magic",
]

# 존재하지 않는 메서드 패턴
SUSPICIOUS_PATTERNS = [
    r'\.auto_generate\(\)',
    r'\.magic_deploy\(\)',
    r'AI\.solve\(',
    r'llm\.auto_fix\(',
]


def check_hallucination_patterns(code: str) -> CheckResult:
    """가짜 라이브러리 및 존재하지 않는 API 사용 감지"""
    found = []

    for fake_lib in FAKE_LIBRARIES:
        if fake_lib in code:
            found.append(f"가짜 라이브러리: {fake_lib}")

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, code):
            found.append(f"의심 패턴: {pattern}")

    if found:
        return CheckResult(
            name="hallucination_check",
            passed=False,
            severity="FAIL",
            message=f"할루시네이션 패턴 {len(found)}개 감지",
            detail="; ".join(found),
        )
    return CheckResult(
        name="hallucination_check", passed=True,
        severity="INFO", message="할루시네이션 패턴 없음"
    )
