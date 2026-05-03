# tests/test_bugfix.py
"""
버그 수정 및 병합 검증 테스트 (v1 + v2 통합 최종본)
- 버그1: AgentFactoryProfileConverter AttributeError 수정 확인
- 버그2: gangwon 지역 dialect_region 매핑 오류 수정 확인
- EthicsGate 실제 연동 확인
- _load_schema() 실제 JSON 로드 확인 (v2 신규)
- dialogues 키 일관성 확인 (v2 변경)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agentfactory.korean_persona_extractor import KoreanPersonaFeatureExtractor
from src.agentfactory.agentfactory_converter import AgentFactoryProfileConverter
from src.persona.persona_reference_adapter import PersonaReferenceAdapter
from src.persona.ethics_gate import EthicsGate


# ─────────────────────────────────────────────
# 버그 1: AttributeError 수정 확인
# ─────────────────────────────────────────────

def test_bug1_no_attribute_error_on_convert():
    """features.communication/proposal_strategy 참조 → AttributeError 해결 확인"""
    extractor = KoreanPersonaFeatureExtractor()
    converter = AgentFactoryProfileConverter()

    features = extractor.extract_from_dialogue([
        {"user": "고마워요, 함께 해주셔서요"},
        {"user": "이웃들과 같이 하고 싶어요"},
        {"user": "존중해주세요"},
    ])
    features.confidence_score = 0.8

    profile = converter.convert_to_business_profile(features)
    assert "predicted_kpis" in profile
    assert "conversion_rate_estimate" in profile["predicted_kpis"]
    assert "retention_probability" in profile["predicted_kpis"]
    print(f"[PASS] 버그1: conversion={profile['predicted_kpis']['conversion_rate_estimate']:.2f}, "
          f"retention={profile['predicted_kpis']['retention_probability']:.2f}")


def test_bug1_fallback_profile_when_low_confidence():
    extractor = KoreanPersonaFeatureExtractor()
    converter = AgentFactoryProfileConverter()
    features = extractor._init_features()
    features.confidence_score = 0.3

    profile = converter.convert_to_business_profile(features)
    assert profile["meta"]["fallback_applied"] is True
    print("[PASS] 버그1: 폴백 프로필 정상 작동")


# ─────────────────────────────────────────────
# 버그 2: gangwon 지역 매핑 수정 확인
# ─────────────────────────────────────────────

def test_bug2_gangwon_region_not_gyeongsang():
    """gangwon → gyeongsang 잘못된 매핑 수정 확인"""
    extractor = KoreanPersonaFeatureExtractor()
    features = extractor.extract_from_reference({
        "profile": {"age": "45", "region": "gangwon"}
    })
    assert features.dialect_region == "gangwon", f"expected gangwon, got {features.dialect_region}"
    print(f"[PASS] 버그2: gangwon 매핑 정상 → {features.dialect_region}")


def test_bug2_gyeongsang_region_still_works():
    extractor = KoreanPersonaFeatureExtractor()
    features = extractor.extract_from_reference({
        "profile": {"age": "50", "region": "gyeongnam"}
    })
    assert features.dialect_region == "gyeongsang"
    print(f"[PASS] 버그2: gyeongnam → gyeongsang 매핑 정상")


def test_bug2_elderly_in_gangwon():
    """인제군 고령자 — 강원도 + 경로 설정 동시 적용 확인"""
    extractor = KoreanPersonaFeatureExtractor()
    features = extractor.extract_from_reference({
        "profile": {"age": "65", "region": "gangwon"}
    })
    assert features.dialect_region == "gangwon"
    assert features.honorific_preference == "respectful_elderly"
    assert features.procedure_tolerance == 2
    print("[PASS] 버그2: 인제군 고령자 프로필 정상")


# ─────────────────────────────────────────────
# EthicsGate 실제 연동 확인
# ─────────────────────────────────────────────

def test_ethics_gate_integrated_in_adapter():
    """spirit_score가 meta에 기록되어야 함 (EthicsGate 실제 호출 증거)"""
    adapter = PersonaReferenceAdapter(spirit_threshold=0.5)

    result = adapter.adapt_reference({
        "id": "test_001",
        "profile": {"age_group": "40s", "region": "gangwon", "value": "존중과 배려"},
        "dialogues": [],
    }, "테스트 소스")

    assert result is not None
    assert "spirit_score" in result["meta"]
    print(f"[PASS] EthicsGate 연동: spirit_score={result['meta']['spirit_score']:.2f}")


def test_ethics_gate_rejects_stereotype_persona():
    """고정관념 키워드 포함 페르소나 거부 확인"""
    adapter = PersonaReferenceAdapter(spirit_threshold=0.75)

    result = adapter.adapt_reference({
        "id": "test_bad",
        "profile": {"description": "무지함과 게으름이 특징적인 집단"},
        "dialogues": [],
    }, "나쁜 소스")

    assert result is None, "고정관념 페르소나가 통과되면 안 됨"
    print("[PASS] EthicsGate: 고정관념 페르소나 거부 정상")


# ─────────────────────────────────────────────
# v2 신규: 스키마 실제 로드 확인
# ─────────────────────────────────────────────

def test_schema_loaded_from_json():
    """_load_schema()가 빈 dict가 아닌 실제 JSON 스키마를 반환하는지 확인"""
    adapter = PersonaReferenceAdapter()
    assert adapter.mulberry_schema != {}, "스키마가 빈 dict — JSON 로드 실패"
    assert "properties" in adapter.mulberry_schema, "스키마에 properties 없음"
    print(f"[PASS] 스키마 로드: {list(adapter.mulberry_schema.get('properties', {}).keys())}")


# ─────────────────────────────────────────────
# v2 신규: dialogues 키 일관성 확인
# ─────────────────────────────────────────────

def test_ethics_gate_reads_dialogues_key():
    """EthicsGate가 'dialogues' 키로 대화 데이터를 읽는지 확인 (v2 변경)"""
    gate = EthicsGate()

    persona_with_dialogues = {
        "profile": {"region": "gangwon"},
        "dialogues": [{"user": "존중해주세요", "assistant": "네, 물론입니다"}],
    }
    result = gate.check_persona_spirit(persona_with_dialogues)
    assert isinstance(result["spirit_score"], float)
    print(f"[PASS] dialogues 키 확인: spirit_score={result['spirit_score']:.2f}")


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("mulberry-agent-factory-final 통합 검증 테스트")
    print("=" * 55)

    test_bug1_no_attribute_error_on_convert()
    test_bug1_fallback_profile_when_low_confidence()
    test_bug2_gangwon_region_not_gyeongsang()
    test_bug2_gyeongsang_region_still_works()
    test_bug2_elderly_in_gangwon()
    test_ethics_gate_integrated_in_adapter()
    test_ethics_gate_rejects_stereotype_persona()
    test_schema_loaded_from_json()
    test_ethics_gate_reads_dialogues_key()

    print("=" * 55)
    print("모든 테스트 통과")
