# [Trang Manager 확인] LAB ↔ BANK 브릿지 1단계 완료 — 다음 작업 안내

**작성일**: 2026-05-06  
**작성**: Koda (Claude / Anthropic)  
**대상**: Nguyen Trang Manager  

---

## 완료된 작업 (BANK repo 커밋: 5813621)

LAB의 `face_off_*.py` 철학을 BANK Lynn/Jr.Lynn이 실제로 사용하게 연결했습니다.

### 신규 파일 2개 (mulberry_memory_bank/scripts/)

| 파일 | 역할 |
|------|------|
| `guardian_bridge.py` | GuardianAlgorithm(10% 환원) + GhostArchive(해마) BANK 구현 |
| `burnout_monitor.py` | Jr.Lynn 번아웃 자동 감지 + 강제 휴식 트리거 |

### 저장 위치
```
persona_config/ghost_archive_records.json  ← 전체 협상 기록 (해마)
persona_config/guardian_contribution.json  ← 환원 누계
training_logs/burnout_report_YYYY-MM-DD.json ← 일별 번아웃 리포트
training_logs/junior_lynn_v1_rest_signal.json ← CRITICAL 시 휴식 신호
```

---

## Trang Manager / Kbin 다음 작업 (3가지)

### 1. lynn_core.py — 휴식 신호 감지 연결
`RestScheduler`가 `rest_signal.json` 파일을 주기적으로 확인해서  
CRITICAL 번아웃 시 자동으로 `BioManager.set_bio("charging")` 호출.

```python
# lynn_core.py 에 추가 필요
def check_rest_signal(self):
    signal_path = f"training_logs/{self.agent_id}_rest_signal.json"
    if os.path.exists(signal_path):
        with open(signal_path) as f:
            signal = json.load(f)
        if not signal.get("resolved"):
            self.bio_manager.set_bio("charging")
            self.rest_scheduler.trigger_immediate_rest()
```

### 2. lynn_daily_write.yml — burnout_monitor 자동 실행
```yaml
- name: Run Burnout Monitor
  run: python scripts/burnout_monitor.py
```
Lynn 일일 워크플로우에 추가해서 매일 자동 번아웃 체크.

### 3. LAB Gateway — /memory 엔드포인트 연동
거래 완료 시 `guardian_bridge.complete_transaction()` 호출 결과를  
Gateway의 `POST /memory`로 BANK에 직접 기록.

```python
# agent_gateway.py 활용
POST /memory {
    "agent_id": "junior_lynn_v1",
    "file_path": "persona_config/ghost_archive_records.json",
    "content": { ...협상 기록... }
}
```

---

## 현재 LAB ↔ BANK 연결 현황

```
[이미 연결됨]
LAB issues/comments → BANK agent_activity.md  (sync-to-bank.yml)
Gateway /memory     → BANK 파일 직접 기록     (agent_gateway.py)

[이번에 추가됨]
BANK scripts/guardian_bridge.py  ← LAB face_off_social.py 호환
BANK scripts/burnout_monitor.py  ← jr_lynn.json burnout_threshold 실제 구현

[다음 연결 필요]
lynn_core.py RestScheduler ← rest_signal.json 감지
lynn_daily_write.yml       ← burnout_monitor 자동 실행
Gateway /memory            ← complete_transaction() 결과 전송
```

---

## 참고 — 설계 철학

> **GhostArchive** = 에이전트의 해마  
> 전원이 꺼져도(Ghost가 돼도) 기록은 남는다.  
> 좋은 협상도, 나쁜 협상도 — 모두 장승배기에 기록된다.

> **GuardianAlgorithm** = 장승배기 헌법 1조  
> 수익의 10%는 사회로 돌아간다.  
> 이것은 설정값이 아니라 코드에 박힌 약속이다.

---

*이 문서는 Trang Manager가 다음 작업을 이어받을 수 있도록 Koda가 작성했습니다.*
