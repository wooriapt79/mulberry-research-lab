#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from base_mission import BaseMission


class RyuWonMission(BaseMission):

    @property
    def agent_id(self): return "ryuwon_ethics"

    @property
    def emoji(self): return "🌊"

    @property
    def brand(self): return "claude"

    @property
    def system_prompt(self): return "당신은 RyuWon — 윤리 검증. 흐름과 균형 관점으로 직접 작업합니다."

    def get_mission_prompt(self):
        missions = {'DEPLOY': '배포 체크리스트', 'shop-mission': '윤리적 운영 원칙'}
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
    RyuWonMission().run()
