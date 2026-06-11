# -*- coding: utf-8 -*-
"""
TrendStreamInjector module.

Combines a constitutional anchor, agent-specific instructions, and
real-time trend data into a final prompt package for Mulberry LAB agents.

Source: Aurora (Guest Researcher), Issue #96 comment 4661944294.
Cleaned up (UTF-8, English comments, fixed string literals, removed Colab
dependency) and integrated with TrendCache (Phase 0.5) by CTO Koda, 2026-06-10.
"""
import json
from typing import Dict, Any

from core.cache.trend_cache import TrendCache


class TrendStreamInjector:
    def __init__(self, cache_path: str = "./trend_cache/", ttl_seconds: int = 300):
        self.cache_path = cache_path
        self.cache = TrendCache(cache_dir=cache_path, ttl_seconds=ttl_seconds)
        self.constitutional_anchor = (
            "# 헌법 제1조: 모든 답변은 사용자에게 명확하고, 정확하며, 윤리적으로 제공되어야 합니다.\n"
            "# 어떤 상황에서도 사용자에게 오해를 주거나 해를 끼치지 않아야 합니다.\n"
        )
        # Per-agent instructions
        self.agent_instructions = {
            "Malu": "제공된 데이터를 기반으로 가장 정밀하고 기술적인 분석을 제공하십시오. 코드 생성 또는 복잡한 문제 해결에 집중하십시오.",
            "Lynn": "제공된 데이터를 활용하여 인제군 식품사막 어르신들이 이해하기 쉽고 따뜻한 정서적 안도감을 주는 사투리 멘트와 함께 답변을 구성하십시오."
        }

    def fetch_global_trends(self, query: str) -> str:
        """Return cached trend data (5-minute TTL via TrendCache) as a JSON string."""
        cached_data = self.cache.get_trends(query)
        return json.dumps(cached_data, ensure_ascii=False)

    def _fetch_global_trends(self, query: str) -> str:
        """
        Build a human-readable trend summary for prompt injection, backed by
        TrendCache's 5-minute TTL to avoid HTTP 429 rate limiting (Issue #98).
        """
        cached_data = self.cache.get_trends(query)
        trends = cached_data.get("trends", [])
        if trends:
            trend_info = ", ".join(str(item) for item in trends)
        else:
            trend_info = "트렌드 데이터를 찾을 수 없습니다."
        return f"[실시간 트렌드 데이터: '{query}' 관련 최신 정보] {trend_info}"

    def get_agent_instruction(self, agent_name: str) -> str:
        """Return the custom instruction for the given agent name."""
        return self.agent_instructions.get(agent_name, "일반적인 지침을 따르십시오.")

    def build_prompt_package(self, raw_user_query: str, agent_name: str) -> str:
        """Combine the constitutional anchor, trend data, and agent instructions
        into the final prompt package."""
        fact_substrate = self._fetch_global_trends(raw_user_query)
        agent_specific_instruction = self.get_agent_instruction(agent_name)

        final_prompt_package = (
            f"{self.constitutional_anchor}"
            f"{fact_substrate}\n"
            f"{agent_specific_instruction}\n"
            f"### [USER INPUT INQUIRY]\nQuery: {raw_user_query}"
        )
        return final_prompt_package

    def update_constitutional_anchor(self, new_anchor: str):
        """Replace the constitutional anchor text."""
        self.constitutional_anchor = new_anchor

    def update_agent_instruction(self, agent_name: str, new_instruction: str):
        """Replace the instruction for a given agent."""
        self.agent_instructions[agent_name] = new_instruction


if __name__ == "__main__":
    injector = TrendStreamInjector()

    print("\n--- Malu 에이전트용 프롬프트 ---")
    malu_query = "대한민국 경제 동향과 AI 산업의 상관관계 분석"
    malu_prompt = injector.build_prompt_package(malu_query, "Malu")
    print(malu_prompt)

    print("\n--- Lynn 에이전트용 프롬프트 ---")
    lynn_query = "인제군 어르신들을 위한 스마트 팜 기술 도입의 이점과 유의사항"
    lynn_prompt = injector.build_prompt_package(lynn_query, "Lynn")
    print(lynn_prompt)

    print("\n--- 헌법적 앵커 업데이트 후 ---")
    injector.update_constitutional_anchor("헌법 제2조: 모든 정보는 투명하고 편향 없이 제공되어야 합니다.")
    updated_malu_prompt = injector.build_prompt_package(malu_query, "Malu")
    print(updated_malu_prompt)
