"""
spirit_gate/checks/security.py — 보안 검증
하드코딩된 시크릿·API 키·위험 패턴 탐지
작성: Koda CTO · 2026-05-31
"""
import re
from ..gate_result import CheckResult

# 하드코딩된 시크릿 패턴
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9_\-]{10,}["\']', "하드코딩된 API 키"),
    (r'(?i)(secret|password|passwd|token)\s*=\s*["\'][^"\']{6,}["\']', "하드코딩된 시크릿/패스워드"),
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API 키 패턴"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub PAT 패턴"),
    (r'(?i)anthropic[_-]?key\s*=\s*["\'][^"\']+["\']', "Anthropic API 키"),
]

# 위험 코드 패턴
DANGER_PATTERNS = [
    (r'\beval\s*\(', "eval() 사용 — 코드 실행 위험"),
    (r'\bexec\s*\(', "exec() 사용 — 코드 실행 위험"),
    (r'__import__\s*\(', "__import__() 동적 임포트"),
    (r'subprocess.*shell\s*=\s*True', "shell=True subprocess — 인젝션 위험"),
    (r'os\.system\s*\(', "os.system() 직접 호출"),
]


def check_hardcoded_secrets(code: str) -> CheckResult:
    found = []
    for pattern, label in SECRET_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            found.append(label)

    if found:
        return CheckResult(
            name="hardcoded_secrets",
            passed=False,
            severity="BLOCK",
            message=f"하드코딩된 시크릿 {len(found)}개 발견",
            detail=", ".join(found) + " → 환경변수로 교체 필요",
        )
    return CheckResult(
        name="hardcoded_secrets", passed=True,
        severity="INFO", message="하드코딩된 시크릿 없음"
    )


def check_dangerous_patterns(code: str) -> CheckResult:
    found = []
    for pattern, label in DANGER_PATTERNS:
        if re.search(pattern, code):
            found.append(label)

    if found:
        return CheckResult(
            name="dangerous_patterns",
            passed=False,
            severity="FAIL",
            message=f"위험 코드 패턴 {len(found)}개 발견",
            detail="; ".join(found),
        )
    return CheckResult(
        name="dangerous_patterns", passed=True,
        severity="INFO", message="위험 패턴 없음"
    )
