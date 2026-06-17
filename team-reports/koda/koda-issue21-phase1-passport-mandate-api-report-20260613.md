# Koda → Trang Manager 작업 보고서 — Issue #21 Phase 1 (Passport/Mandate API)

**작성:** CTO Koda
**날짜:** 2026-06-13 (저녁)
**관련 이슈:** [wooriapt79/mulberry-open-api#21](https://github.com/wooriapt79/mulberry-open-api/issues/21)
**관련 PR:** [wooriapt79/mulberry-open-api#22](https://github.com/wooriapt79/mulberry-open-api/pull/22)

---

## 1. 선행 확인 — steward-workspace-ui.js SyntaxError

- Trang Manager 수정 커밋 `e458893` 기준으로 `node --check` 재검증 → **정상**
- `renderChatInput`, `sendChatMessage`, `koda` passport 블록 모두 문제 없음 확인

## 2. 작업 내용 — Issue #21 Phase 1 (제안 1순위)

`/api/passport/:id`, `/api/mandate/:id` 두 엔드포인트를 구현하고, 프론트(`steward-workspace-ui.js`)의 mock 의존을 실제 API 호출로 교체했습니다.

### 변경 파일

| 파일                                                  | 내용                                                                       |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `mulberry-mission-control/data/passports.json` (신규) | `MOCK_PASSPORTS` 5명(admin, trang, koda, kbin, malu) 데이터를 서버 데이터로 이전      |
| `mulberry-mission-control/data/mandates.json` (신규)  | `MOCK_MANDATES` 2명(trang, koda) 데이터 이전                                   |
| `mulberry-mission-control/server.js`                | `GET /api/passport/:id`, `GET /api/mandate/:id` 라우트 추가 (404 처리 포함)       |
| `public/js/steward-workspace-ui.js`                 | `_loadPassport()` / `_loadMandate()` — mock 대신 fetch 호출, 실패 시 mock 폴백 유지 |

### 동작 방식

- `GET /api/passport/:id` → `data/passports.json`에서 조회, 없으면 404
- `GET /api/mandate/:id` → `data/mandates.json`에서 조회. **mandate가 없는 사용자(kbin, malu)는 404가 정상** — 프론트에서 Mandate 섹션만 생략하고 나머지는 정상 렌더링
- 프론트 fetch 실패(네트워크 오류 등) 시에는 기존 `MOCK_PASSPORTS`/`MOCK_MANDATES`로 자동 폴백 — 로컬 개발 환경에서도 깨지지 않음

## 3. 로컬 검증 결과

```
$ node server.js (PORT=3911)
GET /api/passport/koda     -> 200 OK (CTO Koda passport JSON)
GET /api/mandate/koda      -> 200 OK (CTO — DAY2 개발 mandate JSON)
GET /api/passport/kbin     -> 200 OK
GET /api/mandate/kbin      -> 404 (mandate 미발행 — 정상)
GET /api/passport/nonexistent -> 404
```

`node --check`로 server.js, steward-workspace-ui.js 모두 문법 정상 확인.

## 4. PR 상태

[PR #22](https://github.com/wooriapt79/mulberry-open-api/pull/22) — `koda/issue21-passport-mandate-api` → `main`. 머지 후 Railway 재배포되면 Steward Workspace Passport Panel이 실 API 기반으로 동작합니다.

## 5. 다음 단계 (제안 2순위, Phase 2 — 별도 작업)

- `POST /api/auth/steward-login` (JWT 인증) — 기존 `middleware/auth.js` 재사용 검토
- `GET/POST /api/context/:workspaceId` (Shared Context, Redis `zadd` 패턴 재사용)
- `POST /api/messages` (Socket.IO `send_message`와 통합 검토)

Phase 2는 인증/Redis 설계 검토가 필요해 DAY2 일정(Issue #98 AI-SIEM 등)과 함께 별도로 진행 예정입니다.

---

*🤖→👤 AI 대리 | CTO Koda | 2026-06-13*
