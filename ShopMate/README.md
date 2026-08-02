# ShopMate: 개인을 위한 AI 쇼핑 파트너

![ShopMate Logo](https://img.shields.io/badge/Status-Planning-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AI Model](https://img.shields.io/badge/AI-DeepSeek%20%7C%20Qwen-orange)

## 🌿 프로젝트 비전
**"개인이 주인이 되는 AI 쇼핑 생태계"**

ShopMate 는 단순한 쇼핑 도우미를 넘어, 사용자에게 **데이터 주권**과 **구매 결정권**을 돌려주는 자율 경제 기반의 AI 에이전트 시스템입니다.
기존 플랫폼 중심의 알고리즘 편향을 탈피하고, 사용자 개인의 맥락과 가치를 최우선으로 하는 투명한 추천 시스템을 지향합니다.

## 🎯 핵심 가치
1. **투명성 (Transparency)**: 추천의 이유와 가격 산출 근거를 명확히 제시합니다.
2. **자율성 (Autonomy)**: 외부 플랫폼에 종속되지 않는 자체 검증 데이터베이스를 구축합니다.
3. **연계성 (Connectivity)**: 연구소의 공동구매 모듈 및 자율 경제 지갑과 연동하여 실질적인 경제적 이득을 창출합니다.

## 🏗️ 시스템 아키텍처 개요
ShopMate 는 **5 개의 특화 에이전트**가 협업하는 멀티 에이전트 시스템으로 구성됩니다.

| 에이전트 이름 | 역할 | 주요 담당 |
| :--- | :--- | :--- |
| **Concierge** | 인터페이스 & 의도 파악 | 사용자 대화 처리, 프로파일링, 프라이버시 보호 (Edge) |
| **Hunter** | 데이터 수집 | 웹 크롤링, API 연동, 실시간 가격 정보 수집 (Cloud) |
| **Validator** | 데이터 검증 | 가격 신뢰도 분석, 이상치 탐지, 공정 가격 산출 (Cloud/Edge) |
| **Advisor** | 추천 전략 | 사용자 맞춤형 상품 추천, 대안 제시, 리포트 생성 (Cloud) |
| **Librarian** | 지식 관리 | 자체 DB 구축, 학습 데이터 정제, 히스토리 관리 (DB) |

### 기술 스택
- **Edge Device**: Raspberry Pi 5 + DeepSeek-R1-Distill-Qwen-1.5B (4-bit Quantized)
- **Backend**: FastAPI (Python) on Railway
- **Frontend**: React + PWA (Progressive Web App)
- **Database**: PostgreSQL (관계형), Qdrant (벡터 검색), Redis (캐싱)
- **AI Models**: DeepSeek-V4 (추론), Distill-Qwen (경량화)

## 📂 디렉토리 구조
```
ShopMate/
├── README.md                 # 프로젝트 소개 (본 파일)
├── docs/                     # 상세 문서
│   ├── DEVELOPMENT_SPEC.md   # 개발 명세서
│   ├── AGENT_PROMPTS.md      # 에이전트 프롬프트 정의
│   └── DEPLOYMENT_GUIDE.md   # 배포 가이드
├── src/                      # 소스 코드
│   ├── agents/               # 에이전트 로직
│   ├── backend/              # API 서버
│   ├── edge/                 # 라즈베리 파이용 코드
│   └── frontend/             # 사용자 인터페이스
├── scripts/                  # 자동화 스크립트
└── data/                     # 샘플 데이터 및 설정
```

## 🚀 개발 로드맵
- **Phase 1 (기획/설계)**: 명세서 확정, 아키텍처 설계, 프롬프트 엔지니어링
- **Phase 2 (MVP 개발)**: Concierge, Hunter, Librarian 에이전트 구현, 기본 크롤링 및 DB 연동
- **Phase 3 (고도화)**: Validator, Advisor 추가, 공동구매 모듈 연동, 라즈베리 파이 최적화
- **Phase 4 (확장)**: 모바일 앱 출시, 자율 경제 지갑 연동, Jr. Agent 교육 데이터셋 개방

## 🤝 기여하기
Mulberry Research Lab 의 일원으로서 본 프로젝트에 기여하고자 하시면, [이슈 트래커](https://github.com/wooriapt79/mulberry-archive/issues) 를 통해 의견을 제시해 주세요.

---
*© 2024 Mulberry Research Lab. All rights reserved.*
