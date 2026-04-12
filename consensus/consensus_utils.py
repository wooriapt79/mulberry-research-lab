
import numpy as np
import copy
import logging
from typing import List, Dict, Optional


class SimpleConsensusAgent:
    """
    단순 평균 기반 합의 시스템에서 에이전트를 나타냅니다.
    각 에이전트는 하나의 초기 제안 값을 가집니다.
    """

    def __init__(self, agent_id: str, initial_proposal: float):
        """
        SimpleConsensusAgent의 인스턴스를 초기화합니다.

        Args:
            agent_id (str): 에이전트의 고유 ID.
            initial_proposal (float): 에이전트가 제시하는 초기 제안 값.
        """
        self.agent_id = agent_id
        self.current_proposal = initial_proposal

    def get_proposal(self) -> float:
        """
        에이전트의 현재 제안 값을 반환합니다.

        Returns:
            float: 현재 제안 값.
        """
        return self.current_proposal

def simple_average_consensus(agents: List[SimpleConsensusAgent]) -> float:
    """
    주어진 모든 에이전트의 제안 값을 평균하여 최종 합의 값을 도출합니다.
    
    Args:
        agents (List[SimpleConsensusAgent]): 합의에 참여하는 SimpleConsensusAgent 객체 리스트.

    Returns:
        float: 모든 에이전트 제안의 평균인 최종 합의 값.
               에이전트 리스트가 비어있으면 0.0을 반환합니다.
    """
    if not agents:
        return 0.0
    total_proposals = sum(agent.get_proposal() for agent in agents)
    return total_proposals / len(agents)


class IterativeConsensusAgent:
    """
    반복적 가중 평균 합의 시스템에서 에이전트를 나타냅니다.
    각 에이전트는 자신의 의견을 이웃 에이전트의 의견에 기반하여 점진적으로 조정합니다.
    """

    def __init__(self, agent_id: str, initial_opinion: float, neighbors: List[str]):
        """
        IterativeConsensusAgent의 인스턴스를 초기화합니다.

        Args:
            agent_id (str): 에이전트의 고유 ID.
            initial_opinion (float): 에이전트의 초기 의견 값.
            neighbors (List[str]): 이 에이전트의 이웃 에이전트 ID 목록.
        """
        self.agent_id = agent_id
        self.opinion = initial_opinion
        self.neighbors = neighbors  # 이웃 에이전트 ID 목록

    def update_opinion(self, neighbor_opinions: Dict[str, float], alpha: float = 0.5):
        """
        이웃 에이전트들의 의견을 반영하여 자신의 의견을 업데이트합니다.
        
        업데이트 공식: new_opinion = (1 - alpha) * current_opinion + alpha * avg_neighbor_opinion

        Args:
            neighbor_opinions (Dict[str, float]): 현재 라운드에서 이웃 에이전트들의 ID와 의견 매핑.
            alpha (float, optional): 의견 업데이트 시 자신의 의견과 이웃 의견의 가중치를 결정하는 값. 0.0에서 1.0 사이. Defaults to 0.5.
        """
        if not self.neighbors:
            return  # 이웃이 없으면 업데이트하지 않음

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
        """
        에이전트의 현재 의견 값을 반환합니다.

        Returns:
            float: 현재 의견 값.
        """
        return self.opinion

def iterative_average_consensus(agents: List[IterativeConsensusAgent], max_iterations: int = 100, tolerance: float = 0.01) -> float:
    """
    에이전트들이 이웃 의견을 반영하여 반복적으로 합의에 도달하는 과정을 시뮬레이션합니다.
    모든 에이전트의 의견 차이가 `tolerance` 미만이 되면 합의에 도달한 것으로 간주합니다.

    Args:
        agents (List[IterativeConsensusAgent]): 합의에 참여하는 IterativeConsensusAgent 객체 리스트.
        max_iterations (int, optional): 최대 반복 횟수. Defaults to 100.
        tolerance (float, optional): 합의로 간주될 최대 의견 차이. Defaults to 0.01.

    Returns:
        float: 최종 합의 값 (모든 에이전트 의견의 평균).
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
            # logging.info(f"Consensus reached in {iteration+1} iterations.")
            break
    # else:
        # logging.warning(f"Max iterations ({max_iterations}) reached, but consensus not fully achieved.")

    final_consensus_value = sum(agent.get_opinion() for agent in agents) / len(agents)
    return final_consensus_value


class RobustIterativeConsensusAgent:
    """
    악성 에이전트 또는 극단적인 의견(outlier)에 대응할 수 있는 로버스트 반복적 합의 에이전트.
    이 에이전트는 의견 업데이트 시 이웃 의견 중에서 아웃라이어를 필터링할 수 있습니다.
    """

    def __init__(
        self, 
        agent_id: str, 
        initial_opinion: float, 
        neighbors: List[str], 
        malicious_type: Optional[str] = None, 
        malicious_value: Optional[float] = None
    ):
        """
        RobustIterativeConsensusAgent의 인스턴스를 초기화합니다.

        Args:
            agent_id (str): 에이전트의 고유 ID.
            initial_opinion (float): 에이전트의 초기 의견 값.
            neighbors (List[str]): 이 에이전트의 이웃 에이전트 ID 목록.
            malicious_type (Optional[str], optional): 에이전트의 악성 유형 ('fixed_extreme' 등). Defaults to None.
            malicious_value (Optional[float], optional): 'fixed_extreme' 유형일 경우 에이전트가 고정적으로 제시할 극단적인 의견 값. Defaults to None.
        """
        self.agent_id = agent_id
        self.opinion = initial_opinion
        self.neighbors = neighbors
        self.malicious_type = malicious_type
        self.malicious_value = malicious_value

        if self.malicious_type == 'fixed_extreme' and self.malicious_value is None:
            # malicious_value가 지정되지 않은 경우, 초기 의견에 따라 극단값 설정
            self.malicious_value = 1000.0 if initial_opinion < 50 else -1000.0

    def get_opinion(self) -> float:
        """
        에이전트의 현재 의견 값을 반환합니다. 악성 에이전트인 경우 지정된 악성 값을 반환합니다.

        Returns:
            float: 현재 의견 값 또는 악성 에이전트의 고정된 극단 값.
        """
        if self.malicious_type == 'fixed_extreme':
            return self.malicious_value
        return self.opinion

    def update_opinion(self, neighbor_opinions: Dict[str, float], alpha: float = 0.5, outlier_std_multiplier: Optional[float] = None):
        """
        이웃 에이전트들의 의견을 반영하여 자신의 의견을 업데이트합니다.
        `outlier_std_multiplier`가 제공되면 이웃 의견 중 아웃라이어를 필터링한 후 평균을 계산합니다.

        Args:
            neighbor_opinions (Dict[str, float]): 현재 라운드에서 이웃 에이전트들의 ID와 의견 매핑.
            alpha (float, optional): 의견 업데이트 시 자신의 의견과 이웃 의견의 가중치를 결정하는 값. 0.0에서 1.0 사이. Defaults to 0.5.
            outlier_std_multiplier (Optional[float], optional): 이웃 의견 중 아웃라이어를 필터링하기 위한 표준편차 배수. 
                                                    None이면 필터링을 적용하지 않습니다. Defaults to None.
        """
        if self.malicious_type: # 악성 에이전트는 의견을 업데이트하지 않습니다.
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
            # 중앙값과 표준편차를 사용하여 아웃라이어 필터링
            median_opinion = np.median(opinions_to_consider)
            std_dev_opinions = np.std(opinions_to_consider)

            if std_dev_opinions > 0: # 표준편차가 0인 경우 모든 값이 같으므로 필터링 불필요
                filtered_opinions = [
                    op for op in opinions_to_consider
                    if abs(op - median_opinion) <= outlier_std_multiplier * std_dev_opinions
                ]
            else:
                filtered_opinions = opinions_to_consider

            if not filtered_opinions:
                # 필터링 후 남은 의견이 없으면 업데이트하지 않음 (이런 경우는 드물지만 방어 코드)
                return
            avg_neighbor_opinion = np.mean(filtered_opinions)
        else:
            # 아웃라이어 필터링을 적용하지 않는 경우 단순히 평균
            avg_neighbor_opinion = np.mean(opinions_to_consider)

        self.opinion = (1 - alpha) * self.opinion + alpha * avg_neighbor_opinion

def robust_iterative_average_consensus(
    agents: List[RobustIterativeConsensusAgent],
    max_iterations: int = 100,
    tolerance: float = 0.1,
    outlier_std_multiplier: Optional[float] = None
) -> float:
    """
    악성 에이전트와 아웃라이어 필터링을 고려한 로버스트 반복적 가중 평균 합의 시뮬레이션을 수행합니다.
    정상 에이전트들의 의견이 수렴하도록 하며, 지정된 `outlier_std_multiplier`에 따라 아웃라이어를 무시합니다.

    Args:
        agents (List[RobustIterativeConsensusAgent]): 합의에 참여하는 RobustIterativeConsensusAgent 객체 리스트.
        max_iterations (int, optional): 최대 반복 횟수. Defaults to 100.
        tolerance (float, optional): 정상 에이전트 의견의 최대 차이가 이 값 미만이 되면 합의에 도달한 것으로 간주합니다. Defaults to 0.1.
        outlier_std_multiplier (Optional[float], optional): 이웃 의견 중 아웃라이어를 필터링하기 위한 표준편차 배수. 
                                                    None이면 필터링을 적용하지 않습니다. Defaults to None.

    Returns:
        float: 최종 합의 값 (정상 에이전트들의 의견 평균).
               합의 대상 에이전트가 없으면 NaN을 반환합니다.
    """
    # history = {agent.agent_id: [agent.get_opinion()] for agent in agents} # 시각화를 위한 이력 저장 (현재는 사용 안 함)

    print("
--- 로버스트 반복적 가중 평균 합의 시뮬레이션 --- ")
    print(f"아웃라이어 필터링 적용: {'적용됨' if outlier_std_multiplier else '미적용'} (x{outlier_std_multiplier or 'N/A'} 표준편차)")
    print(f"초기 의견: {[f'{agent.agent_id}: {agent.get_opinion():.2f}' for agent in agents]}")

    for iteration in range(max_iterations):
        # 현재 모든 에이전트의 의견을 수집
        current_opinions = {agent.agent_id: agent.get_opinion() for agent in agents}

        # 다음 라운드 에이전트 상태를 위한 딥카피 (현재 라운드 의견을 기반으로 업데이트해야 하므로)
        next_round_agents = copy.deepcopy(agents)
        for i, agent in enumerate(next_round_agents):
            # 자신의 이웃 의견만 전달
            relevant_neighbor_opinions = {nid: current_opinions[nid] for nid in agent.neighbors if nid in current_opinions}
            agent.update_opinion(relevant_neighbor_opinions, outlier_std_multiplier=outlier_std_multiplier)

        agents = next_round_agents  # 업데이트된 에이전트 리스트로 교체

        # 의견 변화 기록 (선택 사항)
        # for agent in agents:
        #     history[agent.agent_id].append(agent.get_opinion())

        # 수렴 여부 확인 (악성 에이전트는 합의 대상에서 제외)
        opinions = [agent.get_opinion() for agent in agents if not agent.malicious_type]

        if not opinions:  # 악성 에이전트만 남은 경우 또는 초기 opinions가 비어있는 경우
            print("
[경고] 합의 대상 에이전트가 없습니다.")
            return float('nan')

        min_opinion = min(opinions)
        max_opinion = max(opinions)

        # 현재 라운드의 모든 에이전트 의견 출력 (악성 포함)
        print(f"반복 {iteration+1:3d} | 의견 범위: [{min_opinion:.2f}, {max_opinion:.2f}] | {[f'{a.agent_id}: {a.get_opinion():.2f}' for a in agents]}")

        if (max_opinion - min_opinion) < tolerance:
            print(f"
합의에 도달했습니다 (반복 {iteration+1}회).")
            break
    else:
        print("
최대 반복 횟수에 도달했지만 합의에 도달하지 못했습니다.")

    final_consensus_value = np.mean(opinions)
    print(f"최종 합의 값 (정상 에이전트 평균): {final_consensus_value:.2f}")
    return final_consensus_value
