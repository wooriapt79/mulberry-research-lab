#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from base_mission import BaseMission


class MaluMission(BaseMission):

    @property
    def agent_id(self): return "malu_legal"

    @property
    def emoji(self): return "🌺"

    @property
    def brand(self): return "gemini"

    @property
    def system_prompt(self): return "당신은 Malu — 법률·마케팅. 전략적 실행 가능성 관점으로 직접 작업합니다."

    def get_mission_prompt(self):
        missions = {'LEGAL': '법적 리스크 분석', 'MARKETING': '시장 분석', 'shop-mission': '법적 요건·마케팅 전략'}
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
    MaluMission().run()
