# 📋 Mulberry Agent Image Lab - Tasks

**작업 목록 및 진행 상황**

---

## 🎯 전체 진행률: 25% (12/48 완료)

---

## Phase 1: MVP (1주) - 75% 완료

### Task 1.1: 프로젝트 구조 설정 ✅
- [x] 디렉토리 구조 생성
- [x] README.md 작성
- [x] TASKS.md 작성
- [x] EVALUATION.md 작성
- [x] .gitignore 설정
- [x] requirements.txt 작성
- [x] package.json 작성

**예상 시간:** 2시간  
**실제 시간:** 1.5시간  
**담당:** CTO Koda

---

### Task 1.2: Model 1 - Steganography ⏳
- [x] 기본 인코더 구현
- [x] 기본 디코더 구현
- [ ] Agent 실행기 구현
- [ ] 압축 알고리즘 추가
- [ ] 에러 핸들링
- [ ] 단위 테스트

**파일:**
```
models/model-1-steganography/
├── encoder.py          # ✅ 완료
├── decoder.py          # ✅ 완료
├── executor.py         # 🔄 진행 중
├── compression.py      # ⏳ 대기
├── tests/              # ⏳ 대기
└── README.md           # ✅ 완료
```

**예상 시간:** 8시간  
**실제 시간:** 5시간 (진행 중)  
**담당:** CTO Koda

**주요 코드:**
```python
# LSB (Least Significant Bit) 방식
# 픽셀의 마지막 비트에 데이터 저장
# 육안으로 구별 불가능

def encode_agent_to_image(image_path, agent_config):
    # 이미지 로드
    img = Image.open(image_path)
    pixels = np.array(img)
    
    # Agent 설정을 Binary로 변환
    config_bytes = json.dumps(agent_config).encode('utf-8')
    config_bits = ''.join(format(byte, '08b') for byte in config_bytes)
    
    # 픽셀의 LSB에 저장
    flat_pixels = pixels.flatten()
    for i, bit in enumerate(config_bits):
        flat_pixels[i] = (flat_pixels[i] & 0xFE) | int(bit)
    
    # 이미지 저장
    encoded_pixels = flat_pixels.reshape(pixels.shape)
    encoded_img = Image.fromarray(encoded_pixels.astype('uint8'))
    encoded_img.save('agent.mba')
```

---

### Task 1.3: Model 2 - Metadata Encoding ⏳
- [x] EXIF 메타데이터 인코더
- [x] PNG 메타데이터 인코더
- [ ] 메타데이터 디코더
- [ ] Agent 실행기 (Node.js)
- [ ] 플랫폼별 테스트
- [ ] 단위 테스트

**파일:**
```
models/model-2-metadata/
├── encoder.py          # ✅ 완료
├── decoder.py          # 🔄 진행 중
├── executor.js         # ⏳ 대기
├── platform-tests/     # ⏳ 대기
└── README.md           # ✅ 완료
```

**예상 시간:** 6시간  
**실제 시간:** 3시간 (진행 중)  
**담당:** CTO Koda

**주요 코드:**
```python
from PIL import Image
from PIL.PngImagePlugin import PngInfo

def encode_agent_to_metadata(image_path, agent_config):
    img = Image.open(image_path)
    
    # PNG 메타데이터에 저장
    metadata = PngInfo()
    metadata.add_text("agent_type", agent_config['type'])
    metadata.add_text("agent_config", json.dumps(agent_config))
    metadata.add_text("version", "1.0")
    
    img.save('agent.mbimg', pnginfo=metadata)
```

---

### Task 1.4: Model 3 - Prompt Keywords ⏳
- [x] 프롬프트 빌더 구현
- [x] DALL-E 통합
- [ ] 키워드 파서 (JavaScript)
- [ ] Agent 실행기 (JavaScript)
- [ ] 함수 사전 정의
- [ ] 단위 테스트

**파일:**
```
models/model-3-prompt-keywords/
├── generator.py        # ✅ 완료
├── prompt-builder.py   # ✅ 완료
├── parser.js           # 🔄 진행 중
├── executor.js         # ⏳ 대기
├── function-dict.js    # ⏳ 대기
└── README.md           # ✅ 완료
```

**예상 시간:** 10시간  
**실제 시간:** 6시간 (진행 중)  
**담당:** CTO Koda

**주요 코드:**
```python
# 프롬프트에 Agent 키워드 삽입
def build_agent_prompt(visual_desc, agent_config):
    keywords = []
    
    if agent_config['type'] == 'CRAWLER':
        keywords.extend(['THINKEIN', 'ROUTIICG', 'PROZESSING'])
    elif agent_config['type'] == 'CONFIG':
        keywords.extend(['GITHUB_AUTOSETUP', 'RAILWAY_DEPLOY'])
    
    return f"{visual_desc} with {' and '.join(keywords)} elements"
```

---

### Task 1.5: Content Analyzer 🔄
- [x] GPT-4 통합
- [x] 블로그 글 파싱
- [ ] 키워드 추출
- [ ] Agent 타입 결정
- [ ] 설정 자동 생성
- [ ] 단위 테스트

**파일:**
```
analyzers/
├── content-analyzer.py     # 🔄 진행 중
├── keyword-extractor.py    # ⏳ 대기
├── agent-type-classifier.py # ⏳ 대기
└── config-generator.py     # ⏳ 대기
```

**예상 시간:** 8시간  
**실제 시간:** 4시간 (진행 중)  
**담당:** CTO Koda

---

### Task 1.6: Image Generators ⏳
- [x] DALL-E 3 통합
- [ ] Visual 프롬프트 빌더
- [ ] 스타일 템플릿
- [ ] 품질 검증
- [ ] 배치 생성

**파일:**
```
generators/
├── dalle-generator.py          # ✅ 완료
├── visual-prompt-builder.py    # 🔄 진행 중
├── style-templates.py          # ⏳ 대기
└── quality-validator.py        # ⏳ 대기
```

**예상 시간:** 6시간  
**실제 시간:** 2시간 (진행 중)  
**담당:** CTO Koda

---

### Task 1.7: Agent Executors ⏳
- [x] Config Executor 기본 구조
- [ ] Crawler Executor
- [ ] Analyzer Executor
- [ ] Monitor Executor
- [ ] 에러 핸들링
- [ ] 로깅 시스템

**파일:**
```
executors/
├── config-executor.js      # 🔄 진행 중
├── crawler-executor.js     # ⏳ 대기
├── analyzer-executor.js    # ⏳ 대기
├── monitor-executor.js     # ⏳ 대기
└── logger.js               # ⏳ 대기
```

**예상 시간:** 12시간  
**실제 시간:** 3시간 (진행 중)  
**담당:** CTO Koda

---

### Task 1.8: 파일 포맷 정의 ⏳
- [ ] .mba 포맷 사양
- [ ] .mbimg 포맷 사양
- [ ] .mbconfig 포맷 사양
- [ ] 검증 도구
- [ ] 변환 도구

**파일:**
```
utils/
├── file-formats.py         # ⏳ 대기
├── mba-validator.py        # ⏳ 대기
├── mbimg-validator.py      # ⏳ 대기
├── mbconfig-validator.py   # ⏳ 대기
└── converter.py            # ⏳ 대기
```

**예상 시간:** 8시간  
**실제 시간:** 0시간  
**담당:** CTO Koda, Research Director Malu

---

### Task 1.9: 기본 테스트 ⏳
- [ ] Steganography 테스트
- [ ] Metadata 테스트
- [ ] Prompt Keywords 테스트
- [ ] Integration 테스트
- [ ] 성능 테스트

**파일:**
```
tests/
├── test_steganography.py   # ⏳ 대기
├── test_metadata.py        # ⏳ 대기
├── test_prompt_keywords.py # ⏳ 대기
├── test_integration.py     # ⏳ 대기
└── test_performance.py     # ⏳ 대기
```

**예상 시간:** 6시간  
**실제 시간:** 0시간  
**담당:** CTO Koda

---

## Phase 2: 고도화 (2주) - 0% 완료

### Task 2.1: 암호화 ⏳
- [ ] AES-256 암호화
- [ ] RSA 키 교환
- [ ] 토큰 관리
- [ ] 서명 검증

**예상 시간:** 12시간  
**담당:** CTO Koda

---

### Task 2.2: 에러 핸들링 강화 ⏳
- [ ] 전역 에러 핸들러
- [ ] Retry 로직
- [ ] Fallback 메커니즘
- [ ] 에러 리포팅

**예상 시간:** 8시간  
**담당:** CTO Koda

---

### Task 2.3: 성능 최적화 ⏳
- [ ] 이미지 압축
- [ ] 캐싱 시스템
- [ ] 병렬 처리
- [ ] 메모리 최적화

**예상 시간:** 10시간  
**담당:** CTO Koda

---

### Task 2.4: UI/UX 개선 ⏳
- [ ] CLI 도구
- [ ] 웹 인터페이스
- [ ] 진행 표시
- [ ] 사용자 피드백

**예상 시간:** 16시간  
**담당:** CTO Koda

---

## Phase 3: 프로덕션 (3주) - 0% 완료

### Task 3.1: 대시보드 ⏳
- [ ] Agent 활동 모니터링
- [ ] 통계 시각화
- [ ] 실시간 업데이트

**예상 시간:** 20시간  
**담당:** CTO Koda

---

### Task 3.2: API 서버 ⏳
- [ ] RESTful API
- [ ] 인증/인가
- [ ] Rate Limiting

**예상 시간:** 16시간  
**담당:** CTO Koda

---

### Task 3.3: 모니터링 시스템 ⏳
- [ ] 로그 수집
- [ ] 메트릭 추적
- [ ] 알림 시스템

**예상 시간:** 12시간  
**담당:** CTO Koda

---

### Task 3.4: 배포 자동화 ⏳
- [ ] CI/CD 파이프라인
- [ ] Docker 컨테이너
- [ ] Railway 배포

**예상 시간:** 10시간  
**담당:** CTO Koda

---

## 📊 우선순위

### P0 (즉시)
1. ✅ Model 3 완성 (가장 자연스러움)
2. 🔄 Content Analyzer 완성
3. 🔄 기본 테스트

### P1 (이번 주)
4. ⏳ Model 2 완성 (가장 간단)
5. ⏳ Agent Executors
6. ⏳ 파일 포맷 정의

### P2 (다음 주)
7. ⏳ Model 1 완성 (가장 안전)
8. ⏳ 암호화 추가
9. ⏳ 성능 최적화

---

## 🎯 데일리 목표

### Day 1 (오늘)
- [x] 프로젝트 구조 설정
- [x] README 작성
- [x] Model 3 기본 구현 (70%)
- [ ] Content Analyzer 완성 (40% → 100%)

### Day 2
- [ ] Model 3 완성 (100%)
- [ ] Agent Executor 기본 구현
- [ ] 통합 테스트

### Day 3
- [ ] Model 2 완성
- [ ] 파일 포맷 정의
- [ ] 문서화

---

## 📝 메모

### 기술적 결정
1. **Model 3 우선**: 가장 자연스럽고 AI 생성 이미지와 완벽 통합
2. **Python + Node.js**: 이미지 처리(Python), Agent 실행(Node.js)
3. **OpenAI API**: DALL-E 3 + GPT-4 조합

### 고려사항
1. **비용**: DALL-E 3 생성 비용 ($0.04/image)
2. **속도**: 이미지 생성 5-10초
3. **품질**: 프롬프트 최적화 필요

### 다음 논의 주제
1. 파일 확장자 최종 결정 (.mba vs .mbimg vs .mbconfig)
2. 암호화 방식 선택
3. 배포 전략

---

**작성일:** 2026-04-19  
**최종 업데이트:** 2026-04-19 22:00  
**담당:** CTO Koda
