2. YAML → Python 클래스 컨버터 스크립트 (`trigger_rule_converter.py`)


####!/usr/bin/env python3
##### src/proactive/trigger_rule_converter.py

Mulberry Proactive Trigger Rule Converter
YAML 규칙 파일을 Python 클래스 코드로 자동 변환
- Spirit Score 검증 훅 자동 삽입
- 에지 퍼스트 실행 패턴 지원
- Korean Persona 톤 선택 연동.
---  
experiments/image-agent/paper-airplan/mulberry-agent-factory-final/src/proactive

### YAML → Python 변환
#### 입력: 예 proactive_triggers_inje.yaml
---
proactive_rules:
  time_based:
    - condition: "weather == 'rain' AND time BETWEEN 17:00-20:00"
      action: "suggest_warm_food"
      spirit_check: true
      
  pattern_based:
    - condition: "user_order_history['kimchi_jjigae'] >= 3 AND last_order > 7days"
      action: "reorder_suggestion"
      max_frequency: "once_per_week"
      
  context_based:
    - condition: "user_location == 'food_desert' AND inventory['essential'] < 3"
      action: "essential_supply_alert"
      priority: "high"
      
  emotion_based:
    - condition: "text_sentiment == 'lonely' AND dialect_region == 'inje'"
      action: "empathetic_check_in"
      tone: "respectful_elderly"
      requires_explicit_consent: true


---
### **🎤 발표자 노트 (핵심 슬라이드별)**

**Slide 1 (해법 소개)**
"기존 에이전트는 '명령을 기다리는 비서'였다면, 
Mulberry 는 '맥락을 읽는 동반자'를 지향합니다.
핵심은 '방해하지 않는 예측' — 사용자가 원할 때, 원하는 방식으로 제안하는 기술입니다."

**Slide 2 (프라이버시)**
"에지 퍼스트는 선택이 아니라 필수입니다. 개인정보는 사용자 기기 안에서만 처리되고,
서버에는 '익명화된 교훈'만 전달됩니다.
이것이 Mulberry 가 약속하는 '기술적 프라이버시'입니다."

**Slide 3 (Spirit Score)**
"윤리는 사후 검증이 아니라, 설계 단계부터 내장되어야 합니다.

Spirit Score 는 '이 제안이 사람을 존중하는가?'를 0.0~1.0 으로 정량화하는 우리의 나침반입니다."

**Slide 4 (역할 분담)**
"기술만으로는 부족합니다.

기획자의 현장 감각, 연구자의 윤리 통찰,개발자의 실행력이 만날 때,
비로소 '사람을 위한 예측'이 탄생합니다."


