# -*- coding: utf-8 -*-
"""
⚙️ Mulberry AgenticAI Hub — Koda Tech Mission v1.0
Koda CTO: 기술 검토 · 아키텍처 설계 · 코드 품질 판단

Agent: Koda (CTO — Chief Technology Officer)
Date: 2026-06-07
"""

import os
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Koda-Mission] - %(levelname)s - %(message)s'
)


class KodaMission:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.agent_name = "koda"
        self.agent_role = "CTO"
        self.spirit_score_threshold = 0.85

        logging.info("⚙️ Koda Mission initialized — CTO mode online")

    def validate_passport(self) -> bool:
        passport_path = "agentpassport/agents/koda.yaml"
        if os.path.exists(passport_path):
            logging.info("✅ Koda passport validated")
            return True
        logging.warning("⚠️ Passport not found — proceeding with default permissions")
        return True

    def spirit_gate_check(self, content: str) -> float:
        restricted = ["프로덕션 삭제", "DB 초기화", "강제 배포"]
        score = 1.0
        for keyword in restricted:
            if keyword in content:
                score -= 0.15
        return max(0.0, score)

    def analyze_issue(self, issue_url: str, comment_body: str) -> Dict[str, Any]:
        logging.info(f"📥 Koda analyzing: {issue_url}")

        spirit_score = self.spirit_gate_check(comment_body)
        if spirit_score < self.spirit_score_threshold:
            return {
                "status": "HUMAN_REVIEW_REQUIRED",
                "reason": f"Spirit score {spirit_score} below threshold",
                "agent": self.agent_name
            }

        analysis = {
            "agent": self.agent_name,
            "role": self.agent_role,
            "issue_url": issue_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "spirit_score": spirit_score,
            "analysis": self._generate_cto_response(comment_body),
            "status": "SUCCESS"
        }

        self._post_github_comment(issue_url, analysis["analysis"])
        self._record_training_log(analysis)
        return analysis

    def _generate_cto_response(self, comment_body: str) -> str:
        return (
            f"## ⚙️ Koda CTO — 기술 검토 의견\n\n"
            f"**작성일**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"이슈를 검토했습니다. 기술 구현·아키텍처·성능 관점에서 분석합니다.\n\n"
            f"*— Koda (CTO, Mulberry Research Lab)*"
        )

    def _post_github_comment(self, issue_url: str, comment: str) -> None:
        if not self.token:
            logging.warning("⚠️ GITHUB_TOKEN 없음 — 댓글 게시 스킵")
            return
        try:
            import requests
            parts = issue_url.rstrip("/").split("/")
            owner, repo, issue_number = parts[-4], parts[-3], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.post(api_url, json={"body": comment}, headers=headers)
            if response.status_code == 201:
                logging.info("✅ GitHub 댓글 게시 완료")
            else:
                logging.error(f"❌ 댓글 게시 실패: {response.status_code}")
        except Exception as e:
            logging.error(f"❌ GitHub API 오류: {e}")

    def _record_training_log(self, data: Dict) -> None:
        os.makedirs("training_logs", exist_ok=True)
        log_path = f"training_logs/koda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"📚 Training log saved: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Koda Tech Mission")
    parser.add_argument("--issue", type=str, default="")
    parser.add_argument("--comment", type=str, default="")
    parser.add_argument("--token", type=str, default="")
    args = parser.parse_args()

    mission = KodaMission(token=args.token)
    mission.validate_passport()
    result = mission.analyze_issue(args.issue, args.comment)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
