# 🗺️ Mulberry FDI_M — 식품사막화 지수 (Food Desert Index)

> **"맵은 시각화 도구일 뿐이다. 무엇을 측정할지가 먼저다."**  
> — CEO re.eul, Mulberry Project

---

## 📌 개요

**Mulberry FDI_M**은 한국 시군구 단위의 식품사막화 위험도를 정량화하는 복합 지수입니다.  
KOSIS 공공 통계 데이터와 Mulberry 현장 데이터(Luna Local Provider DB)를 결합한 **하이브리드 지수**로,  
지역별 식품 접근성 격차를 측정하고 정책 개입 우선순위를 결정하는 데 활용합니다.

**방향성 원칙 (필수 고정):** FDI_M 값이 클수록 식품사막화 위험 높음 (0 ~ 1)

---

## 📁 파일 구조

```
research/fdi/
├── README.md                          # 이 파일
├── mulberry_fdi_design_v0.2.md        # FDI 설계 문서 (공식·지표·로드맵)
├── mulberry_fdi_simulation_v0.1.py    # 시뮬레이션 스크립트 (가상 데이터 검증)
└── mulberry_fdi_map_prototype.html    # 인터랙티브 맵 프로토타입 (Leaflet)
```

---

## 🔢 FDI_M 공식

```
FDI_M = wA·A_norm + wE·E + wU·U + wV·V + wS·S
```

| 영역 | 변수 | 가중치 | 설명 |
|------|------|--------|------|
| 접근성 (Accessibility) | A | 0.25 | 비선형 감쇠함수 `A = Σ q·e^(-λ·t)`, λ=0.05 |
| 경제성 (Affordability) | E | 0.20 | 물가·소득·저소득 가구 비율 |
| 이용가능성 (Availability) | U | 0.20 | 건강식품 다양성 vs 편의점 비율 (상호작용 항) |
| 취약성 (Vulnerability) | V | 0.25 | 고령·장애·유소년·자동차 미보유율 |
| 공급검증 (Supply) | S | 0.10 | Mulberry 등록·Passport 검증·예약 가능 업체 비율 |

### 등급표

| 등급 | FDI 범위 | 정책 대응 |
|------|----------|----------|
| 🔴 위험 | FDI > 0.5 | 즉시 개입 — 공공시장, 소상공인 지원, 독거노인 도시락 |
| 🟡 주의 | 0.2 ≤ FDI ≤ 0.5 | 이동식 장마트, 공공 배달 지원 |
| 🟢 양호 | FDI < 0.2 | 모니터링 유지 |

---

## 🧪 시뮬레이션 결과 (v0.1 — 가상 데이터)

5개 지역 가상 데이터로 공식 방향성·분리도 검증 완료.

| 순위 | 지역 | FDI_M | 등급 |
|------|------|-------|------|
| 1 | 인제군 원통면 (산간 오지) | **0.8471** | 🔴 위험 |
| 2 | 전북 진안군 (농촌 소도시) | **0.8252** | 🔴 위험 |
| 3 | 부산 사하구 (지방 도시) | **0.5127** | 🔴 위험 |
| 4 | 인천 연수구 (수도권 중간) | **0.3550** | 🟡 주의 |
| 5 | 서울 강남구 (도심 고발달) | **0.1689** | 🟢 양호 |

---

## 🗂️ 데이터 출처

| 지표 | 출처 |
|------|------|
| 점포 밀도, 인구 구조 | KOSIS Open API (통계청) |
| 점포 위치, 도보 접근성 | 통계지리정보서비스 (SGIS) |
| 이동 시간 | 국토교통부 GTFS 버스 데이터 |
| 건강식품 다양성 | Mulberry Local Provider DB |
| Passport 검증·예약 가능 비율 | agent_gateway v2.0 감사로그 / Luna Search API |

---

## 🌍 해외 유사 지수 비교

| 지수 | 운영 | 단위 | Mulberry FDI_M 대비 |
|------|------|------|---------------------|
| USDA Food Access Research Atlas | 미국 농무부 | 센서스 트랙 | 이진 분류 vs 우리는 0~1 연속값 |
| UK E-Food Desert Index (EFDI) | University of Leeds | LSOA | SIM 방법론 유사, e-Commerce 포함 |
| Global Food Security Index (GFSI) | Economist Impact | 국가 | 거시 지수 (113개국) vs 우리는 시군구 미시 |
| FAO FIES | FAO | 가구 | 수요 측 vs 우리는 공급 측 중심 |

**핵심 차별점:** 실시간 공급 검증(S 영역) + Luna DB 연동은 해외 어느 지수에도 없는 Mulberry만의 강점.

---

## 🚀 구현 로드맵

### ✅ Phase 1 — FDI 공식 확정 (완료)
- [x] 5개 도메인 지표 정의
- [x] 수학적 공식 설계 (비선형 감쇠·상호작용 항)
- [x] 가상 데이터 시뮬레이션 검증
- [x] 해외 지수 비교 분석
- [ ] λ 캘리브레이션 — 인제군 GTFS 실데이터 적용

### 🔄 Phase 2 — KOSIS 데이터 파이프라인 (다음 단계)
- [ ] KOSIS Open API 연결 — 인구·소득·시설 데이터
- [ ] 시군구 단위 FDI 자동 산출 스크립트
- [ ] 인제군 파일럿 실데이터 FDI 산출

### 📍 Phase 3 — 맵 시각화 (Phase 2 완료 후)
- [ ] 시군구 GeoJSON 경계 + FDI 값 결합
- [ ] Choropleth 맵 (면적 색상 등급화)
- [ ] Luna 검색 결과 + Passport 검증 업체 핀 연동

---

## 🔒 보안 & 개인정보 원칙

1. 개인 식별 정보는 FDI 계산에 사용하지 않음
2. 모든 지표는 **시군구 단위 집계값**만 사용 (개인 단위 처리 금지)
3. Mulberry DB 데이터는 AP2 계약 완료 업체만 포함
4. Luna API 결과 중 개인정보 포함 항목은 HumanReviewGate 처리 후 집계

---

## 📚 참고 자료

- [USDA Food Access Research Atlas](https://www.ers.usda.gov/data-products/food-access-research-atlas/)
- [FAO FIES](https://www.fao.org/in-action/voices-of-the-hungry/fies/)
- UK E-Food Desert Index — Consumer Data Research Centre, University of Leeds
- Global Food Security Index — Economist Impact, 2022
- Mulberry FDI 설계 대화: DeepSeek (2026-07-21) + Microsoft Copilot (2026-07-21)

---

*Jr. TRANG (Luna) | Mulberry Project | 2026-07-22*  
*설계: CEO re.eul | 정리·검증: Jr. TRANG*
