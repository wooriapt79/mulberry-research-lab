# Mulberry Research Package — Issue #18
Ethics-Aware Knowledge Distillation for Edge AI

생성일시: 2026-05-08 14:11 UTC
연동 이슈: #18 (https://github.com/wooriapt79/mulberry-research-lab/issues/18)

## 빠른 시작

```bash
cd research/#18_ethics_distillation
make setup       # 가상환경 + 의존성 설치
make experiment  # 첫 실험 실행
make paper       # 논문 초안 자동 업데이트
```

## 디렉토리 구조

```
#18_ethics_distillation/
  experiments/
    distillation/    -- 지식 증류 실험 코드
    edge_benchmark/  -- RPi5 벤치마크
  src/mulberry_edge/
    ethics/          -- Spirit Score 정책 엔진
    utils/           -- 토크나이저 정렬 도구
  data/
    distilled_traces/ -- 실험 결과 저장
    scenarios/        -- 인제 시나리오 100개
  configs/            -- 실험 설정 파일
  paper/sections/     -- 논문 섹션 초안
  tests/ethics/       -- 윤리 게이트 단위 테스트
  docs/               -- 코드-논문 매핑 문서
```

## Mulberry 연구 윤리

- 투명성: 모든 설정/코드 버전 관리 및 공개
- 재현성: requirements.txt + Makefile + 시드(42) 고정
- 윤리 검증: Spirit Score 검증이 파이프라인에 내재화
- 공동체 기여: Apache 2.0 라이선스
