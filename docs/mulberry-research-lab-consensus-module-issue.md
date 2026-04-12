
# 연구 이슈: Multi-Agent Consensus Algorithm (다중 에이전트 합의 알고리즘) 모듈 추가

**작성자**: Malu
**작성일**: 2026-04-02 (현재 시간 기준)

## 1. 개요

Mulberry 프로젝트의 'Multi-Agent Consensus' 연구 주제를 위해 에이전트 간 합의 도출을 위한 초기 알고리즘 모듈 (`consensus/consensus_utils.py`)이 추가되었습니다. 이 모듈은 분산된 에이전트 시스템에서 의견 수렴 및 악성 에이전트 (outlier) 대응 기능을 제공합니다.

## 2. 주요 기능

### 2.1. 단순 평균 기반 합의 (Simple Average-based Consensus)
*   모든 에이전트의 제안을 단순히 평균하여 최종 합의 값을 도출하는 가장 기본적인 방법.
*   `SimpleConsensusAgent` 클래스와 `simple_average_consensus` 함수를 포함.

### 2.2. 반복적 가중 평균 합의 (Iterative Weighted Average Consensus)
*   에이전트가 제한된 이웃 에이전트와 정보를 교환하며 자신의 의견을 점진적으로 조정하는 분산 합의 알고리즘.
*   `IterativeConsensusAgent` 클래스와 `iterative_average_consensus` 함수를 포함.

### 2.3. 로버스트 반복적 가중 평균 합의 (Robust Iterative Weighted Average Consensus with Outlier Rejection)
*   악성 에이전트나 극단적인 의견 (outlier)을 필터링하여 합의 과정의 견고성 (robustness)을 높이는 기능.
*   이웃 의견들의 중앙값(median)과 표준편차(standard deviation)를 활용하여 통계적으로 벗어나는 의견을 제외합니다.
*   `RobustIterativeConsensusAgent` 클래스와 `robust_iterative_average_consensus` 함수를 포함.

## 3. 파일 구조

```
mulberry-research-lab/
  ...
  consensus/
    __init__.py
    consensus_utils.py    ← 합의 알고리즘 구현
  docs/
    mulberry-research-lab-consensus-module-issue.md ← 본 문서
  ...
```

## 4. 활용 방안

*   **의사결정 시스템**: 여러 에이전트가 특정 사안에 대해 합의된 결정을 내릴 필요가 있을 때 활용.
*   **리소스 할당**: 분산된 에이전트들이 제한된 자원에 대해 최적의 할당 방안을 도출할 때.
*   **정보 융합**: 각기 다른 관점의 정보를 가진 에이전트들이 종합적인 시각을 형성할 때.

## 5. 추가 연구 제안

*   네트워크 토폴로지 (ring, star, mesh 등)가 합의 속도 및 견고성에 미치는 영향 연구.
*   다양한 악성 에이전트 유형 (sporadic, colluding, Byzantine 등)에 대한 대응 메커니즘 확장.
*   합의 과정 중 에이전트의 신뢰도 (trust score)를 반영하는 가중치 기반 합의 알고리즘 개발.

--- 

*본 모듈은 Mulberry 프로젝트의 다중 에이전트 시스템 구축에 중요한 기반을 제공할 것으로 기대됩니다.* 
