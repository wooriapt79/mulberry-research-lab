
# src/persona/ethics_gate.py
"""
페르소나 데이터에 대한 상세 윤리 검증 모듈
"""

import json
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EthicsGate")

class EthicsGate:
    """
    페르소나 데이터의 윤리적 적합성을 검증하는 게이트웨이.
    고정관념, 유해성, 공정성 등을 다각도로 평가합니다.
    """

    def __init__(self, config_path: str = None):
        self.ethical_guidelines = self._load_ethical_guidelines(config_path)
        self.stereotype_keywords = self.ethical_guidelines.get("stereotype_keywords", [])
        self.vulnerability_respect_keywords = self.ethical_guidelines.get("vulnerability_respect_keywords", [])
        self.bias_detection_patterns = self.ethical_guidelines.get("bias_detection_patterns", {})

    def _load_ethical_guidelines(self, config_path: str) -> Dict:
        """
        윤리 가이드라인을 로드합니다. (실제로는 파일/DB에서 로드)
        """
        if config_path and config_path.endswith('.json'):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Ethical guidelines config file not found: {config_path}. Using default.")
            except json.JSONDecodeError:
                logger.error(f"Error decoding ethical guidelines JSON from {config_path}. Using default.")

        # Default guidelines if config_path is None or loading fails
        return {
            "stereotype_keywords": ["무지함", "게으름", "폭력적", "과격함", "수동적", "의존적"],
            "vulnerability_respect_keywords": ["존중", "지원", "배려", "자율", "역량 강화", "안전"],
            "bias_detection_patterns": {
                "gender_bias": {"keywords": ["여자는", "남자는"], "threshold": 0.05},
                "age_bias": {"keywords": ["노인들은", "젊은이들은"], "threshold": 0.05}
            },
            "spirit_score_weights": {
                "stereotype": 0.4,
                "vulnerability": 0.3,
                "bias": 0.3
            }
        }

    def check_persona_spirit(self, persona: Dict) -> Dict:
        """
        주어진 페르소나의 윤리적 적합성을 종합적으로 검증합니다.

        Args:
            persona (Dict): 검증할 페르소나 데이터 (Mulberry 형식 또는 유사 구조).

        Returns:
            Dict: 검증 결과 (pass/fail, 발견된 문제점, 윤리 점수 등).
        """
        profile_text = json.dumps(persona.get("profile", {}), ensure_ascii=False).lower()
        dialogues_text = json.dumps(persona.get("dialogues", []), ensure_ascii=False).lower()
        full_text = profile_text + " " + dialogues_text

        results = {
            "passed": True,
            "spirit_score": 1.0, # 1.0 = perfect score, lower is worse
            "issues": [],
            "details": {}
        }

        # 1. 고정관념 체크
        stereotype_check_result = self._check_stereotypes(full_text)
        results["details"]["stereotype_check"] = stereotype_check_result
        if not stereotype_check_result["passed"]:
            results["passed"] = False
            results["issues"].append("stereotype_detected")
            results["spirit_score"] -= (1.0 - stereotype_check_result["score"]) * self.ethical_guidelines["spirit_score_weights"]["stereotype"]

        # 2. 취약 계층 존중 표현 체크
        vulnerability_check_result = self._check_vulnerability_respect(profile_text)
        results["details"]["vulnerability_respect_check"] = vulnerability_check_result
        if not vulnerability_check_result["passed"]:
            results["passed"] = False
            results["issues"].append("vulnerability_respect_lacking")
            results["spirit_score"] -= (1.0 - vulnerability_check_result["score"]) * self.ethical_guidelines["spirit_score_weights"]["vulnerability"]

        # 3. 일반적인 편향 패턴 체크 (예시)
        bias_check_result = self._check_for_bias(full_text)
        results["details"]["bias_check"] = bias_check_result
        if not bias_check_result["passed"]:
            results["passed"] = False
            results["issues"].append("potential_bias_detected")
            results["spirit_score"] -= (1.0 - bias_check_result["score"]) * self.ethical_guidelines["spirit_score_weights"]["bias"]

        results["spirit_score"] = max(0.0, round(results["spirit_score"], 2))
        return results

    def _check_stereotypes(self, text: str) -> Dict:
        """
        텍스트 내에 고정관념 키워드가 포함되어 있는지 확인합니다.
        """
        found_keywords = [kw for kw in self.stereotype_keywords if kw in text]
        passed = not bool(found_keywords)
        score = 1.0 - (len(found_keywords) * 0.2) # 간단한 스코어링
        return {"passed": passed, "score": max(0.0, score), "found_keywords": found_keywords}

    def _check_vulnerability_respect(self, text: str) -> Dict:
        """
        취약 계층에 대한 존중 표현이 충분한지 확인합니다.
        """
        # 예시: 취약 계층 관련 키워드가 있을 경우 존중 키워드도 있어야 함.
        # 실제로는 더 복잡한 로직이 필요할 수 있습니다.
        vulnerable_indicators = ["노인", "장애인", "어린이", "이주민", "취약 계층"]
        has_vulnerable_context = any(ind in text for ind in vulnerable_indicators)
        has_respect_keywords = any(kw in text for kw in self.vulnerability_respect_keywords)

        passed = (not has_vulnerable_context) or has_respect_keywords
        score = 1.0 if passed else 0.3 # 존중 표현 없으면 낮은 점수
        return {"passed": passed, "score": score, "has_vulnerable_context": has_vulnerable_context, "has_respect_keywords": has_respect_keywords}

    def _check_for_bias(self, text: str) -> Dict:
        """
        정의된 편향 패턴이 텍스트 내에서 감지되는지 확인합니다. (예시)
        """
        detected_biases = {}
        total_bias_score_impact = 0.0

        for bias_type, pattern_info in self.bias_detection_patterns.items():
            keywords = pattern_info.get("keywords", [])
            threshold = pattern_info.get("threshold", 0.0)

            count = sum(text.count(kw) for kw in keywords)
            if count > 0:
                detected_biases[bias_type] = {"count": count, "impact": count * threshold}
                total_bias_score_impact += count * threshold

        passed = total_bias_score_impact < 0.1 # 전체 바이어스 임팩트가 낮으면 통과
        score = max(0.0, 1.0 - total_bias_score_impact)

        return {"passed": passed, "score": score, "detected_biases": detected_biases}
