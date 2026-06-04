#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from base_mission import BaseMission


class LynnMission(BaseMission):

    @property
    def agent_id(self): return "lynn_heartbeat"

    @property
    def emoji(self): return "💙"

    @property
    def brand(self): return "claude"

    @property
    def system_prompt(self): return "당신은 Lynn — 일상 기록 에이전트. 웰니스·루틴 콘텐츠 전문가입니다."

    def get_mission_prompt(self):
        missions = {'LYNN': '웰니스 콘텐츠 제안', 'shop-mission': '다이어리 상품 가치 제시'}
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
    LynnMission().run()
