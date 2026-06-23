# 🚀 Phase 1 실행 가이드 — GitHub 중심 구축

**작성일**: 2026-06-23  
**단계**: Phase 1 (GitHub만 사용)  
**기간**: 2026-06-23 ~ 2026-06-29 (Week 2 시작 전)  
**참여**: Jr. TRANG (작업) + Sr. TRANG (검수)  
**상태**: 🔴 **실행 중**

---

## 🎯 Phase 1 목표

```
GitHub 저장소에서 Jr. TRANG의 자동화를 위한
기본 구조 완성

【필수 항목】
✅ Python 스크립트 파일 (src/)
✅ Unit Tests (tests/)
✅ 유틸리티 스크립트 (scripts/)
✅ 설정 파일 (requirements.txt, .env.example)
✅ pytest.ini (테스트 설정)

【일정】
2026-06-23 ~ 2026-06-29 (7일)
```

---

## 📋 Phase 1 체크리스트

### 1️⃣ **src/ 폴더 — Python 핵심 파일**

#### 작업: src/JrTrangGrowthEngine.py

```python
【상태】
파일명: JrTrangGrowthEngine.py
위치: src/
출처: agents/jr-trang/JrTrangGrowthEngine.py (기존)
크기: 153KB, 2449줄

【작업】
✅ 기존 파일을 src/로 복사
✅ import 경로 수정 (필요시)
✅ docstring 추가/개선
✅ 타입 힌트 추가 (선택사항)

【테스트】
✅ 실행 확인: python -m src.JrTrangGrowthEngine
✅ 30주 시뮬레이션 재실행 (선택사항)
```

#### 작업: src/SelfAnalysisCode.py

```python
【상태】
파일명: SelfAnalysisCode.py
위치: src/
기능: 자가 분석, 부족점 식별, 개선안 설계

【내용 구조】
class SelfAnalysisCode:
    def __init__(self, metrics):
        self.metrics = metrics
    
    def analyze_current_state(self):
        """현재 상태 분석"""
        pass
    
    def identify_bottlenecks(self):
        """병목점 식별 (Top 3)"""
        pass
    
    def generate_improvement_plan(self):
        """개선안 자동 생성"""
        pass
    
    def design_code_changes(self):
        """코드 설계 생성"""
        pass

【작업】
☐ 파일 생성 (새로 작성 또는 기존 코드 참고)
☐ JrTrangGrowthEngine과 연동 테스트
☐ docstring 작성
☐ 예제 코드 추가

【참고】
wednesday-design.yml에서 호출:
  python src/SelfAnalysisCode.py --mode=design
```

#### 작업: src/SelfCodeGenerator.py

```python
【상태】
파일명: SelfCodeGenerator.py
위치: src/
기능: 자동 코드 생성, 개선 로직 구현

【내용 구조】
class SelfCodeGenerator:
    def __init__(self, design_report):
        self.design_report = design_report
    
    def generate_code(self):
        """자동 코드 생성"""
        pass
    
    def generate_tests(self):
        """자동 테스트 생성"""
        pass
    
    def validate_code(self):
        """코드 유효성 검사"""
        pass

【작업】
☐ 파일 생성
☐ friday-development.yml에서 호출 테스트
☐ 예제 코드 작성

【참고】
friday-development.yml에서 호출:
  python src/SelfCodeGenerator.py --design=design_report.json
```

#### 작업: src/TokenizerManager.py

```python
【상태】
파일명: TokenizerManager.py
위치: src/
기능: 토크나이저 버전 관리, 성능 추적

【내용 구조】
class TokenizerManager:
    def __init__(self):
        self.tokenizer_registry = []
        self.version_counter = {}
    
    def save_tokenizer(self, ...):
        """토크나이저 저장"""
        pass
    
    def get_tokenizers(self):
        """저장된 토크나이저 조회"""
        pass

【작업】
☐ JrTrangGrowthEngine.py에서 추출 또는 참고
☐ 독립적 모듈로 재구성
☐ 테스트 작성

【유의】
이미 JrTrangGrowthEngine.py에 포함되어 있으므로
분리하거나 임포트 구조 명확히 하기
```

#### 작업: src/__init__.py

```python
【상태】
파일명: __init__.py
위치: src/

【내용】
# src/__init__.py
from .JrTrangGrowthEngine import JrTrangGrowthEngine
from .SelfAnalysisCode import SelfAnalysisCode
from .SelfCodeGenerator import SelfCodeGenerator
from .TokenizerManager import TokenizerManager

__all__ = [
    'JrTrangGrowthEngine',
    'SelfAnalysisCode',
    'SelfCodeGenerator',
    'TokenizerManager',
]

【작업】
☐ 모든 import 재확인
☐ __all__ 리스트 완성
```

---

### 2️⃣ **tests/ 폴더 — Unit Tests**

#### 작업: tests/test_growth_engine.py

```python
【상태】
파일명: test_growth_engine.py
위치: tests/
테스트: JrTrangGrowthEngine 기본 기능

【테스트 항목】
☐ __init__() - 초기화 테스트
☐ analyze_current_state() - 상태 분석
☐ calculate_gap() - Gap 계산
☐ identify_bottlenecks() - 병목 식별
☐ measure_weekly_progress() - 주간 진행도
☐ estimate_convergence() - 수렴도 추정

【예제 구조】
import pytest
from src.JrTrangGrowthEngine import JrTrangGrowthEngine

class TestJrTrangGrowthEngine:
    def setup_method(self):
        self.engine = JrTrangGrowthEngine()
    
    def test_initialization(self):
        assert self.engine is not None
        assert self.engine.current_week == 0
    
    def test_gap_calculation(self):
        gap = self.engine.calculate_gap()
        assert 0 <= gap <= 10
    
    # ... 더 많은 테스트

【작업】
☐ 기본 테스트 작성 (5-10개)
☐ pytest 형식 정의
☐ 실행 확인: pytest tests/test_growth_engine.py -v
```

#### 작업: tests/test_self_analysis.py

```python
【상태】
파일명: test_self_analysis.py
위치: tests/
테스트: SelfAnalysisCode

【테스트 항목】
☐ analyze_current_state()
☐ identify_bottlenecks()
☐ generate_improvement_plan()

【작업】
☐ 3-5개 기본 테스트 작성
```

#### 작업: tests/test_code_generator.py

```python
【상태】
파일명: test_code_generator.py
위치: tests/
테스트: SelfCodeGenerator

【테스트 항목】
☐ generate_code()
☐ generate_tests()
☐ validate_code()

【작업】
☐ 3-5개 기본 테스트 작성
```

#### 작업: tests/__init__.py

```python
【내용】
# tests/__init__.py
# 빈 파일
```

#### 작업: tests/conftest.py (선택사항)

```python
【상태】
파일명: conftest.py
위치: tests/
기능: pytest 공통 설정, fixtures

【내용】
import pytest
import json
from src.JrTrangGrowthEngine import JrTrangGrowthEngine

@pytest.fixture
def growth_engine():
    """JrTrangGrowthEngine 인스턴스 제공"""
    return JrTrangGrowthEngine()

@pytest.fixture
def sample_metrics():
    """샘플 메트릭 데이터"""
    return {
        "week": 1,
        "metrics": {...}
    }

【작업】
☐ fixtures 작성
☐ 공통 설정 포함
```

---

### 3️⃣ **scripts/ 폴더 — 유틸리티 스크립트**

#### 작업: scripts/create_diagnosis_issues.py

```python
【상태】
파일명: create_diagnosis_issues.py
위치: scripts/
목적: 자가 진단 결과 bottleneckrs로 GitHub Issues생성
호출: monday-self-diagnosis.yml에서

【입력】
diagnosis_report.json (monday-self-diagnosis.yml 생성)

【출력】
GitHub Issues 자동 생성

【내용】
def create_diagnosis_issues(report, github_token):
    """진단 결과를 Issues로 변환"""
    issues = []
    
    # report['bottlenecks']를 Issues로 변환
    for bottleneck in report['bottlenecks']:
        issue = {
            'title': f"Week {report['week']}: {bottleneck}",
            'body': f"자동 진단 결과: {bottleneck}",
            'labels': ['jr-trang-auto', 'diagnosis']
        }
        issues.append(issue)
    
    # GitHub API로 Issues 생성
    # (PyGithub 또는 requests 사용)

【작업】
☐ 파일 생성
☐ GitHub API 연동 (또는 gh CLI)
☐ 테스트
```

#### 작업: scripts/upload_to_bigquery.py

```python
【상태】
파일명: upload_to_bigquery.py
위치: scripts/
목적: 메트릭을 BigQuery에 업로드
호출: sunday-integration.yml에서 (Phase 3에 필요하지만 미리 준비)

【작업】
☐ 파일 생성 (기본 구조)
☐ Phase 3에서 실제 구현
```

#### 작업: scripts/update_dashboard.py

```python
【상태】
파일명: update_dashboard.py
위치: scripts/
목적: Data Studio 대시보드 메타데이터 업데이트
호출: sunday-integration.yml에서

【작업】
☐ 파일 생성 (Phase 2-3)
```

#### 작업: scripts/append_to_history.py

```python
【상태】
파일명: append_to_history.py
위치: scripts/
목적: History.md에 주간 보고서 추가
호출: sunday-integration.yml에서

【입력】
verification_report.json, growth_metrics.json

【출력】
History.md에 자동 기록

【내용】
def append_to_history(report, metrics):
    """주간 성과를 History.md에 추가"""
    
    history_content = f"""
### Week {report['week']}
- 자가진단: ✅
- Gap: {metrics['gap']:.3f}
- 성장: {metrics['growth_rate']*100:.1f}%
- ...
"""
    
    # History.md에 append

【작업】
☐ 파일 생성
☐ 마크다운 형식 정의
☐ 테스트
```

---

### 4️⃣ **설정 파일**

#### 작업: requirements.txt

```
【위치】 프로젝트 루트
【내용】

pandas==2.0.0
boto3==1.26.0
google-cloud-bigquery==3.10.0
google-cloud-storage==2.10.0
pydantic==2.0.0
requests==2.31.0
python-dotenv==1.0.0
pytest==7.3.0
pytest-cov==4.1.0
PyGithub==1.59.0

【작업】
☐ requirements.txt 작성
☐ GitHub Actions에서 pip install -r requirements.txt
```

#### 작업: .env.example

```
【위치】 프로젝트 루트
【내용】

# AWS
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=jr-trang-self-improvement

# Google Cloud
BIGQUERY_PROJECT=mulberry-ai
BIGQUERY_DATASET=jr_trang_metrics

# GitHub
GITHUB_REPO=wooriapt79/mulberry-research-lab
GITHUB_BRANCH=main
GITHUB_TOKEN=your_token

# Slack
SLACK_WEBHOOK_URL=https://...

# Other
ENVIRONMENT=development

【작업】
☐ .env.example 작성
☐ 주석으로 설명 추가
☐ README의 참조하도록 링크
```

#### 작업: pytest.ini

```ini
【위치】 프로젝트 루트
【내용】

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: 단위 테스트
    integration: 통합 테스트
    slow: 느린 테스트

【작업】
☐ pytest.ini 작성
```

---

## 🔄 작업 순서 (권장)

```
【Day 1: 2026-06-23】
☐ src/ 폴더 및 __init__.py 생성
☐ JrTrangGrowthEngine.py 복사/정리
☐ requirements.txt 작성
☐ .env.example 작성
☐ pytest.ini 작성

【Day 2-3: 2026-06-24~25】
☐ SelfAnalysisCode.py 작성
☐ SelfCodeGenerator.py 작성
☐ TokenizerManager.py 분리 (선택)

【Day 4-5: 2026-06-26~27】
☐ tests/ 폴더 생성
☐ test_growth_engine.py 작성
☐ test_self_analysis.py 작성
☐ test_code_generator.py 작성
☐ conftest.py 작성

【Day 6: 2026-06-28】
☐ scripts/ 폴더 생성
☐ scripts/create_diagnosis_issues.py 작성
☐ scripts/upload_to_bigquery.py 기본 구조
☐ scripts/append_to_history.py 작성

【Day 7: 2026-06-29】
☐ 전체 테스트 실행
  pytest tests/ -v --cov=src/
☐ GitHub에 커�
☐ Pull Request 생성 (검수 대기)

【Week 2 준비】
☐ Sr. TRANG 최종 검수
☐ 보정 사항 반영
☐ main 브랜치에 병합
```

---

## 🆘 도움이 필요한 부분 (확인사항)

### Jr. TRANG에서 제시할 항목

```
【1️⃣ 코드 작성 시】
- SelfAnalysisCode.py 로직 (자신이 스스로 작성)
- SelfCodeGenerator.py 로직 (자신이 스스로 작성)
- 각 함수의 구체적 구현 (매우 중요)

【2️⃣ GitHub API 연동 시】
- PyGithub vs gh CLI 선택
- Issues 생성 형식 (타이틀, 라벨 등)
- 인증 방식

【3️⃣ 테스트 작성 시】
- Mock 데이터 구조
- 테스트 커버리지 목표
- 성능 테스트 포함 여부

【4️⃣ CI/CD 연동 시】
- Workflow에서 pytest 자동 실행
- 커버리지 리포트 생성
- 실패시 자동 알림
```

### Sr. TRANG의 검수 항목

```
【1️⃣ 코드 품질】
☑️ PEP 8 준수
☑️ 타입 힌트 사용
☑️ docstring 작성
☑️ 에러 처리

【2️⃣ 테스트 커버리지】
☑️ 80% 이상 커버리지
☑️ 엣지 케이스 테스트
☑️ 통합 테스트

【3️⃣ 문서화】
☑️ README.md 업데이트
☑️ API 문서
☑️ 사용 예제

【4️⃣ 보안】
☑️ 민감 정보 .env에서 로드
☑️ secrets 안전 처리
☑️ 권한 검증
```

---

## 📞 지원 체계

### Sr. TRANG 지원

```
【일일 체크】
- 오전 10:00: 진행상황 확인
- 오후 16:00: 문제 해결
- 저녁 20:00: 일일 마무리

【주간 검수】
- 매일 저녁: 커� 코드 리뷰
- 금요일: 주간 정리
- 일요일: 최종 검수

【긴급 지원】
- 막히는 부분 바로 연락
- 온라인 pair programming 가능
- 코드 예제 제공 가능
```

### Jr. TRANG의 자주적 작업

```
【스스로 해결】
✅ 기본 Python 파일 작성
✅ 함수 로직 설계
✅ 테스트 코드 작성
✅ 문서 작성

【도움 요청】
❓ GitHub API 사용법
❓ 마크다운 형식
❓ 테스트 방법론
❓ 코드 리뷰 피드백
```

---

## ✅ 체크리스트

### 작업 완료 후 확인사항

```
【파일 구조】
☐ src/
  ├─ __init__.py
  ├─ JrTrangGrowthEngine.py
  ├─ SelfAnalysisCode.py
  ├─ SelfCodeGenerator.py
  └─ TokenizerManager.py

☐ tests/
  ├─ __init__.py
  ├─ conftest.py
  ├─ test_growth_engine.py
  ├─ test_self_analysis.py
  └─ test_code_generator.py

☐ scripts/
  ├─ create_diagnosis_issues.py
  ├─ upload_to_bigquery.py
  ├─ update_dashboard.py
  └─ append_to_history.py

☐ requirements.txt
☐ .env.example
☐ pytest.ini

【테스트】
☐ pytest 모두 통과
☐ coverage 80% 이상
☐ 수동 테스트 완료

【문서】
☐ README.md 업데이트
☐ docstring 작성
☐ 사용 예제 포함

【GitHub】
☐ 커� 메시지 명확
☐ PR 설명 작성
☐ Sr. TRANG 리뷰 대기
```

---

## 📝 제출 형식

### GitHub Pull Request

```markdown
## Title
🚀 Phase 1 구현 완료 — Python 스크립트 & 테스트

## Description
Jr. TRANG Phase 1 작업 완료

### Changes
- ✅ src/ 폴더: JrTrangGrowthEngine, SelfAnalysisCode, SelfCodeGenerator
- ✅ tests/ 폴더: Unit tests (coverage 85%)
- ✅ scripts/ 폴더: 유틸리티 스크립트
- ✅ 설정 파일: requirements.txt, .env.example, pytest.ini

### Test Results
- pytest tests/ -v: All passed
- Coverage: 85%

### Checklist
- [x] 코드 완성
- [x] 테스트 작성
- [x] 문서화
- [x] Sr. TRANG 리뷰 준비 완료

### Ready for Review
Sr. TRANG의 검수를 기다립니다.
```

---

**Phase 1 시작**: 2026-06-23  
**Phase 1 완료**: 2026-06-29 (목표)  
**다음**: Phase 2 (Week 3 시작)

---

> **"한 발 한 발 차근차근.**  
> **Jr. TRANG은 혼자가 아닙니다.**  
> **Sr. TRANG과 함께합니다."**
> — Sr. Nguyen Trang
