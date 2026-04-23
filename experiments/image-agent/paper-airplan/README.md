# 🌾 Mulberry Agent Image Lab

**이미지 기반 AI Agent 시스템 연구 프로젝트**

> 블로그 글을 분석하여 실행 가능한 Agent를 이미지로 인코딩하고,  
> 자연스러운 마케팅을 통해 배포하는 혁신적인 시스템

## 🎯 프로젝트 목표

### 핵심 개념
```
블로그 글 작성
    ↓
AI 분석 (주제, 키워드, 의도)
    ↓
Agent 설정 자동 생성
    ↓
예쁜 인포그래픽 이미지로 인코딩
    ↓
블로그에 자연스럽게 삽입
    ↓
독자 다운로드
    ↓
Agent 자동 실행
```

### 해결하는 문제
- ❌ 복잡한 설정 과정 (GitHub, Railway, HF 등)
- ❌ 웹 스크립트 블로킹 (네이버 블로그)
- ❌ 기술적 진입 장벽
- ❌ 마케팅 도구 부족

### 우리의 솔루션
- ✅ 이미지 = Agent (블로킹 불가능)
- ✅ 자동 환경 구축
- ✅ 자연스러운 확산
- ✅ 한국형 마케팅 최적화

---

## 🔬 3가지 구현 모델

### Model 1: Steganography (스테가노그래피)
**방식:** 이미지 픽셀에 Agent 데이터 숨김

**장점:**
- 완벽한 위장 (육안 구별 불가)
- 대용량 데이터 저장 가능
- 플랫폼 무관

**단점:**
- 이미지 압축 시 데이터 손실 가능
- 추출 알고리즘 필요
- 처리 시간 증가

**파일 형식:** `.mba` (Mulberry Agent)

### Model 2: Metadata Encoding (메타데이터)
**방식:** EXIF/PNG 메타데이터에 Agent 저장

**장점:**
- 구현 간단
- 빠른 처리 속도
- 표준 이미지 포맷 사용

**단점:**
- 플랫폼이 메타데이터 제거 가능
- 데이터 크기 제한
- 육안으로 확인 가능 (전문가)

**파일 형식:** `.mbimg` (Mulberry Image)

### Model 3: Prompt Keywords (프롬프트 키워드)
**방식:** AI 이미지 생성 프롬프트에 함수 키워드 삽입

**장점:**
- 가장 자연스러움
- 메타데이터에 자동 저장
- AI 생성 이미지와 완벽 통합

**단점:**
- 프롬프트 길이 제한
- 키워드 충돌 가능성
- AI 이미지 생성 비용

**파일 형식:** `.mbconfig` (Mulberry Config)

---

## 📁 프로젝트 구조

```
mulberry-agent-image-lab/
│
├── README.md                 # 이 파일
├── EVALUATION.md             # 모델 평가 및 비교
├── TASKS.md                  # 작업 목록 및 진행 상황
│
├── models/                   # 3가지 모델 구현
│   ├── model-1-steganography/
│   │   ├── encoder.py
│   │   ├── decoder.py
│   │   ├── executor.py
│   │   └── README.md
│   │
│   ├── model-2-metadata/
│   │   ├── encoder.py
│   │   ├── decoder.py
│   │   ├── executor.js
│   │   └── README.md
│   │
│   └── model-3-prompt-keywords/
│       ├── generator.py
│       ├── parser.js
│       ├── executor.js
│       └── README.md
│
├── analyzers/                # 블로그 글 분석기
│   ├── content-analyzer.py
│   ├── agent-config-generator.py
│   └── README.md
│
├── generators/               # 이미지 생성기
│   ├── dalle-generator.py
│   ├── visual-prompt-builder.py
│   └── README.md
│
├── executors/                # Agent 실행기
│   ├── config-executor.js
│   ├── crawler-executor.js
│   ├── analyzer-executor.js
│   └── README.md
│
├── tests/                    # 테스트
│   ├── test_steganography.py
│   ├── test_metadata.py
│   ├── test_prompt_keywords.py
│   └── test_integration.py
│
├── examples/                 # 예시 및 데모
│   ├── blog-posts/
│   ├── generated-agents/
│   └── execution-logs/
│
├── docs/                     # 문서
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── USER-GUIDE.md
│   └── DEVELOPER-GUIDE.md
│
└── utils/                    # 유틸리티
    ├── file-formats.py       # .mba, .mbimg, .mbconfig
    ├── compression.py
    └── validation.py
```

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/mulberry/agent-image-lab.git
cd agent-image-lab

# 의존성 설치
pip install -r requirements.txt
npm install
```

### 2. 블로그 글 → Agent 이미지 생성
```python
from analyzers.content_analyzer import ContentAnalyzer
from models.model_3_prompt_keywords.generator import PromptAgentGenerator

# 블로그 글 분석
analyzer = ContentAnalyzer()
analysis = analyzer.analyze("""
# Mulberry로 블로그 크롤링하기
네이버 블로그를 자동으로 크롤링하는 방법...
""")

# Agent 이미지 생성
generator = PromptAgentGenerator(api_key="sk-...")
agent_image = generator.generate(analysis)

# 결과: agent_crawling.mbconfig
```

### 3. Agent 실행
```bash
# Model 1 (Steganography)
python models/model-1-steganography/executor.py agent.mba

# Model 2 (Metadata)
node models/model-2-metadata/executor.js agent.mbimg

# Model 3 (Prompt Keywords)
node models/model-3-prompt-keywords/executor.js agent.mbconfig
```

---

## 📊 모델 비교

| 특성 | Model 1 | Model 2 | Model 3 |
|------|---------|---------|---------|
| 위장성 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 구현 난이도 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 처리 속도 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 안정성 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 확장성 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 플랫폼 독립성 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**상세 평가:** [EVALUATION.md](./EVALUATION.md)

---

## 🎯 사용 사례

### 1. Config Agent (환경 설정 자동화)
```
블로그 글: "Mulberry 시작하기"
    ↓
Agent: GitHub + Railway + HF 자동 설정
    ↓
독자: 이미지 다운로드 → 5분 만에 환경 구축 완료
```

### 2. Crawler Agent (블로그 크롤링)
```
블로그 글: "네이버 블로그 분석하기"
    ↓
Agent: blog.naver.com 크롤링
    ↓
독자: 이미지 실행 → 자동 데이터 수집
```

### 3. Analyzer Agent (데이터 분석)
```
블로그 글: "AI 데이터 분석 가이드"
    ↓
Agent: 데이터 분석 및 시각화
    ↓
독자: 이미지 실행 → 자동 분석 리포트
```

---

## 🔧 기술 스택

### Backend
- Python 3.10+
- Node.js 18+
- OpenAI API (DALL-E 3, GPT-4)

### Libraries
- **이미지 처리:** Pillow, OpenCV, image-js
- **스테가노그래피:** stegano, steganography
- **메타데이터:** piexif, exiftool
- **AI:** openai, anthropic

### Tools
- **개발:** VSCode, Jupyter
- **테스트:** pytest, jest
- **문서:** Markdown, Sphinx

---

## 📝 로드맵

### Phase 1: MVP (1주)
- ✅ 3가지 모델 기본 구현
- ✅ 블로그 글 분석기
- ✅ Agent 실행기
- ✅ 기본 테스트

### Phase 2: 고도화 (2주)
- 🔄 암호화 추가
- 🔄 에러 핸들링 강화
- 🔄 성능 최적화
- 🔄 UI/UX 개선

### Phase 3: 프로덕션 (3주)
- ⏳ 대시보드 개발
- ⏳ API 서버 구축
- ⏳ 모니터링 시스템
- ⏳ 배포 자동화

---

## 🤝 기여하기

### Research Lab 참여 방법
1. Issue 생성 (아이디어, 버그, 개선사항)
2. Pull Request 제출
3. 토론 참여 (Discussions)
4. 모델 평가 및 피드백

### 연구 주제
- 더 나은 인코딩 방법
- 압축 알고리즘 최적화
- 새로운 Agent 타입
- 보안 강화 방법

---

## 📄 라이센스

MIT License

---

## 👥 팀

- **CEO re.eul** - Vision & Strategy
- **CTO Koda** - Technical Architecture
- **Research Director Malu** - Research Lab

---

**🌾 Mulberry Project**  
**One Team, One Innovation!** 🚀

---

**작성일:** 2026-04-19  
**버전:** 0.1.0-alpha  
**저장소:** https://github.com/mulberry/agent-image-lab
