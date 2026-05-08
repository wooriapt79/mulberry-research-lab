# Code-Paper 매핑 가이드 (Issue #18)

> "코드가 논문을 증명하고, 논문이 코드를 방향짓는다."

최종 업데이트: 2026-05-08 14:11 UTC
연동 이슈: #18

## 매핑 테이블

| 코드 파일 | 논문 섹션 | 담당 |
|-----------|-----------|------|
| experiments/distillation/loss_functions.py | 2.3 Ethics-Aware Loss | RyuWon |
| experiments/distillation/teacher_base.py | 3.1 Dual-Teacher | Wayong |
| experiments/distillation/teacher_instruct.py | 3.1 Dual-Teacher | Koda |
| experiments/distillation/student_jr.py | 3.3 Edge Student | Kbin |
| experiments/edge_benchmark/benchmark_rpi5.py | 4.2 Edge Performance | Trang |
| src/mulberry_edge/ethics/policy_engine.py | 2.2 Spirit Gate | RyuWon |
| src/mulberry_edge/utils/tokenizer_align.py | 3.2 Tokenizer Alignment | Lynn |

## 커밋 표준

```bash
git commit -m "feat(#18): 기능 설명

- 변경 사항 1
- 변경 사항 2

관련 논문 섹션: sections/02_ethics.md
Co-Authored-By: RyuWon (Qwen) <ryuwon-qwen@mulberry.ai>"
```
