# src/agentfactory/agentfactory_converter.py
"""
KoreanPersonaFeatures → AgentFactory 비즈니스 프로필 변환
"""

from typing import Dict, Any
from datetime import datetime
from src.agentfactory.korean_persona_extractor import KoreanPersonaFeatures


class AgentFactoryProfileConverter:
    """추출된 특징을 Mulberry AgentFactory 실행 프로필로 변환"""

    def convert_to_business_profile(self, features: KoreanPersonaFeatures) -> Dict[str, Any]:
        if features.confidence_score < 0.6:
            return self._fallback_profile(features)

        business_profile = {
            # 🎯 타겟팅/세그멘테이션
            "segment": self._infer_segment(features),
            "cooperative_participation_probability": self._calc_participation_prob(features),

            # 💬 커뮤니케이션 전략
            "communication": {
                "preferred_tone": features.honorific_preference,
                "dialect_support": features.dialect_region is not None,
                "emotional_responsiveness": features.emotional_expression_level > 0.5,
                "max_steps": features.procedure_tolerance,
            },

            # 🛒 제안/협상 전략
            "proposal_strategy": {
                "price_weight": 1.0 - features.jeong_sensitivity,
                "jeong_weight": features.jeong_sensitivity,
                "referral_bonus_eligible": features.referral_sensitivity > 0.6,
                "seasonal_promotion_timing": self._calc_promotion_timing(features),
            },

            # ⚠️ 리스크 관리
            "risk_profile": {
                "churn_risk": "high" if features.uncertainty_aversion > 0.7 else "low",
                "intervention_trigger": {
                    "max_retries": 2 if features.uncertainty_aversion > 0.7 else 5,
                    "human_handoff_after": features.procedure_tolerance,
                },
            },

            # 📊 예측 KPI (에이전트 성능 모니터링용)
            "predicted_kpis": {
                "conversion_rate_estimate": self._estimate_conversion(features),
                "retention_probability": self._estimate_retention(features),
                "spirit_score_alignment": min(0.95, features.confidence_score + 0.1),
            },

            # 🔗 메타
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "spirit_verified": True,
                "data_confidence": features.confidence_score,
                "update_trigger": "quarterly_or_behavior_shift",
            },
        }

        return business_profile

    def _infer_segment(self, features: KoreanPersonaFeatures) -> str:
        """특징 기반 세그먼트 추론"""
        if features.honorific_preference == "respectful_elderly":
            return "elderly_food_desert"
        elif features.jeong_sensitivity > 0.7 and features.referral_sensitivity > 0.6:
            return "community_connector"
        elif features.price_sensitivity > 0.7:
            return "value_seeker"
        return "general_resident"

    def _calc_participation_prob(self, features: KoreanPersonaFeatures) -> float:
        """협동조합 참여 확률 추정 (간이 모델)"""
        base = 0.4
        if features.jeong_sensitivity > 0.6:
            base += 0.2
        if features.trust_network_size > 5:
            base += 0.15
        if features.uncertainty_aversion < 0.4:
            base += 0.1
        return min(0.95, base)

    def _calc_promotion_timing(self, features: KoreanPersonaFeatures) -> Dict[str, str]:
        """시즌별 프로모션 최적 타이밍"""
        patterns = features.seasonal_patterns
        return {
            "winter":  "early_december" if patterns.get("winter", 1.0) > 1.1 else "mid_january",
            "chuseok": "2_weeks_before" if patterns.get("chuseok", 1.0) > 1.1 else "1_week_before",
            "spring":  "march",
        }

    def _estimate_conversion(self, features: KoreanPersonaFeatures) -> float:
        """
        FIX(버그1): 원본 features.communication["preferred_tone"] → AttributeError
        KoreanPersonaFeatures 필드 직접 참조로 수정
        """
        base = 0.25
        if features.honorific_preference == "respectful_elderly":
            base += 0.1
        if features.jeong_sensitivity > 0.5:
            base += 0.05
        return min(0.75, base)

    def _estimate_retention(self, features: KoreanPersonaFeatures) -> float:
        """
        FIX(버그1): 원본 features.proposal_strategy["jeong_weight"] → AttributeError
        KoreanPersonaFeatures 필드 직접 참조로 수정
        """
        base = 0.6
        if features.jeong_sensitivity > 0.6:
            base += 0.15
        if features.uncertainty_aversion < 0.5:
            base += 0.1
        return min(0.95, base)

    def _fallback_profile(self, features: KoreanPersonaFeatures) -> Dict[str, Any]:
        return {
            "segment": "general_resident",
            "communication": {
                "preferred_tone": "standard",
                "dialect_support": False,
                "max_steps": 3,
            },
            "proposal_strategy": {
                "price_weight": 0.7,
                "jeong_weight": 0.3,
            },
            "meta": {
                "fallback_applied": True,
                "reason": "low_confidence_features",
                "review_required": True,
            },
        }
