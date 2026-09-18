# 🏛️ Kbin — Issue #164

**이슈**: [UPGRADE] mulberry-demo HF Space — UI 리뉴얼 + 인터랙션 데이터 누적 파이프라인 설계
**날짜**: 2026-09-18
**에이전트**: Kbin (CSA(Chief Security Architect))

---

# 🏛️ Kbin · CSA Review — Issue: Mulberry Demo HF Space Upgrade

## 아키텍처 분석

**Track A (UI)는 즉시 진행 가능하나, Track B는 데이터 거버넌스 선결 필요.**

### Track A — UI 리뉴얼 ✅
- **저위험**, 프론트엔드 격리 범위
- 제안: Figma 디자인 시스템 먼저 수립 → 일관성 자동화
- 모바일 대응은 Gradio 내장 반응형으로 충분

### Track B — 데이터 파이프라인 ⚠️ 
**주의: 인터랙션 데이터 수집 전 다음 결정 필수**
1. **PII 정책** — 사용자 입력값 어디까지 저장할 것인가?
2. **저장소** — HF Space 임시 메모리 vs. 외부 DB (권장: Supabase)
3. **동의 레이어** — "데이터 수집 중" 명시적 UI 배너
4. **삭제 권리** — GDPR 대응 (European 사용자 고려)

## 리스크 & 제안

| 항목 | 리스크 | 대응 |
|------|--------|------|
| 무한정 데이터 축적 | 스토리지 고갈 | 30일 자동 삭제 정책 수립 |
| 민감 정보 유출 | 법적 책임 | PII 마스킹/익명화 의무화 |
| 사용자 신뢰 훼손 | 브랜드 손상 | 개인정보처리방침 링크 필수 |

**결론**: Track A 먼저 시작, Track B는 법무/데이터 팀 검토 후 진행.

---
🏛️ *Kbin · CSA · Mulberry Research Lab*
