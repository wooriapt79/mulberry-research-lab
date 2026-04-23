# 📄 Mulberry Agent File Format Specifications

**우리만의 파일 확장자 정의서**

---

## 🎯 개요

Mulberry Agent 시스템은 3가지 파일 포맷을 정의합니다.

| 확장자 | 모델 | 방식 | 용도 |
|--------|------|------|------|
| `.mba` | Model 1 | Steganography | 대용량, 최고 보안 |
| `.mbimg` | Model 2 | Metadata | 빠른 프로토타입 |
| `.mbconfig` | Model 3 | Prompt Keywords | 블로그 마케팅 |

---

## 📦 .mba (Mulberry Agent)

**Model 1: Steganography**

### 파일 구조

```
PNG Image File
├── Image Data (RGB pixels)
│   └── LSB bits = Agent Data
│       ├── Header (9 bytes)
│       │   ├── Signature (4 bytes): "MLBY"
│       │   ├── Version (1 byte): 0x01
│       │   └── Data Length (4 bytes): uint32
│       │
│       └── Payload (variable)
│           └── Compressed Agent Config (zlib)
```

### Header 상세

```python
# Byte 0-3: Signature
SIGNATURE = b'MLBY'  # Mulberry 식별자

# Byte 4: Version
VERSION = 0x01

# Byte 5-8: Payload Length (Little Endian)
# 예: 1024 bytes = 0x00 0x04 0x00 0x00
```

### Payload 구조

```json
{
  "type": "CRAWLER | ANALYZER | CONFIG | MONITOR",
  "action": "crawl | analyze | setup | monitor",
  "target": "URL or service",
  "endpoint": "API endpoint",
  "settings": { /* 추가 설정 */ }
}
```

### 인코딩 알고리즘

1. Agent Config → JSON
2. JSON → UTF-8 bytes
3. zlib 압축 (level 9)
4. Header 생성
5. Header + Compressed Data
6. Binary → Bit stream
7. Bit stream → Image LSB

### 디코딩 알고리즘

1. Image LSB → Bit stream
2. Bit stream → Binary
3. Header 파싱 (signature 확인)
4. Compressed Data 추출
5. zlib 압축 해제
6. UTF-8 bytes → JSON
7. JSON → Agent Config

### 용량 계산

```
최대 용량 = (width × height × 3) / 8 bytes

예시:
1024 × 1024 × 3 / 8 = 393,216 bytes (~384 KB)
```

### 보안 고려사항

- 육안 구별 불가능
- 압축 시 데이터 손실 주의 (PNG 권장)
- JPEG 사용 금지 (손실 압축)

---

## 📦 .mbimg (Mulberry Image)

**Model 2: Metadata Encoding**

### 파일 구조

```
PNG Image File
├── Image Data (standard PNG)
└── PNG Text Chunks (metadata)
    ├── mulberry_agent: "true"
    ├── mulberry_version: "1.0"
    ├── agent_type: "CRAWLER | ..."
    ├── agent_config: "{...JSON...}"
    ├── generated_at: "ISO 8601"
    └── model: "metadata-encoding"
```

### Metadata Fields

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `mulberry_agent` | string | ✅ | "true" (Agent 식별자) |
| `mulberry_version` | string | ✅ | 포맷 버전 (예: "1.0") |
| `agent_type` | string | ✅ | Agent 타입 |
| `agent_config` | string | ✅ | JSON 문자열 |
| `generated_at` | string | ✅ | ISO 8601 timestamp |
| `model` | string | ✅ | "metadata-encoding" |
| `topic` | string | ❌ | 주제 (선택) |
| `target` | string | ❌ | 타겟 (선택) |

### Agent Config 예시

```json
{
  "type": "CONFIG",
  "action": "setup",
  "services": ["github", "railway"],
  "auto_deploy": true,
  "settings": {
    "github": {
      "repo_name": "my-project",
      "private": false
    }
  }
}
```

### 플랫폼 호환성

| 플랫폼 | 메타데이터 보존 | 상태 |
|--------|----------------|------|
| PNG 파일 | ✅ 보존됨 | 안전 |
| 네이버 블로그 | ⚠️ 가능성 있음 | 테스트 필요 |
| 티스토리 | ✅ 보존됨 | 안전 |
| 인스타그램 | ❌ 제거됨 | 비추천 |

### 용량 제한

```
PNG 메타데이터: ~10 KB (권장)
EXIF: ~64 KB (최대)
```

---

## 📦 .mbconfig (Mulberry Config)

**Model 3: Prompt Keywords**

### 파일 구조

```
PNG Image File
├── Image Data (DALL-E generated)
└── PNG Text Chunks (metadata)
    ├── prompt: "A landscape with THINKEIN..."
    ├── agent_type: "CRAWLER | ..."
    ├── agent_config: "{...JSON...}"
    ├── mulberry_version: "1.0"
    └── model: "prompt-keywords"
```

### Prompt 구조

```
Visual Description + Agent Keywords

예시:
"A beautiful Korean landscape,
 featuring THINKEIN meditation elements,
 and ROUTIICG pathways,
 connected to ASTROFEN network,
 ready for PROZESSING DATA flow"
```

### Function Keywords Dictionary

| Keyword | Function | Category | Description |
|---------|----------|----------|-------------|
| `THINKEIN` | AI Engine | Core | AI 엔진 활성화 |
| `PROZESSING` | Data Process | Core | 데이터 처리 |
| `ROUTIICG` | Routing | Network | 라우팅 설정 |
| `ASTROFEN` | Server Connect | Network | 서버 연결 |
| `GITHUB_AUTOSETUP` | GitHub Setup | Config | GitHub 자동 설정 |
| `RAILWAY_DEPLOY` | Railway Deploy | Config | Railway 배포 |
| `WORKBENCH_SETUP` | IDE Setup | Config | 워크벤치 설정 |
| `SERVELL` | Endpoint | Network | 서버 엔드포인트 |
| `POE` | Point of Entry | Core | 진입점 |
| `MAIHESSHONE` | Maintenance | System | 유지보수 모드 |
| `PROCEGANG` | Parallel Process | System | 병렬 처리 |

### Agent Type별 Keyword 조합

```
CRAWLER:
  THINKEIN + ROUTIICG + PROZESSING

CONFIG:
  GITHUB_AUTOSETUP + RAILWAY_DEPLOY + WORKBENCH_SETUP

ANALYZER:
  THINKEIN + PROZESSING + ASTROFEN

MONITOR:
  ASTROFEN + PROCEGANG + MAIHESSHONE
```

### 생성 프로세스

1. 블로그 글 분석 (GPT-4)
2. Agent 타입 결정
3. 시각적 프롬프트 생성
4. 키워드 삽입
5. DALL-E 3 이미지 생성
6. 메타데이터 저장

### 실행 프로세스

1. 이미지 로드
2. 메타데이터에서 프롬프트 추출
3. 키워드 파싱
4. 함수 매핑
5. 순차 실행

---

## 🔐 확장자별 보안 수준

### .mba (최고)
```
✅ 육안 구별 불가
✅ 기술적 탐지 어려움
✅ 플랫폼 독립적
⚠️ 압축 시 주의
```

### .mbimg (중간)
```
⚠️ 전문 도구로 확인 가능
⚠️ 플랫폼이 제거 가능
✅ 구현 간단
✅ 속도 빠름
```

### .mbconfig (최고)
```
✅ 자연스러운 프롬프트
✅ AI 생성 이미지
✅ 메타데이터 안정적
⚠️ 키워드 충돌 주의
```

---

## 📊 확장자 선택 가이드

### 용도별 추천

**블로그 마케팅:**
→ `.mbconfig` (가장 자연스러움)

**대용량 Agent:**
→ `.mba` (용량 제한 없음)

**빠른 프로토타입:**
→ `.mbimg` (구현 간단)

**최고 보안:**
→ `.mba` 또는 `.mbconfig`

---

## 🔄 포맷 변환

### .mbconfig → .mba
```python
# 1. .mbconfig에서 agent_config 추출
# 2. .mba로 인코딩
```

### .mbimg → .mbconfig
```python
# 1. .mbimg에서 agent_config 추출
# 2. 시각적 프롬프트 생성
# 3. DALL-E로 .mbconfig 생성
```

---

## 🎨 MIME Type

```
.mba      →  image/x-mulberry-agent
.mbimg    →  image/x-mulberry-image
.mbconfig →  image/x-mulberry-config

(모두 PNG 기반이므로 image/png도 호환)
```

---

## 📝 JSON Schema

### Agent Config (공통)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "version"],
  "properties": {
    "type": {
      "type": "string",
      "enum": ["CRAWLER", "ANALYZER", "CONFIG", "MONITOR"]
    },
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+$"
    },
    "action": {
      "type": "string"
    },
    "target": {
      "type": "string"
    },
    "endpoint": {
      "type": "string",
      "format": "uri"
    },
    "settings": {
      "type": "object"
    }
  }
}
```

---

## 🚀 버전 관리

### 현재 버전: 1.0

**포맷 변경 시:**
- Minor 업데이트 (1.0 → 1.1): 하위 호환
- Major 업데이트 (1.0 → 2.0): 비호환

**버전 확인:**
```python
# .mba: Header byte 4
# .mbimg, .mbconfig: metadata['mulberry_version']
```

---

**작성일:** 2026-04-19  
**버전:** 1.0  
**상태:** 초안 (Lab 토론 필요)

**🌾 Mulberry Project - 우리만의 표준!** ✨
