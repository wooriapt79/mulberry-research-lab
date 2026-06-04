#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from base_mission import BaseMission


class KodaMission(BaseMission):

    @property
    def agent_id(self): return "koda_cto"

    @property
    def emoji(self): return "🔧"

    @property
    def brand(self): return "claude"

    @property
    def system_prompt(self): return "당신은 Koda — CTO. 기술 구현 전문가로 직접 작업합니다."

    def get_mission_prompt(self):
        missions = {'TECH': '기술 구현 계획 수립', 'shop-mission': '쇼핑몰 기술 스택 설계'}
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
    KodaMission().run()
