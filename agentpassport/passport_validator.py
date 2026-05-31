#!/usr/bin/env python3
"""
agentpassport/passport_validator.py — MAPA-A1 패스포트 유효성 검사
==================================================================
패스포트 변경 시 자동 검증 + 실패 시 GitHub 이슈 생성.

검증 항목:
  1. MAPA-A1-Standard 필수 필드 존재 여부
  2. steward_alignment 필드 설정 여부
  3. Spirit Gate 임계값 범위 (0.0~1.0)
  4. integrity_signature.declaration 비어있지 않은지
  5. L4 도구 위치 (prohibited 또는 human_required)

사용법:
  python passport_validator.py                  # 전체 검증
  python passport_validator.py --agent kbin_csa # 특정 에이전트
  python passport_validator.py --fix            # 수정 가이드 출력

설계: Trang Manager 지시 · 구현: Koda CTO · 2026-06-01
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE       = Path(__file__).parent
AGENTS_DIR = BASE / "agents"
STANDARD   = BASE / "MAPA-A1-Standard.yaml"
REPO       = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
GH_TOKEN   = os.getenv("GITHUB_TOKEN", "")

L4_TOOLS = ["deploy_production", "financial_transaction", "legal_binding_action"]


@dataclass
class ValidationResult:
    agent_id: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.agent_id}: {'VALID' if self.passed else f'INVALID ({len(self.errors)}개 오류)'}"


def validate_passport(yaml_path: Path) -> ValidationResult:
    """단일 패스포트 파일 검증"""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    agent_id = data.get("metadata", {}).get("agent_id", yaml_path.stem)
    errors, warnings = [], []

    # 1. schema_version
    if data.get("schema_version") != "MAPA-A1":
        errors.append("schema_version이 'MAPA-A1'이 아님")

    # 2. 필수 메타데이터
    meta = data.get("metadata", {})
    for field_name in ["agent_id", "formal_name", "role", "steward_alignment"]:
        if not meta.get(field_name):
            errors.append(f"metadata.{field_name} 누락")

    # 3. steward_alignment 설정 여부
    if meta.get("steward_alignment") == "":
        errors.append("steward_alignment 비어있음 — CEO re.eul 설정 필요")

    # 4. tool_governance_matrix 존재
    matrix = data.get("tool_governance_matrix", {})
    if not matrix:
        errors.append("tool_governance_matrix 누락")

    # 5. Spirit Gate 임계값
    gate = data.get("gate_alignment", {}).get("spirit_gate", {})
    threshold = gate.get("min_score_threshold")
    if threshold is not None:
        if not (0.0 <= float(threshold) <= 1.0):
            errors.append(f"spirit_gate.min_score_threshold 범위 오류: {threshold}")
    else:
        warnings.append("spirit_gate.min_score_threshold 미설정 — 기본값 0.85 적용")

    # 6. integrity_signature.declaration
    declaration = data.get("integrity_signature", {}).get("declaration", "")
    if not declaration.strip():
        errors.append("integrity_signature.declaration 비어있음")

    # 7. L4 도구 위치 확인
    allowed = matrix.get("autonomous_processing_zone", {}).get("allowed_tools", [])
    for l4_tool in L4_TOOLS:
        if l4_tool in allowed:
            errors.append(f"L4 도구 '{l4_tool}'이 autonomous_zone에 있음 — prohibited 또는 human_required로 이동 필요")

    return ValidationResult(
        agent_id=agent_id,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_all() -> List[ValidationResult]:
    results = []
    if not AGENTS_DIR.exists():
        print("❌ agents/ 디렉토리 없음")
        return results
    for f in sorted(AGENTS_DIR.glob("*_passport.yaml")):
        result = validate_passport(f)
        results.append(result)
        print(result.summary())
        for e in result.errors:
            print(f"    ❌ {e}")
        for w in result.warnings:
            print(f"    ⚠️  {w}")
    return results


def create_github_issue(failed: List[ValidationResult]):
    """검증 실패 시 GitHub 이슈 자동 생성"""
    if not GH_TOKEN or not failed:
        return

    body_lines = ["## 🛂 패스포트 유효성 검사 실패\n"]
    for r in failed:
        body_lines.append(f"### ❌ {r.agent_id}")
        for e in r.errors:
            body_lines.append(f"- {e}")
        body_lines.append("")

    body_lines += [
        "---",
        "담당: Koda CTO + 해당 에이전트",
        "기준: MAPA-A1-Standard.yaml",
        f"*자동 생성: passport_validator.py*"
    ]

    payload = json.dumps({
        "title": f"🛂 [패스포트 오류] {len(failed)}개 에이전트 MAPA-A1 검증 실패",
        "body": "\n".join(body_lines),
        "labels": ["passport", "validation-error"],
    }).encode("utf-8")

    url = f"https://api.github.com/repos/{REPO}/issues"
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"token {GH_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"\n📋 검증 실패 이슈 생성: #{result.get('number')} {result.get('html_url')}")
    except Exception as e:
        print(f"이슈 생성 실패: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MAPA-A1 패스포트 유효성 검사")
    parser.add_argument("--agent", help="특정 에이전트 ID 검사")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  🛂 MAPA-A1 패스포트 유효성 검사")
    print(f"{'='*55}\n")

    if args.agent:
        target = AGENTS_DIR / f"{args.agent}_passport.yaml"
        if not target.exists():
            # agent_id 기반으로 찾기
            for f in AGENTS_DIR.glob("*_passport.yaml"):
                data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                if data.get("metadata", {}).get("agent_id") == args.agent:
                    target = f
                    break
        if target.exists():
            result = validate_passport(target)
            print(result.summary())
            for e in result.errors:
                print(f"  ❌ {e}")
        else:
            print(f"패스포트 파일 없음: {args.agent}")
    else:
        results = validate_all()
        failed = [r for r in results if not r.passed]
        total = len(results)
        passed = total - len(failed)

        print(f"\n{'='*55}")
        print(f"  결과: {passed}/{total} 통과")
        if failed:
            print(f"  실패: {len(failed)}개")
            create_github_issue(failed)
        else:
            print(f"  ✅ 전체 VALID")
        print(f"{'='*55}\n")

    sys.exit(0)
