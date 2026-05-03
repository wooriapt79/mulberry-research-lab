# Auto-generated test — SampleRules
# Generated at: 2026-05-03T20:14:31.258628

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from datetime import datetime
from src.proactive.rules.samplerules import SampleRules, TriggerCondition


def test_check_suggest_umbrella_0_returns_trigger_condition():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "clear"}
    result = rules.check_suggest_umbrella_0(context)
    assert isinstance(result, TriggerCondition)
    assert 0.0 <= result.confidence <= 1.0
    print(f"[PASS] check_suggest_umbrella_0: met={result.met}, confidence={result.confidence:.2f}")

def test_check_morning_greeting_1_returns_trigger_condition():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "clear"}
    result = rules.check_morning_greeting_1(context)
    assert isinstance(result, TriggerCondition)
    assert 0.0 <= result.confidence <= 1.0
    print(f"[PASS] check_morning_greeting_1: met={result.met}, confidence={result.confidence:.2f}")

def test_check_reorder_kimchi_jjigae_0_returns_trigger_condition():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "clear"}
    result = rules.check_reorder_kimchi_jjigae_0(context, user_history={})
    assert isinstance(result, TriggerCondition)
    assert 0.0 <= result.confidence <= 1.0
    print(f"[PASS] check_reorder_kimchi_jjigae_0: met={result.met}, confidence={result.confidence:.2f}")

def test_check_essential_supply_alert_0_returns_trigger_condition():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "clear"}
    result = rules.check_essential_supply_alert_0(context, local_inventory={})
    assert isinstance(result, TriggerCondition)
    assert 0.0 <= result.confidence <= 1.0
    print(f"[PASS] check_essential_supply_alert_0: met={result.met}, confidence={result.confidence:.2f}")

def test_check_companion_checkin_0_returns_trigger_condition():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "clear"}
    result = rules.check_companion_checkin_0(context, user_consent={'explicit_opt_in': False})
    assert isinstance(result, TriggerCondition)
    assert 0.0 <= result.confidence <= 1.0
    print(f"[PASS] check_companion_checkin_0: met={result.met}, confidence={result.confidence:.2f}")


def test_evaluate_all_returns_list():
    rules = SampleRules()
    context = {"current_time": datetime.now(), "weather": "rain"}
    signals = rules.evaluate_all(context)
    assert isinstance(signals, list)
    print(f"[PASS] evaluate_all: {len(signals)}개 신호")


if __name__ == "__main__":
    print("=" * 50)
    print("SampleRules 자동 생성 테스트")
    print("=" * 50)
    test_check_suggest_umbrella_0_returns_trigger_condition()
    test_check_morning_greeting_1_returns_trigger_condition()
    test_check_reorder_kimchi_jjigae_0_returns_trigger_condition()
    test_check_essential_supply_alert_0_returns_trigger_condition()
    test_check_companion_checkin_0_returns_trigger_condition()
    test_evaluate_all_returns_list()
    print("모든 테스트 통과")
