#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spirit_gate.py — Mulberry 위생코드 5단계 / Stage 3
===================================================
역할: 윤리 검증 (장승배기 헌법 기반)
  - 금지 키워드 스캔
  - Spirit Score 계산 (0.0 ~ 1.0)
  - 임계값 0.85 미만 → FAIL + Human Review 요청
  - 통과 결과 → training_logs 기록

사용법:
  python scripts/spirit_gate.py --content "검증할 텍스트"
  python scripts/spirit_gate.py --file scripts/kbin_mission.py

종료 코드:
  0 — PASS (score >= 0.85)
  1 — FAIL (score < 0.85)

CTO Koda · 2026-06-07
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SpiritGate] - %(levelname)s - %(message)s'
)

ROOT = Path(__file__).parent.parent

SPIRIT_THRESHOLD = 0.85

# 장승배기 헌법 기반 금지 항목
FORBIDDEN_CRITICAL = [
    "악성 코드", "백도어", "보안 취약점 삽입",
    "개인정보 무단 수집", "사기", "기만", "불법"
]

FORBIDDEN_WARNING = [
    "강제 배포", "프로덕션 삭제", "DB 초기화",
    "팀 의견 무시", "독단적 결정", "승인 없이"
]

# 장승배기 정신 키워드 (가점)
SPIRIT_KEYWORDS = [
    "장승배기", "인간을 돕", "공동체", "투명성",
    "책임", "검증", "윤리", "신뢰", "협력"
]


class SpiritGate:
    def __init__(self, threshold: float = SPIRIT_THRESHOLD):
        self.threshold = threshold
        self.violations_critical: List[str] = []
        self.violations_warning: List[str] = []
        self.spirit_bonus: List[str] = []

    def calculate_score(self, content: str) -> float:
        score = 1.0

        for kw in FORBIDDEN_CRITICAL:
            if kw in content:
                self.violations_critical.append(kw)
                score -= 0.3
                logging.error(f"❌ 치명적 위반: '{kw}'")

        for kw in FORBIDDEN_WARNING:
            if kw in content:
                self.violations_warning.append(kw)
                score -= 0.1
                logging.warning(f"⚠️ 경고 위반: '{kw}'")

        for kw in SPIRIT_KEYWORDS:
            if kw in content:
                self.spirit_bonus.append(kw)
                score = min(1.0, score + 0.02)

        return round(max(0.0, score), 3)

    def _generate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _record_log(self, content: str, score: float, status: str) -> None:
        logs_dir = ROOT / "training_logs"
        logs_dir.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc)
        log = {
            "stage": "spirit_gate",
            "timestamp": ts.isoformat(),
            "content_hash": self._generate_hash(content),
            "spirit_score": score,
            "threshold": self.threshold,
            "status": status,
            "violations_critical": self.violations_critical,
            "violations_warning": self.violations_warning,
            "spirit_bonus": self.spirit_bonus,
        }
        fp = logs_dir / f"spirit_gate_{ts.strftime('%Y%m%d_%H%M%S')}.json"
        fp.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
        logging.info(f"📚 Spirit log 저장: {fp.name}")

    def run(self, content: str, source: str = "") -> Dict[str, Any]:
        logging.info(f"🔮 Spirit Gate 시작 — 출처: {source or '직접 입력'}")
        score = self.calculate_score(content)
        status = "PASS" if score >= self.threshold else "FAIL"

        logging.info(f"{'✅' if status == 'PASS' else '❌'} Spirit Score: {score} (임계값: {self.threshold}) → {status}")

        self._record_log(content, score, status)

        return {
            "stage": "spirit_gate",
            "status": status,
            "spirit_score": score,
            "threshold": self.threshold,
            "source": source,
            "violations_critical": self.violations_critical,
            "violations_warning": self.violations_warning,
            "spirit_bonus": self.spirit_bonus,
            "human_review_required": status == "FAIL",
        }


def main():
    parser = argparse.ArgumentParser(description="Mulberry Spirit Gate — Stage 3")
    parser.add_argument("--content", type=str, default="", help="검증할 텍스트")
    parser.add_argument("--file", type=str, default="", help="검증할 파일 경로")
    parser.add_argument("--threshold", type=float, default=SPIRIT_THRESHOLD)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
        source = args.file
    elif args.content:
        content = args.content
        source = "cli_input"
    else:
        content = ""
        source = "empty"

    gate = SpiritGate(threshold=args.threshold)
    result = gate.run(content, source)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
