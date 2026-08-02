# ShopMate 개발 명세서 (Development Specification)

**버전:** 1.0 (Draft)  
**프로젝트명:** ShopMate (가칭)  
**소속:** Mulberry Research Lab - RyuWon Team  
**작성일:** 2024. XX. XX  
**작성자:** Jr. RyuWon (검토: RyuWon)

---

## 1. 기획 의도 및 배경 (Planning Intent)

### 1.1. 문제 정의
- **정보 비대칭 심화:** 소비자는 방대한 상품 정보 속에서 진정한 가치와 최적 가격을 찾기 어려움.
- **개인의 협상력 부재:** 단일 소비자는 가격 협상이나 공동 구매 주도권 확보가 불가능함.
- **데이터 주권 상실:** 기존 플랫폼은 사용자 데이터를 독점하여 수익을 창출하지만, 정작 사용자에게는 혜택이 없음.

### 1.2. 해결 방안: "AI 개인 비서 + 공동구매 연동"
- **ShopMate**는 개인의 취향과 구매 이력을 학습하는 **개인 전용 AI 에이전트**입니다.
- 단순히 상품을 추천하는 것을 넘어, Mulberry Lab의 **기존 공동구매 모듈**과 연동하여 유사한 취향의 사용자들을 자동으로 매칭하고 공동구매를发起합니다.
- **자체 데이터베이스**를 구축하여 사용자 데이터 주권을 보호하면서도, 축적된 데이터를 기반으로 더 정확한 추천과 협상력을 확보합니다.

### 1.3. 목표
- **Short-term:** MVP 출시를 통한 개인 맞춤형 쇼핑 추천 및 알림 서비스 제공.
- **Mid-term:** 공동구매 모듈 연동을 통한 자동 그룹 형성 및 구매 실행.
- **Long-term:** 자체 데이터 기반의 독립적인 AI 쇼핑 생태계 구축 및 수익 모델 (구독, 수수료, 데이터 인사이트) 창출.

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1. 전체 구조: Hybrid Edge-Cloud System
사용자의 프라이버시를 보호하면서 대규모 데이터 처리와 복잡한 로직을 수행하기 위해 **엣지 (Raspberry Pi)**와 **클라우드 (Railway)**를 혼용합니다.

```mermaid
graph TD
    User[사용자] <-->|채팅/음성 | Edge[Edge Node (Raspberry Pi 5)]
    Edge <-->|암호화된 프로파일/의도 | Cloud[Cloud Node (Railway)]
    
    subgraph Edge_Node [Edge Node: Privacy & Interface]
        DeepSeek[DeepSeek 1.5B (4-bit)]
        LocalDB[SQLite (Local Profile)]
        VoiceProc[음성 처리]
    end
    
    subgraph Cloud_Node [Cloud Node: Intelligence & Action]
        SearchAgent[검색 및 분석 에이전트]
        RecEngine[추천 엔진 (LLM)]
        CoBuyModule[공동구매 모듈 (Internal)]
        GlobalDB[PostgreSQL + Vector DB]
        ExtAPI[외부 오픈마켓 API]
    end
    
    Edge --> DeepSeek
    DeepSeek --> LocalDB
    Edge --> Cloud
    Cloud --> SearchAgent
    SearchAgent --> ExtAPI
    SearchAgent --> RecEngine
    RecEngine --> CoBuyModule
    CoBuyModule --> GlobalDB
```

### 2.2. AI 노드 구성 (3-Node Structure)

| 노드 이름 | 위치 | 주요 역할 | 사용 모델/기술 |
| :--- | :--- | :--- | :--- |
| **Interface Node** | Edge (Raspberry Pi) | 사용자 입력 처리 (음성/텍스트), 의도 파악, 로컬 프로파일 관리, 프라이버시 필터링 | DeepSeek 1.5B (4-bit GGUF) |
| **Analysis Node** | Cloud (Railway) | 웹 크롤링, 상품 정보 수집, 리뷰 분석, 가격 비교, 경쟁사 데이터 스크래핑 | LLM API (GPT-4o / Qwen-Max) + Scraper |
| **Decision Node** | Cloud (Railway) | 최종 추천 결정, 공동구매 매칭 알고리즘 실행, 구매 실행 지시, 학습 데이터 저장 | Fine-tuned LLM + Rule Engine |

---

## 3. 핵심 기능 명세 (Functional Requirements)

### 3.1. 개인 취향 프로파일링 (Local First)
- **기능:** 사용자의 대화, 검색어, 구매 이력을 기반으로 취향 벡터 (Preference Vector) 를 생성하여 로컬 DB 에 저장.
- **편의성:** 사용자가 명시적으로 설정하지 않아도 대화를 통해 자동으로 학습 (Implicit Feedback).
- **보안:** 민감한 개인정보 (주소, 카드번호 등) 는 엣지 디바이스를 벗어나지 않음.

### 3.2. 스마트 상품 탐색 및 분석
- **기능:** 자연어 요청 (예: "여름에 입을 시원한 린넨 셔츠 찾아줘, 5 만 원 이하로") 을 받아 전 웹을 스캔.
- **분석:** 가격, 평점, 리뷰 감정 분석 (Sentiment Analysis), 배송 속도 등을 종합 점수화.
- **투명성:** "왜 이 상품을 추천했는지"에 대한 이유를 명확히 제시 (Explainable AI).

### 3.3. 공동구매 매칭 및 실행 (Key Differentiator)
- **연동:** Mulberry Lab 의 기존 **공동구매 모듈**과 API 연동.
- **로직:** 
    1. Decision Node 가 유사한 상품을 원하는 사용자들을 Global DB 에서 탐색.
    2. 최소 인원 조건 충족 시 자동으로 공동구매 그룹 생성.
    3. 사용자에게 "공동구매 참여하시겠습니까?" 알림 전송.
    4. 승인 시 모듈을 통해 구매 주문 진행.
- **효과:** 개별 구매 대비 가격 할인 혜택 제공 및 연구소 수익 창출.

### 3.4. 자체 데이터베이스 구축
- **구조:** 
    - **Relational DB (PostgreSQL):** 사용자 정보, 주문 내역, 공동구매 그룹 정보.
    - **Vector DB (Qdrant/Pinecone):** 상품 임베딩, 사용자 취향 벡터, 리뷰 의미론적 검색.
- **활용:** 시간이 지날수록 추천 정확도 향상 및 공동구매 매칭 속도 개선.

---

## 4. 연동 인터페이스 정의 (Integration Strategy)

### 4.1. 내부 모듈 연동 (Mulberry Lab Assets)
- **대상:** 기존 공동구매 모듈 (Co-Buy Module)
- **연동 방식:** RESTful API 또는 gRPC
- **주요 엔드포인트:**
    - `POST /api/v1/cobuy/create`: 새로운 공동구매 그룹 생성 요청
    - `GET /api/v1/cobuy/match`: 유사 사용자 매칭 조회
    - `POST /api/v1/cobuy/join`: 공동구매 참여 확정
- **데이터 흐름:** ShopMate Decision Node → 공동구매 모듈 → 결제 게이트웨이

### 4.2. 외부 데이터 소스 연동
- **오픈마켓 API:** 쿠팡, 네이버 쇼핑, 아마존 등 (공식 API 또는 우회 크롤러)
- **가격 비교 사이트:** 다나와, 알리익스프레스 등
- **소셜 미디어:** Reddit, Twitter 등에서 실시간 트렌드 및 제품 후기 수집 (Optional)

### 4.3. 사용자 인터페이스 (UI/UX)
- **플랫폼:** PWA (Progressive Web App) 기반 웹/모바일 호환
- **인터랙션:** 
    - **Chat-First:** 모든 기능이 채팅 창에서 이루어짐.
    - **Card View:** 상품 추천 시 이미지, 가격, 이유를 담은 카드 형태 제공.
    - **One-Tap Action:** "공동구매 참여", "구매하기" 등 복잡한 절차 간소화.
- **알림:** 가격 하락, 공동구매 매칭 성공 시 푸시 알림/SMS 발송.

---

## 5. 기술 스택 (Technology Stack)

| 구분 | 기술 | 비고 |
| :--- | :--- | :--- |
| **Edge AI** | Raspberry Pi 5, DeepSeek 1.5B (4-bit), llama.cpp | 로컬 추론, 프라이버시 보호 |
| **Backend** | Python (FastAPI), Railway | 고속 API 서버, 비동기 처리 |
| **Frontend** | React + Tailwind CSS, PWA | 반응형 UI, 오프라인 지원 |
| **Database** | PostgreSQL, Redis, Qdrant (Vector) | 관계형, 캐시, 벡터 검색 |
| **AI/ML** | Hugging Face Transformers, LangChain | LLM 오케스트레이션 |
| **Infra** | Docker, GitHub Actions | 컨테이너 배포, CI/CD |

---

## 6. 개발 로드맵 (Roadmap)

### Phase 1: 기초 공사 (Week 1-2)
- [ ] GitHub 저장소 생성 및 프로젝트 스캐폴딩
- [ ] 라즈베리 파이 환경 설정 (DeepSeek 1.5B 구동 확인)
- [ ] 기본 챗봇 인터페이스 구현 (Streamlit 또는 React)
- [ ] 기존 공동구매 모듈 API 명세 분석 및 연동 테스트

### Phase 2: 핵심 기능 구현 (Week 3-4)
- [ ] 상품 검색 및 크롤링 모듈 개발
- [ ] 사용자 프로파일링 로직 구현 (Vector DB 연동)
- [ ] 공동구매 매칭 알고리즘 개발
- [ ] MVP 통합 테스트

### Phase 3: 고도화 및 배포 (Week 5-6)
- [ ] UX/UI 정교화 (모바일 최적화)
- [ ] 성능 최적화 (응답 속도, 배터리 소모 등)
- [ ] 베타 테스터 모집 및 피드백 반영
- [ ] 공식 출시 (Railway 배포)

---

## 7. 기대 효과 및 수익 모델

### 7.1. 사용자 편의성 증대
- 검색 시간 단축 (수십 분 → 수 초)
- 최적가 구매 보장 (공동구매 활용)
- 나만을 위한 맞춤 추천 경험

### 7.2. Mulberry Research Lab 수익 창출
- **제휴 마케팅:** 상품 구매 시 발생하는 리워드 수익
- **구독 모델:** 고급 기능 (무제한 공동구매 참여, 상세 분석 리포트) 유료화
- **데이터 인사이트:** 익명화된 트렌드 데이터를 기업에 판매 (윤리적 가이드라인 준수 하에)
- **공동구매 수수료:** 성공적인 거래 발생 시 소액의 플랫폼 수수료

---

## 8. 위험 요소 및 대응 방안

- **위험:** 외부 API 변경으로 인한 크롤링 오류
    - **대응:** 다중 소스 백업 시스템 및 정기적인 크롤러 업데이트
- **위험:** 라즈베리 파이 성능 한계 (발열, 지연)
    - **대응:** 경량화 모델 사용, 무거운 작업은 클라우드로 오프로딩
- **위험:** 개인정보 유출 우려
    - **대응:** 엣지 컴퓨팅을 통한 로컬 데이터 처리 최소화 원칙, 암호화 통신

---

**결론:**  
ShopMate 는 단순한 쇼핑 도우미를 넘어, **개인의 경제적 이익을 대변하는 AI 에이전트**이자 **Mulberry Lab 의 수익 창출 엔진**이 될 것입니다. 기존 공동구매 모듈과의 연동을 통해 빠른 시장 진입과 차별화된 서비스를 제공할 수 있을 것으로 기대됩니다.
