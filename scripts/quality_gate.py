#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quality_gate.py — Mulberry 위생코드 5단계 / Stage 2
====================================================
역할: 코드 품질 검사
  - validate_registry.py 연동 (tool_registry 검증)
  - 에이전트 Passport 파일 존재 여부 확인
  - mission.py 필수 클래스·메서드 구조 검사
  - training_logs 디렉토리 존재 여부 확인

사용법:
  python scripts/quality_gate.py
  python scripts/quality_gate.py --strict

종료 코드:
  0 — PASS
  1 — FAIL

CTO Koda · 2026-06-07
"""

from __future__ import annotations

import ast
import sys
import os
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [QualityGate] - %(levelname)s - %(message)s'
)

ROOT = Path(__file__).parent.parent

AGENTS = ["kbin", "koda", "malu", "ryuwon", "trang", "lynn", "wayong", "baekya"]

REQUIRED_METHODS = [
    "validate_passport", "spirit_gate_check",
    "analyze_issue", "_post_github_comment", "_record_training_log"
]


class QualityGate:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_mission_structure(self) -> bool:
        """각 *_mission.py 의 필수 클래스·메서드 존재 여부 확인"""
        scripts_dir = ROOT / "scripts"
        all_ok = True
        for agent in AGENTS:
            fp = scripts_dir / f"{agent}_mission.py"
            if not fp.exists():
                self.errors.append(f"❌ 파일 없음: {fp.name}")
                all_ok = False
                continue
            try:
                tree = ast.parse(fp.read_text(encoding="utf-8"))
                methods = {
                    node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                missing = [m for m in REQUIRED_METHODS if m not in methods]
                if missing:
                    self.warnings.append(f"⚠️ [{agent}_mission.py] 누락 메서드: {missing}")
                    logging.warning(f"⚠️ [{agent}_mission.py] 누락: {missing}")
                else:
                    logging.info(f"✅ 구조 OK: {agent}_mission.py")
            except Exception as e:
                self.errors.append(f"Parse Error [{fp.name}]: {e}")
                all_ok = False
        return all_ok

    def check_passports(self) -> bool:
        """agentpassport/agents/{agent}.yaml 존재 여부"""
        passport_dir = ROOT / "agentpassport" / "agents"
        if not passport_dir.exists():
            self.warnings.append("⚠️ agentpassport/agents/ 디렉토리 없음 — 스킵")
            logging.warning("⚠️ passport 디렉토리 없음 — 스킵")
            return True
        for agent in AGENTS:
            fp = passport_dir / f"{agent}.yaml"
            if not fp.exists():
                self.warnings.append(f"⚠️ Passport 없음: {agent}.yaml")
                logging.warning(f"⚠️ Passport 없음: {agent}.yaml")
            else:
                logging.info(f"✅ Passport OK: {agent}.yaml")
        return True

    def check_training_logs_dir(self) -> bool:
        """training_logs/ 디렉토리 존재 여부"""
        logs_dir = ROOT / "training_logs"
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            logging.info("📁 training_logs/ 디렉토리 생성")
        else:
            logging.info("✅ training_logs/ 확인")
        return True

    def check_tool_registry(self) -> bool:
        """validate_registry.py 연동 실행"""
        validator = ROOT / "scripts" / "validate_registry.py"
        if not validator.exists():
            self.warnings.append("⚠️ validate_registry.py 없음 — 스킵")
            return True
        try:
            result = subprocess.run(
                [sys.executable, str(validator), "--summary"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logging.info("✅ Tool Registry 검증 통과")
            else:
                self.warnings.append(f"⚠️ Tool Registry 경고: {result.stdout[:200]}")
                logging.warning("⚠️ Tool Registry 경고 있음")
        except Exception as e:
            self.warnings.append(f"⚠️ Registry 검증 실행 오류: {e}")
        return True

    def run(self) -> Dict[str, Any]:
        logging.info("🔬 Quality Gate 시작")

        self.check_mission_structure()
        self.check_passports()
        self.check_training_logs_dir()
        self.check_tool_registry()

        has_errors = len(self.errors) > 0
        has_warnings = len(self.warnings) > 0
        status = "FAIL" if has_errors or (self.strict and has_warnings) else "PASS"

        result = {
            "stage": "quality_gate",
            "status": status,
            "errors": self.errors,
            "warnings": self.warnings,
            "strict_mode": self.strict,
        }
        logging.info(f"{'✅' if status == 'PASS' else '❌'} Quality Gate: {status}")
        return result


def main():
    parser = argparse.ArgumentParser(description="Mulberry Quality Gate — Stage 2")
    parser.add_argument("--strict", action="store_true", help="경고도 FAIL 처리")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    gate = QualityGate(strict=args.strict)
    result = gate.run()

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
