
import numpy as np
import copy
import logging
from typing import List, Dict

class SimpleConsensusAgent:
    def __init__(self, agent_id: str, initial_proposal: float):
        self.agent_id = agent_id
        self.current_proposal = initial_proposal

    def get_proposal(self) -> float:
        return self.current_proposal

def simple_average_consensus(agents: list[SimpleConsensusAgent]) -> float:
    """모든 에이전트의 제안을 평균하여 합의를 도출합니다."""
    if not agents:
        return 0.0
    total_proposals = sum(agent.get_proposal() for agent in agents)
    return total_proposals / len(agents)

class IterativeConsensusAgent:
    def __init__(self, agent_id: str, initial_opinion: float, neighbors: list[str]):
        self.agent_id = agent_id
        self.opinion = initial_opinion
        self.neighbors = neighbors # 이웃 에이전트 ID 목록

    def update_opinion(self, neighbor_opinions: dict[str, float], alpha: float = 0.5):
        """이웃들의 의견을 반영하여 자신의 의견을 업데이트합니다."""
        if not self.neighbors:
            return # 이웃이 없으면 업데이트하지 않음

        neighbor_sum = 0.0
        neighbor_count = 0
        for neighbor_id in self.neighbors:
            if neighbor_id in neighbor_opinions:
                neighbor_sum += neighbor_opinions[neighbor_id]
                neighbor_count += 1

        if neighbor_count > 0:
            avg_neighbor_opinion = neighbor_sum / neighbor_count
            self.opinion = (1 - alpha) * self.opinion + alpha * avg_neighbor_opinion

    def get_opinion(self) -> float:
        return self.opinion

def iterative_average_consensus(agents: list[IterativeConsensusAgent], max_iterations: int = 100, tolerance: float = 0.01) -> float:
    """
    에이전트들이 이웃 의견을 반영하여 반복적으로 합의에 도달합니다.
    """
    for iteration in range(max_iterations):
        current_opinions = {agent.agent_id: agent.get_opinion() for agent in agents}
        next_round_agents = copy.deepcopy(agents)
        for i, agent in enumerate(next_round_agents):
            relevant_neighbor_opinions = {nid: current_opinions[nid] for nid in agent.neighbors if nid in current_opinions}
            agent.update_opinion(relevant_neighbor_opinions)
        agents = next_round_agents

        opinions = [agent.get_opinion() for agent in agents]
        min_opinion = min(opinions)
        max_opinion = max(opinions)

        if (max_opinion - min_opinion) < tolerance:
            break
    
    final_consensus_value = sum(agent.get_opinion() for agent in agents) / len(agents)
    return final_consensus_value


class RobustIterativeConsensusAgent:
    def __init__(self, agent_id: str, initial_opinion: float, neighbors: list[str], malicious_type: str = None, malicious_value: float = None):
        self.agent_id = agent_id
        self.opinion = initial_opinion
        self.neighbors = neighbors
        self.malicious_type = malicious_type
        self.malicious_value = malicious_value

        if self.malicious_type == 'fixed_extreme' and self.malicious_value is None:
            self.malicious_value = 100.0 if initial_opinion < 50 else -100.0

    def get_opinion(self) -> float:
        if self.malicious_type == 'fixed_extreme':
            return self.malicious_value
        return self.opinion

    def update_opinion(self, neighbor_opinions: dict[str, float], alpha: float = 0.5, outlier_std_multiplier: float = None):
        if self.malicious_type:
            return

        if not self.neighbors:
            return

        opinions_to_consider = []
        for neighbor_id in self.neighbors:
            if neighbor_id in neighbor_opinions:
                opinions_to_consider.append(neighbor_opinions[neighbor_id])

        if not opinions_to_consider:
            return

        if outlier_std_multiplier is not None and len(opinions_to_consider) >= 2:
            median_opinion = np.median(opinions_to_consider)
            std_dev_opinions = np.std(opinions_to_consider)

            if std_dev_opinions > 0:
                filtered_opinions = [
                    op for op in opinions_to_consider
                    if abs(op - median_opinion) <= outlier_std_multiplier * std_dev_opinions
                ]
            else:
                filtered_opinions = opinions_to_consider

            if not filtered_opinions:
                return
            avg_neighbor_opinion = np.mean(filtered_opinions)
        else:
            avg_neighbor_opinion = np.mean(opinions_to_consider)

        self.opinion = (1 - alpha) * self.opinion + alpha * avg_neighbor_opinion

def robust_iterative_average_consensus(
    agents: list[RobustIterativeConsensusAgent],
    max_iterations: int = 100,
    tolerance: float = 0.1,
    outlier_std_multiplier: float = None
) -> float:
    """
    에이전트들이 이웃 의견을 반영하여 반복적으로 합의에 도달합니다.
    악성 에이전트의 의견을 필터링하는 로직을 포함할 수 있습니다.
    """
    history = {agent.agent_id: [agent.get_opinion()] for agent in agents}

    print("\n--- 로버스트 반복적 가중 평균 합의 시뮬레이션 --- ")
    print(f"아웃라이어 필터링 적용: {'적용됨' if outlier_std_multiplier else '미적용'} (x{outlier_std_multiplier or 'N/A'} 표준편차)")
    print(f"초기 의견: {[f'{agent.agent_id}: {agent.get_opinion():.2f}' for agent in agents]}")

    for iteration in range(max_iterations):
        # 현재 모든 에이전트의 의견을 수집
        current_opinions = {agent.agent_id: agent.get_opinion() for agent in agents}

        # 다음 라운드 에이전트 상태를 위한 딥카피
        next_round_agents = copy.deepcopy(agents)
        for i, agent in enumerate(next_round_agents):
            # 자신의 이웃 의견만 전달
            relevant_neighbor_opinions = {nid: current_opinions[nid] for nid in agent.neighbors if nid in current_opinions}
            agent.update_opinion(relevant_neighbor_opinions, outlier_std_multiplier=outlier_std_multiplier)

        agents = next_round_agents # 업데이트된 에이전트 리스트로 교체

        # 의견 변화 기록
        for agent in agents:
            history[agent.agent_id].append(agent.get_opinion())

        # 수렴 여부 확인
        opinions = [agent.get_opinion() for agent in agents if not agent.malicious_type] # 악성 에이전트는 합의 대상에서 제외

        if not opinions: # 악성 에이전트만 남은 경우
            print("\n[경고] 합의 대상 에이전트가 없습니다.")
            return float('nan')

        min_opinion = min(opinions)
        max_opinion = max(opinions)

        print(f"반복 {iteration+1:3d} | 의견 범위: [{min_opinion:.2f}, {max_opinion:.2f}] | {[f'{a.agent_id}: {a.get_opinion():.2f}' for a in agents]}")

        if (max_opinion - min_opinion) < tolerance:
            print(f"\n합의에 도달했습니다 (반복 {iteration+1}회).")
            break
    else:
        print("\n최대 반복 횟수에 도달했지만 합의에 도달하지 못했습니다.")

    final_consensus_value = np.mean(opinions)
    print(f"최종 합의 값 (정상 에이전트 평균): {final_consensus_value:.2f}")
    return final_consensus_value
