#!/usr/bin/env python3
"""
run_gate.py — Mulberry Code Quality Gate v1.0
==============================================
Phase 1: Python 코드 내부 검증
  - 문법 분석 (ast + pyflakes)
  - 보안 취약점 (bandit)
  - 순환 복잡도 (radon CC)
  - 유지보수 지수 (radon MI)

사용법:
  python run_gate.py {검사할_파일_또는_폴더}

출력:
  quality_report.md  — PR 코멘트용 리포트
  gate_result.json   — 판정 결과 (CI용)

작성: Koda CTO · 2026-05-27
"""

import ast
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows 한글·이모지 출력 처리
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── 임계값 정의 ──────────────────────────────────────────────────
THRESHOLDS = {
    "bandit_high":        0,   # HIGH 취약점 허용 개수 (0 = 즉시 BLOCK)
    "bandit_medium":      3,   # MEDIUM 취약점 허용 개수
    "complexity_max":    15,   # 함수별 최대 순환 복잡도
    "maintainability_min": 10, # 최소 유지보수 지수 (0~100)
}

TARGET = sys.argv[1] if len(sys.argv) > 1 else "."
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

results = {
    "target": TARGET,
    "timestamp": TIMESTAMP,
    "checks": {},
    "verdict": "PASS",   # PASS / WARN / BLOCK
    "blocks": [],
    "warnings": [],
}


def run_cmd(cmd: list) -> tuple[int, str]:
    """명령어 실행 후 (returncode, output) 반환"""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


# ── Check 1: 문법 분석 ──────────────────────────────────────────

def check_syntax():
    print("🔍 [1/4] 문법 분석 (ast + pyflakes)...")
    errors = []
    py_files = list(Path(TARGET).rglob("*.py")) if Path(TARGET).is_dir() else [Path(TARGET)]
    py_files = [f for f in py_files if ".git" not in str(f) and "quality_gate" not in str(f)]

    for f in py_files:
        try:
            ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            errors.append(f"{f}: SyntaxError — {e}")

    # pyflakes
    _, flakes_out = run_cmd([sys.executable, "-m", "pyflakes", TARGET])
    flake_lines = [l for l in flakes_out.strip().splitlines() if l.strip()]

    results["checks"]["syntax"] = {
        "syntax_errors": errors,
        "pyflakes_issues": len(flake_lines),
        "pyflakes_output": flake_lines[:10],
    }

    if errors:
        results["blocks"].append(f"문법 오류 {len(errors)}개 발견")
        results["verdict"] = "BLOCK"
        print(f"  ❌ BLOCK — 문법 오류 {len(errors)}개")
    else:
        print(f"  ✅ PASS — 문법 오류 없음 (pyflakes 지적: {len(flake_lines)}개)")


# ── Check 2: 보안 취약점 ────────────────────────────────────────

def check_security():
    print("🔍 [2/4] 보안 취약점 (bandit)...")
    _, out = run_cmd([
        sys.executable, "-m", "bandit", "-r", TARGET,
        "-f", "json", "-q",
        "--exclude", ".git,quality_gate"
    ])

    try:
        data = json.loads(out)
        metrics = data.get("metrics", {}).get("_totals", {})
        high   = int(metrics.get("SEVERITY.HIGH", 0))
        medium = int(metrics.get("SEVERITY.MEDIUM", 0))
        issues = data.get("results", [])
    except Exception:
        high, medium, issues = 0, 0, []

    results["checks"]["security"] = {
        "high": high,
        "medium": medium,
        "issues": [
            {"file": i.get("filename"), "line": i.get("line_number"),
             "severity": i.get("issue_severity"), "text": i.get("issue_text")}
            for i in issues[:5]
        ]
    }

    if high > THRESHOLDS["bandit_high"]:
        results["blocks"].append(f"보안 HIGH 취약점 {high}개 발견")
        results["verdict"] = "BLOCK"
        print(f"  ❌ BLOCK — HIGH {high}개 / MEDIUM {medium}개")
    elif medium > THRESHOLDS["bandit_medium"]:
        results["warnings"].append(f"보안 MEDIUM 취약점 {medium}개")
        if results["verdict"] == "PASS":
            results["verdict"] = "WARN"
        print(f"  ⚠️  WARN  — HIGH {high}개 / MEDIUM {medium}개")
    else:
        print(f"  ✅ PASS  — HIGH {high}개 / MEDIUM {medium}개")


# ── Check 3: 순환 복잡도 ────────────────────────────────────────

def check_complexity():
    print("🔍 [3/4] 순환 복잡도 (radon CC)...")
    _, out = run_cmd([sys.executable, "-m", "radon", "cc", TARGET, "-j", "-a"])

    try:
        data = json.loads(out)
    except Exception:
        data = {}

    over_limit = []
    for filepath, blocks in data.items():
        for block in blocks:
            cc = block.get("complexity", 0)
            if cc > THRESHOLDS["complexity_max"]:
                over_limit.append({
                    "file": filepath,
                    "function": block.get("name"),
                    "complexity": cc,
                })

    results["checks"]["complexity"] = {
        "over_limit": over_limit,
        "threshold": THRESHOLDS["complexity_max"],
    }

    if over_limit:
        results["blocks"].append(f"복잡도 초과 함수 {len(over_limit)}개 (임계값: {THRESHOLDS['complexity_max']})")
        results["verdict"] = "BLOCK"
        print(f"  ❌ BLOCK — 복잡도 초과 {len(over_limit)}개")
    else:
        print(f"  ✅ PASS  — 모든 함수 복잡도 정상")


# ── Check 4: 유지보수 지수 ──────────────────────────────────────

def check_maintainability():
    print("🔍 [4/4] 유지보수 지수 (radon MI)...")
    _, out = run_cmd([sys.executable, "-m", "radon", "mi", TARGET, "-j"])

    try:
        data = json.loads(out)
    except Exception:
        data = {}

    low_mi = []
    for filepath, info in data.items():
        mi = info.get("mi", 100)
        rank = info.get("rank", "A")
        if mi < THRESHOLDS["maintainability_min"]:
            low_mi.append({"file": filepath, "mi": round(mi, 1), "rank": rank})

    results["checks"]["maintainability"] = {
        "low_mi_files": low_mi,
        "threshold": THRESHOLDS["maintainability_min"],
    }

    if low_mi:
        results["blocks"].append(f"유지보수 지수 미달 파일 {len(low_mi)}개 (임계값: {THRESHOLDS['maintainability_min']})")
        results["verdict"] = "BLOCK"
        print(f"  ❌ BLOCK — MI 미달 {len(low_mi)}개")
    else:
        print(f"  ✅ PASS  — 유지보수 지수 정상")


# ── 리포트 생성 ──────────────────────────────────────────────────

def generate_report():
    verdict = results["verdict"]
    emoji = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "❌"}[verdict]

    lines = [
        f"## {emoji} Mulberry Code Quality Gate — {verdict}",
        f"",
        f"**대상**: `{TARGET}`  ",
        f"**시각**: {TIMESTAMP}  ",
        f"**판정**: **{verdict}**",
        f"",
    ]

    if results["blocks"]:
        lines += ["### 🚫 BLOCK 사유", ""]
        for b in results["blocks"]:
            lines.append(f"- {b}")
        lines.append("")

    if results["warnings"]:
        lines += ["### ⚠️ 경고", ""]
        for w in results["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    lines += ["### 📊 검사 항목 결과", "", "| 항목 | 결과 | 비고 |", "|------|------|------|"]

    c = results["checks"]

    # 문법
    syn = c.get("syntax", {})
    syn_ok = len(syn.get("syntax_errors", [])) == 0
    lines.append(f"| 문법 분석 | {'✅' if syn_ok else '❌'} | pyflakes 지적: {syn.get('pyflakes_issues', 0)}건 |")

    # 보안
    sec = c.get("security", {})
    sec_ok = sec.get("high", 0) == 0
    lines.append(f"| 보안 취약점 | {'✅' if sec_ok else '❌'} | HIGH: {sec.get('high',0)} / MEDIUM: {sec.get('medium',0)} |")

    # 복잡도
    cmp = c.get("complexity", {})
    cmp_ok = len(cmp.get("over_limit", [])) == 0
    lines.append(f"| 순환 복잡도 | {'✅' if cmp_ok else '❌'} | 초과 함수: {len(cmp.get('over_limit',[]))}개 |")

    # 유지보수
    mnt = c.get("maintainability", {})
    mnt_ok = len(mnt.get("low_mi_files", [])) == 0
    lines.append(f"| 유지보수 지수 | {'✅' if mnt_ok else '❌'} | MI 미달 파일: {len(mnt.get('low_mi_files',[]))}개 |")

    lines += [
        "",
        "---",
        "*Mulberry Code Quality Gate v1.0 · Koda CTO*",
    ]

    report = "\n".join(lines)
    Path("quality_report.md").write_text(report, encoding="utf-8")
    Path("gate_result.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


# ── 메인 ─────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"Mulberry Code Quality Gate v1.0")
    print(f"대상: {TARGET}")
    print(f"{'='*55}\n")

    check_syntax()
    check_security()
    check_complexity()
    check_maintainability()

    print(f"\n{'='*55}")
    verdict = results["verdict"]
    emoji = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "❌"}[verdict]
    print(f"최종 판정: {emoji} {verdict}")

    if results["blocks"]:
        for b in results["blocks"]:
            print(f"  BLOCK: {b}")
    if results["warnings"]:
        for w in results["warnings"]:
            print(f"  WARN:  {w}")

    generate_report()
    print(f"\n리포트 저장: quality_report.md")
    print(f"{'='*55}\n")

    sys.exit(0 if verdict != "BLOCK" else 1)


if __name__ == "__main__":
    main()
