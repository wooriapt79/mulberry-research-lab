# tool_traces — 도구 사용 감사 로그

백야 제안 + CEO re.eul 승인 (2026-06-02)

## 목적
모든 에이전트의 도구 사용 이력을 누적 보관.
투명성·감사·교육 데이터화.

## 폴더 구조
```
tool_traces/
  baekya/   ← intel.search_global, logic.validate_redteam, sandbox.execute_code
  koda/     ← terminal.exec, file.write, github.commit 등
  kbin/     ← governance_review, document_generation 등
  ryuwon/   ← ethics_review, agency.semantic_search 등
  malu/     ← vision.analyze, ap2.payment_gateway(스텁) 등
  trang/    ← sensory.rhythm_engine, pm_escalation 등
```

## 로그 포맷 (.jsonl)
```json
{"timestamp":"2026-06-02T00:00:00Z","agent":"baekya_intel","tool":"intel.search_global","query":"AI 트렌드","result_summary":"성공","spirit_score":0.92}
```
