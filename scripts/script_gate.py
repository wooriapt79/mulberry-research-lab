#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script_gate.py — Mulberry 위생코드 5단계 / Stage 1
===================================================
역할: Python 코드 문법·구조 검증
  - ast.parse 기반 문법 오류 감지
  - 금지 모듈 import 검사 (보안)
  - 필수 함수(main) 존재 여부 확인

사용법:
  python scripts/script_gate.py --dir scripts
  python scripts/script_gate.py --file scripts/kbin_mission.py

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
from pathlib import Path
from typing import Dict, List, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ScriptGate] - %(levelname)s - %(message)s'
)

FORBIDDEN_IMPORTS = [
    "subprocess", "pickle", "shelve", "ctypes",
    "socket", "pty", "telnetlib"
]

MISSION_FILES = [
    "kbin_mission.py", "koda_mission.py", "malu_mission.py",
    "ryuwon_mission.py", "trang_mission.py", "lynn_mission.py",
    "wayong_mission.py", "baekya_mission.py"
]


class ScriptGate:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_syntax(self, filepath: Path) -> bool:
        try:
            ast.parse(filepath.read_text(encoding="utf-8"))
            logging.info(f"✅ 문법 OK: {filepath.name}")
            return True
        except SyntaxError as e:
            self.errors.append(f"SyntaxError [{filepath.name}]: {e}")
            logging.error(f"❌ 문법 오류 [{filepath.name}]: {e}")
            return False

    def check_forbidden_imports(self, filepath: Path) -> bool:
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                module = ""
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                if module and any(f in module for f in FORBIDDEN_IMPORTS):
                    self.warnings.append(f"⚠️ 금지 모듈 [{filepath.name}]: {module}")
                    logging.warning(f"⚠️ 금지 모듈 감지 [{filepath.name}]: {module}")
            return True
        except Exception as e:
            self.errors.append(f"ImportCheck [{filepath.name}]: {e}")
            return False

    def check_required_functions(self, filepath: Path) -> bool:
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"))
            defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            if "main" not in defined:
                self.warnings.append(f"⚠️ main() 없음: {filepath.name}")
                logging.warning(f"⚠️ main() 누락: {filepath.name}")
            else:
                logging.info(f"✅ main() 확인: {filepath.name}")
            return True
        except Exception as e:
            self.errors.append(f"FunctionCheck [{filepath.name}]: {e}")
            return False

    def run(self, target: str = "scripts") -> Dict[str, Any]:
        logging.info(f"🔍 Script Gate 시작 — 대상: {target}")
        passed, failed = [], []

        target_path = Path(target)
        if target_path.is_file():
            files = [target_path]
        else:
            files = [target_path / f for f in MISSION_FILES if (target_path / f).exists()]

        if not files:
            logging.warning("⚠️ 검사할 mission 파일 없음")

        for fp in files:
            ok = (self.check_syntax(fp) and
                  self.check_forbidden_imports(fp) and
                  self.check_required_functions(fp))
            (passed if ok else failed).append(str(fp))

        result = {
            "stage": "script_gate",
            "status": "PASS" if not failed else "FAIL",
            "passed": len(passed),
            "failed": len(failed),
            "files_passed": passed,
            "files_failed": failed,
            "errors": self.errors,
            "warnings": self.warnings,
        }
        logging.info(f"{'✅' if result['status'] == 'PASS' else '❌'} Script Gate: {result['status']} ({len(passed)}/{len(passed)+len(failed)})")
        return result


def main():
    parser = argparse.ArgumentParser(description="Mulberry Script Gate — Stage 1")
    parser.add_argument("--dir", type=str, default="scripts")
    parser.add_argument("--file", type=str, default="")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    gate = ScriptGate()
    result = gate.run(args.file if args.file else args.dir)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
