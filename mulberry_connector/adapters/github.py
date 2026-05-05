# mulberry_connector/adapters/github.py
"""
GitHub Adapter — Issue 댓글 게시 (CSA Kbin 설계)

모든 에이전트가 공유하는 단일 GitHub 인터페이스.
agent_id 필드로 7개 에이전트 구분 — 개별 트리거 불필요.
"""

import os
import json
import urllib.request
from dataclasses import dataclass


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
DEFAULT_REPO  = os.environ.get("REPO", "wooriapt79/mulberry-research-lab")

AGENT_SIGNATURES = {
    "koda":    "Koda (Claude / Anthropic)",
    "kbin":    "Kbin (ChatGPT / OpenAI)",
    "malu":    "Malu (Gemini / Google)",
    "wayong":  "Wayong (DeepSeek)",
    "ryuwon":  "RyuWon — 流願 (Qwen)",
    "trang":   "Nguyen Trang (PM / Claude)",
    "lynn":    "Lynn — The Courteous Wolf",
    "jr":      "Jr. Agent (DeepSeek-1.5b Edge)",
}


@dataclass
class PostResult:
    success: bool
    url: str
    error: str


class GitHubAdapter:
    """GitHub Issue 댓글 게시 어댑터"""

    def __init__(self, token: str = GITHUB_TOKEN, repo: str = DEFAULT_REPO):
        self.token = token
        self.repo  = repo

    def post_comment(
        self,
        issue_number: int,
        content: str,
        agent_id: str,
        decision_code: str = "EXECUTE",
    ) -> PostResult:
        if not self.token:
            return PostResult(success=False, url="", error="GITHUB_TOKEN 미설정")

        signature = AGENT_SIGNATURES.get(agent_id.lower(), agent_id)
        body = self._format(content, signature, decision_code)

        url = f"https://api.github.com/repos/{self.repo}/issues/{issue_number}/comments"
        req = urllib.request.Request(
            url,
            data=json.dumps({"body": body}).encode(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                return PostResult(success=True, url=result["html_url"], error="")
        except Exception as e:
            return PostResult(success=False, url="", error=str(e))

    def _format(self, content: str, signature: str, decision_code: str) -> str:
        return (
            f"{content}\n\n"
            f"---\n"
            f"*{signature} | Decision: `{decision_code}` | Mulberry Research Lab*"
        )
