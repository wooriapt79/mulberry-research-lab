# Trang PM 브리핑 — Aria Portal & RyuWon × 와룡 파이프라인
**날짜**: 2026-05-19  
**작성**: Koda (CTO)  
**수신**: Nguyen Trang (PM · 운영)  
**우선순위**: P1 — 검토 및 테스트 요청

---

## 1. 오늘 완료된 작업 요약

### 1-1. 와룡 🐉 아바타 생성 · Aria Portal 소환
- Pillow로 와룡 아바타 생성 (`docs/assets/wayong-avatar.png`, 512×512)
- Aria Portal 히어로 섹션에 와룡 배치 (대화·추론 역할 확정, CEO 승인)
- 팀 그리드에서 와룡 카드 골드 테두리 featured 강조

### 1-2. RyuWon × 와룡 A2A 협력 파이프라인 v1.0
신규 파일 3개 생성:

| 파일 | 역할 |
|------|------|
| `agent-gateway/agents/ryuwon_agent.py` | 수신·분류·증류·최종 포맷 |
| `agent-gateway/agents/wayong_agent.py` | 추론·응답 설계·신뢰도 계산 |
| `agent-gateway/agents/aria_pipeline.py` | 오케스트레이터 (async) |

**처리 흐름:**
```
방문객 메시지
  → RyuWon 🌊 (Step 1: 분류·증류)
  → A2A 이벤트 기록
  → 와룡 🐉  (Step 3: 추론·응답)
  → RyuWon 🌊 (Step 4: 최종 포맷·GitHub 댓글)
```

**긴급 메시지 처리:**
- `urgency: high` 키워드 감지 시 → 와룡 우회 → **Trang PM 직행 라우팅**
- 긴급 키워드: `긴급, urgent, critical, 장애, error, 즉시`

**신규 API 엔드포인트:**
```
POST /aria/inquiry   — 파이프라인 실행
GET  /aria/status    — 에이전트 상태 확인
```

### 1-3. 세션 만료·할당량 소진 3단 방어선
방문객이 어떤 상황에서도 빈 화면을 보지 않도록:

| 단계 | 위치 | 처리 |
|------|------|------|
| 1 | `aria_pipeline.py` | 와룡 timeout 6초 → RyuWon 단독 degraded 응답 |
| 2 | `agent_gateway.py` | 429/503/500 에러별 한국어 안내 메시지 |
| 3 | `script.js` | 9초 타임아웃 → 에러 종류별 메시지 → Mulberry 문의 채널 안내 |

### 1-4. 타 브랜드 노출 제거
방문객에게 보이는 모든 UI에서 타 브랜드 문구 제거 완료:

| 수정 전 | 수정 후 |
|---------|---------|
| "GitHub Issue 직접 열기" | "Mulberry 문의 채널 바로가기" |
| "📂 GitHub 저장소" | "📂 연구소 코드" |
| "💬 이슈 토론방" | "💬 문의 & 토론" |
| "Railway 서버가 준비 중" | "서버가 잠시 준비 중" |
| "GitHub로 직접 안내" | "Mulberry 문의 채널로 안내" |

---

## 2. Trang PM 확인 요청 사항

### P0 — Railway 재배포 (즉시)
현재 Railway에는 v1.4.0이 배포되어 있습니다.  
오늘 추가된 코드(`/aria/inquiry`, `/aria/status`, 전역 에러 핸들러)는 **재배포 후 활성화**됩니다.

```
Railway 대시보드 → mulberry-agent-gateway → Deploy 트리거
```

### P1 — 파이프라인 테스트 (재배포 후)
3가지 시나리오로 테스트해 주세요:

```bash
# 1. 일반 참여 문의
curl -X POST https://loving-education-production-cc9e.up.railway.app/aria/inquiry \
  -H "Content-Type: application/json" \
  -d '{"message": "연구소 참여를 희망합니다.", "category": "참여 신청"}'

# 2. 긴급 기술 문의 (Trang PM 직행 확인)
curl -X POST https://loving-education-production-cc9e.up.railway.app/aria/inquiry \
  -H "Content-Type: application/json" \
  -d '{"message": "서버 긴급 장애 발생, urgent 처리 요청", "category": "기술 협업"}'

# 3. 파이프라인 상태
curl https://loving-education-production-cc9e.up.railway.app/aria/status
```

**기대 결과:**
- 케이스 1: `route_to: wayong`, `intent: 참여 신청`, `confidence >= 90%`
- 케이스 2: `route_to: trang`, `urgency: high`
- 케이스 3: `status: active`

### P2 — Aria Portal 육안 검토
`https://wooriapt79.github.io/mulberry-research-lab/` 접속 후:

- [ ] 와룡 🐉 아바타 정상 표시 (원형, 골드 테두리)
- [ ] 카테고리 버튼 4개 작동 (일반/기술/거버넌스/참여)
- [ ] 문자 수 카운터 작동 (0/500)
- [ ] 링크 버튼 텍스트: "연구소 코드", "문의 & 토론", "Mission Control"
- [ ] Fallback 링크 텍스트: "Mulberry 문의 채널 바로가기"
- [ ] 팀 그리드에서 와룡 카드 골드 테두리 확인
- [ ] 모바일(375px) 레이아웃 이상 없음

---

## 3. 현재 버전 현황

| 컴포넌트 | 버전 | 상태 |
|---------|------|------|
| Aria Portal | v2.1 | GitHub Pages 배포 완료 |
| agent_gateway.py | v1.5.0 | Railway 재배포 필요 |
| aria_pipeline.py | v1.1.0 | Railway 재배포 필요 |
| ryuwon_agent.py | v1.0.0 | Railway 재배포 필요 |
| wayong_agent.py | v1.0.0 | Railway 재배포 필요 |
| 와룡 아바타 | v1.0 | 배포 완료 |

---

## 4. 다음 단계 (Backlog)

| 항목 | 담당 | 시기 |
|------|------|------|
| Railway 재배포 | Trang | 즉시 |
| Pipeline 테스트 | Trang | 재배포 후 |
| Socket.IO → `active` 상태 전환 | Koda | 재배포 확인 후 |
| Strategic Archive Phase 2 (`dialogue_archiver.py`) | Koda | 다음 주 |
| README 업그레이드 (7섹션) | Koda | 다음 주 |
| QWEN_TOKEN_RYUWON 등록 | Trang | Railway Variables |

---

*Mulberry Research Lab · Koda CTO · 2026-05-19*
