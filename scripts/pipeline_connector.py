#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_connector.py — Mulberry 위생코드 5단계 파이프라인 엔진
=============================================================
역할: 5단계 순차 실행 오케스트레이터

Stage 1: Script Gate  → 문법·구조 검증
Stage 2: Quality Gate → 코드 품질 검사
Stage 3: Spirit Gate  → 윤리 검증 (score >= 0.85)
Stage 4: [Colab]      → 실행 테스트 (선택, CI에서는 스킵)
Stage 5: Deploy       → 배포 준비 완료 신호

- 단계별 실패 시 즉시 중단 + GitHub Issue 댓글 에러 리포트
- 전체 통과 시 training_logs 기록 + PASS 신호

사용법:
  python scripts/pipeline_connector.py --agent kbin --issue-url <url>
  python scripts/pipeline_connector.py --all --issue-url <url>

환경변수:
  GITHUB_TOKEN

CTO Koda · 2026-06-07
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Pipeline] - %(levelname)s - %(message)s'
)

ROOT   = Path(__file__).parent.parent
REPO   = "wooriapt79/mulberry-research-lab"
AGENTS = ["kbin", "koda", "malu", "ryuwon", "trang", "lynn", "wayong", "baekya"]

# .env.local / .env.railway 로드
for env_file in [ROOT / ".env.local", ROOT / ".env.railway"]:
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


class PipelineConnector:
    def __init__(self, issue_url: str = "", token: str = ""):
        self.issue_url = issue_url
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.results: List[Dict[str, Any]] = []
        self.stage_num = 0

    # ── Stage 실행 헬퍼 ───────────────────────────────────────

    def _run_stage(self, name: str, func) -> Dict[str, Any]:
        self.stage_num += 1
        logging.info(f"▶ Stage {self.stage_num}: {name}")
        try:
            result = func()
            result["stage_num"] = self.stage_num
            self.results.append(result)
            if result.get("status") == "FAIL":
                logging.error(f"❌ Stage {self.stage_num} [{name}] FAIL")
            else:
                logging.info(f"✅ Stage {self.stage_num} [{name}] PASS")
            return result
        except Exception as e:
            err = {"stage": name, "stage_num": self.stage_num, "status": "FAIL", "error": str(e)}
            self.results.append(err)
            logging.error(f"❌ Stage {self.stage_num} [{name}] 예외: {e}")
            return err

    # ── Stage 1: Script Gate ──────────────────────────────────

    def stage1_script_gate(self) -> Dict[str, Any]:
        from scripts.script_gate import ScriptGate
        gate = ScriptGate()
        return gate.run(str(ROOT / "scripts"))

    # ── Stage 2: Quality Gate ─────────────────────────────────

    def stage2_quality_gate(self) -> Dict[str, Any]:
        from scripts.quality_gate import QualityGate
        gate = QualityGate()
        return gate.run()

    # ── Stage 3: Spirit Gate ──────────────────────────────────

    def stage3_spirit_gate(self) -> Dict[str, Any]:
        from scripts.spirit_gate import SpiritGate
        # mission.py 파일들 전체 내용 합산 검증
        content = ""
        for agent in AGENTS:
            fp = ROOT / "scripts" / f"{agent}_mission.py"
            if fp.exists():
                content += fp.read_text(encoding="utf-8") + "\n"
        gate = SpiritGate()
        return gate.run(content, source="all_mission_files")

    # ── Stage 4: Colab Test (선택) ────────────────────────────

    def stage4_colab_test(self) -> Dict[str, Any]:
        logging.info("⏩ Stage 4 (Colab) — CI 환경 스킵")
        return {"stage": "colab_test", "status": "SKIP", "reason": "CI 환경 선택 스킵"}

    # ── Stage 5: Deploy Ready ─────────────────────────────────

    def stage5_deploy_ready(self) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        log = {
            "stage": "deploy_ready",
            "status": "PASS",
            "timestamp": ts,
            "pipeline_results": self.results,
            "message": "위생코드 5단계 통과 — 배포 준비 완료"
        }
        logs_dir = ROOT / "training_logs"
        logs_dir.mkdir(exist_ok=True)
        fp = logs_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fp.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
        logging.info(f"📚 Pipeline 최종 로그 저장: {fp.name}")
        return log

    # ── GitHub 댓글 게시 ──────────────────────────────────────

    def _post_comment(self, body: str) -> None:
        if not self.token or not self.issue_url:
            logging.warning("⚠️ TOKEN 또는 issue_url 없음 — 댓글 스킵")
            return
        try:
            parts = self.issue_url.rstrip("/").split("/")
            issue_number = parts[-1]
            url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
            data = json.dumps({"body": body}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                if resp.status == 201:
                    logging.info("✅ GitHub 댓글 게시 완료")
        except Exception as e:
            logging.error(f"❌ GitHub 댓글 게시 실패: {e}")

    def _build_report_comment(self, final_status: str) -> str:
        icon = "✅" if final_status == "PASS" else "❌"
        lines = [
            f"## {icon} Mulberry 위생코드 5단계 파이프라인 결과\n",
            f"**상태**: `{final_status}`  ",
            f"**시각**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
            "| 단계 | 이름 | 결과 |",
            "|------|------|------|",
        ]
        stage_names = {
            "script_gate": "Stage 1 — Script Gate",
            "quality_gate": "Stage 2 — Quality Gate",
            "spirit_gate": "Stage 3 — Spirit Gate",
            "colab_test": "Stage 4 — Colab Test",
            "deploy_ready": "Stage 5 — Deploy Ready",
        }
        for r in self.results:
            stage = r.get("stage", "unknown")
            status = r.get("status", "?")
            icon2 = "✅" if status == "PASS" else ("⏩" if status == "SKIP" else "❌")
            lines.append(f"| {r.get('stage_num','?')} | {stage_names.get(stage, stage)} | {icon2} {status} |")

        if final_status == "FAIL":
            lines.append("\n⚠️ **Human Review Required** — @KODA @Kbin @TRANG")
        else:
            lines.append("\n🚀 **모든 단계 통과 — 배포 준비 완료**")

        lines.append(f"\n*— CTO Koda (pipeline_connector v1.0)*")
        return "\n".join(lines)

    # ── 전체 파이프라인 실행 ──────────────────────────────────

    def run(self) -> Dict[str, Any]:
        logging.info("🚀 Mulberry 위생코드 5단계 파이프라인 시작")

        stages = [
            ("script_gate",  self.stage1_script_gate),
            ("quality_gate", self.stage2_quality_gate),
            ("spirit_gate",  self.stage3_spirit_gate),
            ("colab_test",   self.stage4_colab_test),
            ("deploy_ready", self.stage5_deploy_ready),
        ]

        final_status = "PASS"
        for name, func in stages:
            result = self._run_stage(name, func)
            if result.get("status") == "FAIL":
                final_status = "FAIL"
                logging.error(f"🛑 파이프라인 중단 — {name} FAIL")
                break

        comment = self._build_report_comment(final_status)
        self._post_comment(comment)

        return {
            "pipeline_status": final_status,
            "stages_run": len(self.results),
            "results": self.results,
        }


def main():
    parser = argparse.ArgumentParser(description="Mulberry Pipeline Connector — 5단계 엔진")
    parser.add_argument("--issue-url", type=str, default="", help="GitHub Issue URL")
    parser.add_argument("--token", type=str, default="")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    connector = PipelineConnector(
        issue_url=args.issue_url,
        token=args.token
    )
    result = connector.run()

    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    sys.exit(0 if result["pipeline_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
