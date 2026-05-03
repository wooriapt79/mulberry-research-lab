# src/agentfactory/korean_persona_extractor.py
"""
한국인 특성 기반 페르소나 특징 추출기
Mulberry AgentFactory 용 프로필 생성 파이프라인
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KoreanPersonaExtractor")


@dataclass
class KoreanPersonaFeatures:
    """추출된 한국인 특성 특징"""
    # 관계 지향성
    trust_network_size: int
    referral_sensitivity: float       # 0.0~1.0: 추천에 반응할 확률

    # 언어 계층성
    dialect_region: Optional[str]     # "gyeongsang", "gangwon", "jeolla" 등
    honorific_preference: str         # "respectful_elderly", "standard", "casual"
    emotional_expression_level: float # 감정어 사용 빈도 (0.0~1.0)

    # 상황 민감성
    peak_activity_hours: List[int]
    seasonal_patterns: Dict[str, float]

    # 위험 회피성
    procedure_tolerance: int          # 허용하는 최대 절차 단계 (1~5)
    uncertainty_aversion: float       # 0.0~1.0

    # 가치 민감성
    price_sensitivity: float          # 0.0~1.0
    jeong_sensitivity: float          # 0.0~1.0: 정(情)/관계 가치 반응도

    # 메타
    confidence_score: float
    data_sources: List[str] = field(default_factory=list)


class KoreanPersonaFeatureExtractor:
    """다중 소스로부터 한국인 특성 특징 추출"""

    def __init__(self, spirit_threshold: float = 0.75):
        self.spirit_threshold = spirit_threshold
        self.dialect_map = {
            "주이소": ("gyeongsang", "respectful_request"),
            "하능가": ("gyeongsang", "question"),
            "기라":   ("gyeongsang", "explanation"),
            "심더":   ("gyeongsang", "past_tense"),
            "뚝":     ("universal",  "connection_loss"),
        }
        # 강원 방언 마커 추가 (인제군 실제 사용 방언)
        self.gangwon_dialect_map = {
            "가라":   ("gangwon", "go"),
            "머래":   ("gangwon", "question"),
            "야":     ("gangwon", "casual"),
        }

    def extract_from_dialogue(self, dialogues: List[Dict]) -> KoreanPersonaFeatures:
        """대화 로그로부터 특징 추출"""
        features = self._init_features()

        for turn in dialogues:
            text = turn.get("user", "").lower()

            # 방언 패턴 분석 — 경상도
            for marker, (region, intent) in self.dialect_map.items():
                if marker in text:
                    features.dialect_region = region
                    if intent == "respectful_request":
                        features.honorific_preference = "respectful_elderly"

            # 방언 패턴 분석 — 강원도 (인제군 우선)
            for marker, (region, intent) in self.gangwon_dialect_map.items():
                if marker in text and features.dialect_region is None:
                    features.dialect_region = region

            # 감정어 빈도 (정 민감성 추정)
            emotional_words = ["고마워", "걱정", "안심", "기쁘", "서운"]
            if any(ew in text for ew in emotional_words):
                features.emotional_expression_level += 0.1

            # 가격/가치 언급
            if any(kw in text for kw in ["싸게", "비싸", "가성비", "추천"]):
                features.price_sensitivity += 0.15
            if any(kw in text for kw in ["정", "믿음", "이웃", "함께"]):
                features.jeong_sensitivity += 0.2

        # 정규화
        features.emotional_expression_level = min(1.0, features.emotional_expression_level)
        features.price_sensitivity = min(1.0, features.price_sensitivity)
        features.jeong_sensitivity = min(1.0, features.jeong_sensitivity)
        features.confidence_score = min(0.95, 0.5 + len(dialogues) * 0.05)

        return features

    def extract_from_reference(self, nemotron_record: Dict) -> KoreanPersonaFeatures:
        """
        Nemotron 등 참고자료로부터 구조적 특징 추출 (내용은 비움)
        """
        features = self._init_features()
        profile = nemotron_record.get("profile", {})

        if "65" in str(profile.get("age", "")):
            features.honorific_preference = "respectful_elderly"
            features.procedure_tolerance = 2  # 고령: 절차 단순화

        # FIX(버그2): 강원도(인제군)는 gangwon, 경상도와 혼동하지 않음
        region = profile.get("region", "")
        if region == "gangwon":
            features.dialect_region = "gangwon"
        elif region in ("gyeongsang", "gyeongnam", "gyeongbuk"):
            features.dialect_region = "gyeongsang"

        features.data_sources.append("nemotron_structure_ref")
        features.confidence_score = 0.6  # 참고자료는 신뢰도 하향

        return features

    def _init_features(self) -> KoreanPersonaFeatures:
        return KoreanPersonaFeatures(
            trust_network_size=3,
            referral_sensitivity=0.5,
            dialect_region=None,
            honorific_preference="standard",
            emotional_expression_level=0.3,
            peak_activity_hours=[9, 10, 19, 20],
            seasonal_patterns={"winter": 1.0, "chuseok": 1.0},
            procedure_tolerance=3,
            uncertainty_aversion=0.5,
            price_sensitivity=0.5,
            jeong_sensitivity=0.5,
            confidence_score=0.0,
            data_sources=[],
        )
