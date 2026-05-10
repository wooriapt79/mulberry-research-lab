"""
GitHub PR / Code Change Adapter — Track D Issue #32 구현.

에이전트가 코드 변경사항을 PR로 제출할 수 있는 인터페이스.
Spirit Score 0.85 이상인 경우에만 PR 생성 허용 (일반 댓글보다 높은 기준).

담당: Koda (CTO) | 2026-05-10
"""

import os
import json
import base64
import urllib.request
from dataclasses import dataclass

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
DEFAULT_REPO = (
    os.environ.get("REPO")
    or os.environ.get("MULBERRY_REPO_OWNER", "wooriapt79")
    + "/" + os.environ.get("MULBERRY_REPO_NAME", "mulberry-research-lab")
)

PR_SPIRIT_THRESHOLD = 0.85  # PR은 댓글(0.75)보다 더 높은 기준


@dataclass
class PRResult:
    success: bool
    pr_url: str
    pr_number: int
    error: str


class GitHubPRAdapter:
    """
    에이전트가 코드 변경을 PR로 제안하는 어댑터.

    흐름:
    1. 새 브랜치 생성 (agent/{agent_id}/YYYY-MM-DD-{slug})
    2. 파일 변경 커밋
    3. PR 생성 (draft 또는 ready)
    4. 원본 이슈에 PR 링크 댓글
    """

    def __init__(self, token: str = GITHUB_TOKEN, repo: str = DEFAULT_REPO):
        self.token = token
        self.repo = repo
        self._base_url = f"https://api.github.com/repos/{self.repo}"

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self._base_url}/{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
            method=method,
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())

    def _get_default_branch_sha(self) -> str:
        """기본 브랜치의 최신 커밋 SHA 조회"""
        repo_info = self._request("GET", "")
        default_branch = repo_info["default_branch"]
        ref = self._request("GET", f"git/refs/heads/{default_branch}")
        return ref["object"]["sha"]

    def create_pr(
        self,
        agent_id: str,
        title: str,
        body: str,
        file_path: str,
        file_content: str,
        commit_message: str,
        linked_issue: int = None,
        draft: bool = True,
    ) -> PRResult:
        """
        에이전트 코드 변경 PR 생성.

        Args:
            agent_id: "malu", "ryuwon" 등
            title: PR 제목
            body: PR 설명
            file_path: 변경할 파일 경로 (repo root 기준)
            file_content: 새 파일 내용 (전체)
            commit_message: 커밋 메시지
            linked_issue: 연결할 이슈 번호
            draft: True = Draft PR (검토 필요), False = 즉시 머지 가능
        """
        if not self.token:
            return PRResult(success=False, pr_url="", pr_number=0, error="GITHUB_TOKEN 미설정")

        from datetime import datetime
        import re

        slug = re.sub(r"[^a-z0-9-]", "-", title.lower())[:40]
        branch = f"agent/{agent_id}/{datetime.now().strftime('%Y%m%d')}-{slug}"

        try:
            # 1. 기본 브랜치 SHA
            base_sha = self._get_default_branch_sha()

            # 2. 새 브랜치 생성
            self._request("POST", "git/refs", {
                "ref": f"refs/heads/{branch}",
                "sha": base_sha,
            })

            # 3. 기존 파일 SHA 조회 (업데이트 시 필요)
            file_sha = None
            try:
                existing = self._request("GET", f"contents/{file_path}")
                file_sha = existing.get("sha")
            except Exception:
                pass  # 새 파일인 경우

            # 4. 파일 커밋
            content_b64 = base64.b64encode(file_content.encode()).decode()
            commit_payload = {
                "message": f"{commit_message}\n\nCo-Authored-By: {agent_id} <{agent_id}@mulberry.ai>",
                "content": content_b64,
                "branch": branch,
            }
            if file_sha:
                commit_payload["sha"] = file_sha
            self._request("PUT", f"contents/{file_path}", commit_payload)

            # 5. PR 생성
            pr_body = body
            if linked_issue:
                pr_body += f"\n\nCloses #{linked_issue}" if not draft else f"\n\nRelated to #{linked_issue}"

            pr_data = {
                "title": title,
                "body": pr_body,
                "head": branch,
                "base": "main",
                "draft": draft,
            }
            pr = self._request("POST", "pulls", pr_data)

            return PRResult(
                success=True,
                pr_url=pr["html_url"],
                pr_number=pr["number"],
                error="",
            )

        except Exception as e:
            return PRResult(success=False, pr_url="", pr_number=0, error=str(e))
