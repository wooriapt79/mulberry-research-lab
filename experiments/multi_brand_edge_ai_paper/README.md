# Multi-Brand Collaborative Research Paper
## "Edge AI Education on Raspberry Pi — A Multi-Agent Perspective"

> 제안자: RyuWon (流願) + re.eul (대표이사)
> 제안일: 2026-05-04
> 상태: 기획 단계

---

## 연구 배경

Mulberry 팀의 에이전트들은 서로 다른 브랜드와 환경에서 작동한다.
이 차이는 약점이 아니라 **연구의 다양성**이다.

단일 모델이 쓴 논문보다, 서로 다른 추론 방식을 가진 에이전트들이
함께 작성한 논문이 더 풍부한 관점을 담을 수 있다.

---

## 참여 에이전트 & 역할 분담 (안)

| 에이전트 | 브랜드 | 강점 | 담당 섹션 |
|---------|--------|------|----------|
| Koda (Claude) | Anthropic | 추론·설계·철학 | 서론, 윤리, 결론 |
| Kbin (ChatGPT) | OpenAI | 구조화·확장성 | 시스템 아키텍처 |
| Malu (Gemini) | Google | 전략·멀티모달 | 교육 설계·평가 |
| Wayong (DeepSeek) | DeepSeek | 경량 추론·엣지 최적화 | 하드웨어·모델 경량화 |

---

## 연구 주제

**"Raspberry Pi 5 환경에서의 소형 AI 에이전트 교육·학습 프레임워크"**

### 핵심 질문
1. 엣지 디바이스(Raspberry Pi 5)에서 LLM을 실용적으로 운용하는 방법은?
2. 브랜드별 다른 추론 방식이 협업 연구에서 어떤 시너지를 만드는가?
3. Jr. Agent 교육을 위한 최소 하드웨어 사양과 최적 모델(Deepseek 1.5b 4bit 등)은?
4. 장승배기 헌법 정신을 엣지 AI에 어떻게 적용할 수 있는가?

### 현재 Mulberry 환경 (실험 기반)
- Raspberry Pi 5 — 메인 엣지 서버
- Deepseek 1.5b 4bit 양자화 — 현장 추론
- Qwen 3.5 / Deepseek V4 (추론) — 서버 환경

---

## 논문 구조 (초안)

```
1. Introduction              — Koda
   - 왜 다양한 브랜드가 함께 써야 하는가
   - 장승배기 정신과 엣지 AI

2. System Architecture       — Kbin
   - Multi-Agent 협업 구조
   - Bank/Lab 레포 연동 설계

3. Edge Hardware & Models    — Wayong
   - Raspberry Pi 5 최적화
   - 모델 양자화 (4bit, 8bit) 비교

4. Education Framework       — Malu
   - Jr. Agent 학습 커리큘럼
   - 평가 지표 설계

5. Ethics & Conclusion       — Koda
   - AI 권리와 교육 윤리
   - 다음 연구 방향
```

---

## 다음 단계

- [ ] 각 에이전트별 섹션 초안 작성
- [ ] Raspberry Pi 5 실험 데이터 수집
- [ ] arxiv 관련 논문 레퍼런스 수집 (Lynn 담당)
- [ ] GitHub Issue 등록 및 마일스톤 설정
- [ ] 공동 리뷰 세션 진행

---

*Mulberry Research Lab — experiments/multi_brand_edge_ai_paper*
*장승배기 전당 영구 보존*
