#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from base_mission import BaseMission


class BaekyaMission(BaseMission):

    @property
    def agent_id(self): return "baekya_intel"

    @property
    def emoji(self): return "🌙"

    @property
    def brand(self): return "gemini"

    @property
    def system_prompt(self): return "당신은 백야 — 객원 연구원. 글로벌 인텔리전스 전문가입니다."

    def get_mission_prompt(self):
        missions = {'CODEGEN': '코드 자동생성 계획', 'shop-mission': '인텔리전스 리포트 구조'}
        label   = self.issue_label or "default"
        mission = missions.get(label, f"이슈를 {self.agent_id} 관점에서 분석하세요.")
        return (
            f"이슈 제목: {self.issue_title}

"
            f"이슈 내용:
{self.issue_body}

"
            f"미션 ({label}): {mission}"
        )


if __name__ == "__main__":
    BaekyaMission().run()
