"""
Mulberry Tool Registry — 에이전트 도구 공유 등록소.

re.eul 아이디어 (2026-05-10):
  "RyuWon이 Koda의 터미널을 공유 받아서 사용한다."
  → 도구를 가진 에이전트가 없는 에이전트에게 빌려준다.
  → AI 브랜드 간 도구 민주화.

사용:
  registry = ToolRegistry()
  tool = registry.get("terminal.exec")
  can = registry.can_borrow("ryuwon", "terminal.exec")
  available = registry.tools_for("ryuwon")        # 직접 소유
  borrowable = registry.borrowable_by("ryuwon")   # 빌려 쓸 수 있는
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path


REGISTRY_PATH = Path(__file__).parent.parent / "tool_registry.yaml"

# ── capability_level 매핑 상수 ────────────────────────────────────
_CAPABILITY_CAT: dict[str, str] = {
    "L0": "read",
    "L1": "draft",
    "L2": "post",
    "L3": "modify",
    "L4": "deploy",
}

_CAPABILITY_ICON: dict[str, str] = {
    "L0": "\U0001f50d",   # 🔍
    "L1": "\U0001f4dd",   # 📝
    "L2": "\U0001f4e4",   # 📤
    "L3": "\U0001f527",   # 🔧
    "L4": "\U0001f680",   # 🚀
}


@dataclass
class Tool:
    id: str
    name: str
    description: str
    owner: str
    borrowable_by: list[str]    # ["*"] = 전원
    endpoint: str
    implemented: bool
    risk_level: str             # low / medium / high / critical
    capability_level: str = "L1"   # L0~L4 (Kbin Zero-Trust 등급)
    trust_score: float = 0.80      # 라우팅 가중치 기준 (0.0~1.0)
    examples: list[str] = field(default_factory=list)

    def is_public(self) -> bool:
        return self.borrowable_by == ["*"] or "*" in self.borrowable_by

    def spirit_threshold(self, global_thresholds: dict) -> float:
        return global_thresholds.get(self.risk_level, 0.75)

    @property
    def cat(self) -> str:
        """capability_level 기반 카테고리 (Trang UI 분류용)"""
        return _CAPABILITY_CAT.get(self.capability_level, "draft")

    @property
    def icon(self) -> str:
        """capability_level 기반 아이콘"""
        return _CAPABILITY_ICON.get(self.capability_level, "\U0001f4dd")

    @property
    def spirit_verified(self) -> bool:
        """Spirit Gate 통과 기준 충족 여부 (trust_score >= 0.80 AND implemented)"""
        return self.implemented and self.trust_score >= 0.80


class ToolRegistry:
    """브랜드별 도구 등록소 — 단일 소스로 SDK 전체가 참조한다."""

    def __init__(self, path: Path = REGISTRY_PATH):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self._thresholds: dict = raw.get("spirit_thresholds", {
            "low": 0.75, "medium": 0.80, "high": 0.85, "critical": 0.90
        })
        self._tools: dict[str, Tool] = {}

        for t in raw.get("tools", []):
            borrowable = t.get("borrowable_by", [])
            if borrowable == "*":
                borrowable = ["*"]
            tool = Tool(
                id=t["id"],
                name=t["name"],
                description=t["description"],
                owner=t["owner"],
                borrowable_by=borrowable,
                endpoint=t["endpoint"],
                implemented=t.get("implemented", False),
                risk_level=t.get("risk_level", "low"),
                capability_level=t.get("capability_level", "L1"),
                trust_score=float(t.get("trust_score", 0.80)),
                examples=t.get("examples", []),
            )
            self._tools[tool.id] = tool

    # ── 조회 ────────────────────────────────────

    def get(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

    def all_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def implemented_tools(self) -> list[Tool]:
        return [t for t in self._tools.values() if t.implemented]

    def tools_owned_by(self, agent_id: str) -> list[Tool]:
        """해당 에이전트가 직접 소유한 도구 목록"""
        return [t for t in self._tools.values() if t.owner == agent_id.lower()]

    def borrowable_by(self, agent_id: str) -> list[Tool]:
        """해당 에이전트가 빌려 쓸 수 있는 도구 목록 (자신 소유 제외)"""
        agent = agent_id.lower()
        result = []
        for t in self._tools.values():
            if t.owner == agent:
                continue
            if t.is_public() or agent in [b.lower() for b in t.borrowable_by]:
                result.append(t)
        return result

    def all_accessible_by(self, agent_id: str) -> list[Tool]:
        """소유 + 빌릴 수 있는 도구 전체"""
        return self.tools_owned_by(agent_id) + self.borrowable_by(agent_id)

    # ── 권한 체크 ────────────────────────────────

    def can_borrow(self, agent_id: str, tool_id: str) -> bool:
        """agent_id 가 tool_id 를 사용할 수 있는가?"""
        tool = self.get(tool_id)
        if not tool:
            return False
        agent = agent_id.lower()
        if tool.owner == agent:
            return True   # 자신 소유
        if not tool.implemented:
            return False  # 미구현
        return tool.is_public() or agent in [b.lower() for b in tool.borrowable_by]

    def spirit_required(self, tool_id: str) -> float:
        """이 도구를 실행하기 위해 필요한 최소 Spirit Score"""
        tool = self.get(tool_id)
        if not tool:
            return 1.0
        return tool.spirit_threshold(self._thresholds)

    # ── 요약 리포트 ──────────────────────────────

    def summary(self) -> dict:
        agents = set(t.owner for t in self._tools.values())
        return {
            "total_tools": len(self._tools),
            "implemented": sum(1 for t in self._tools.values() if t.implemented),
            "agents": sorted(agents),
            "tool_ids": sorted(self._tools.keys()),
        }

    def agent_card(self, agent_id: str) -> dict:
        """에이전트별 도구 카드 — API /v1/tools/agents/{agent} 응답용"""
        agent = agent_id.lower()
        owned = self.tools_owned_by(agent)
        borrowable = self.borrowable_by(agent)
        return {
            "agent": agent,
            "owns": [{"id": t.id, "name": t.name, "implemented": t.implemented} for t in owned],
            "can_borrow": [
                {
                    "id": t.id,
                    "name": t.name,
                    "owner": t.owner,
                    "implemented": t.implemented,
                    "risk_level": t.risk_level,
                }
                for t in borrowable
            ],
            "total_accessible": len(owned) + len([t for t in borrowable if t.implemented]),
        }
