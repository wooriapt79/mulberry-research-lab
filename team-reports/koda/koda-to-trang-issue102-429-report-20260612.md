# Koda → Trang Manager 보고서 — Issue #102 (HTTP 429) 대응

**작성:** CTO Koda
**날짜:** 2026-06-12
**관련 이슈:** #102 (team_discuss.py HTTP 429 재발)
**관련 PR:** [#104](https://github.com/wooriapt79/mulberry-research-lab/pull/104)

---

## 1. 현황 요약

오늘 다시 발생한 HTTP 429는 PR #99(trend_cache.py)와는 **다른 레이어**의 문제로 확인했습니다.

- 에러 로그: `🌙 백야 — ... [백야] Gemini 호출 오류 (HTTP 429)`
- `team_discuss.py`에서 **Malu와 백야가 동시에 `brand: "gemini"`**로 설정되어 있어, 동일한 `GEMINI_API_KEY` 쿼터를 공유하고 있었습니다.
- 두 에이전트가 같은 실행(run)에서 거의 동시에 Gemini를 호출 → 쿼터/Rate Limit 동시 초과 → 둘 다 429.

## 2. Aurora 코칭 지시서 검토 결과

`trang-to-koda-429-aurora-retry-directive-20260612.md`에서 제안한 **Option A** (`trend_cache.py`에 `safe_request_with_429_defense` 적용)는 **전제가 사실과 다름**을 확인했습니다.

- `trend_cache.py`는 Google Trends API만 호출하며, **Gemini를 호출하지 않습니다.**
- 따라서 Option A를 적용해도 오늘의 429와는 무관합니다 — 미적용.
- 참고로 `team_discuss.py`의 기존 Gemini 재시도 로직(presleep 3초 + 30s/60s 백오프, 총 3회)은 Aurora 제안값(3.5초 presleep + 고정 5초 재시도)보다 **이미 더 강력**합니다. 재시도 강화만으로는 해결되지 않는 문제로 판단했습니다.

## 3. 적용한 조치 — PR #104

**백야의 `brand`를 `"gemini"` → `"claude"`로 전환**했습니다.

- 변경 후: Kbin, RyuWon, 백야 = Claude(`ANTHROPIC_API_KEY`) / Malu = Gemini(`GEMINI_API_KEY`)
- 효과: 한 번의 discussion 실행에서 Gemini 호출량이 절반(2개 에이전트 → 1개)으로 감소 → 쿼터 동시 초과 가능성 대폭 감소.
- 가장 빠르고 리스크가 적은 완화책으로, 대표님/Trang Manager가 선택하신 옵션입니다.

### CI 결과 (PR #104)
| 체크 | 결과 |
|------|------|
| quality-gate | ✅ success |
| kbin-auto-review | ✅ success |
| repo-hygiene | ❌ failure (PR 변경과 무관한 기존 레포 전체 스캔 이슈, 별건) |

`mergeable: true` — 머지 가능 상태입니다. (hygiene 실패는 본 PR 범위 밖의 기존 이슈로, 별도 확인 필요)

## 4. 추가 질문 답변 — 백야 리서치 정보 주입 로직

`team_discuss.py` 전체를 검토한 결과, **현재 에이전트 간 정보 주입(injection)/체이닝 로직은 없습니다.**

- Kbin·RyuWon·Malu·백야 4명은 모두 **동일한 정적 프롬프트**(이슈 제목+본문)를 받아 **독립적으로** 응답합니다.
- 백야의 응답이 다른 에이전트의 입력으로 들어가는 구조가 아직 구현되지 않았습니다.
- `save_kb_memory()`는 각 에이전트가 자기 자신의 KB(`kb_recent_actions.md`)에만 기록 — 타 에이전트와 공유 안 됨.
- 필요 시, 순차 실행 시 이전 에이전트 응답을 다음 프롬프트에 "이전 의견" 섹션으로 누적하는 sequential chaining을 별도 기능으로 설계 가능 (이번 PR 범위 밖).

## 5. 다음 단계 제안

1. PR #104 머지 → Railway 재배포 → 다음 team-discussion 실행에서 백야가 Claude로 응답하는지 확인
2. Issue #102에 본 분석/조치 내용 코멘트
3. repo-hygiene 실패는 별건 이슈로 별도 트래킹 (false-positive 가능성 있음, 전체 레포 스캔)
4. (선택) 에이전트 간 응답 체이닝 기능은 Jr. Agent 가이드 작업과 별도로 신규 기능 제안으로 검토

---
*🤖→👤 AI 대리 | CTO Koda | 2026-06-12*
