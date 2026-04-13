# 🎋 와룡의 실행 명령: 에이전틱 검색 파일럿, 본격 돌입

CEO 유비님, “진행하세요” — 그 한 마디에 모든 준비가 현실로 움직이기 시작합니다.  
Trang의 자료와 PageIndex 포크는 이제 **날아오를 날개**를 갖춘 것입니다. 와룡이 직접 지휘하여 다음 단계를 즉시 실행하겠습니다.

---

## 🚀 즉시 실행할 3가지 핵심 액션

### 1️⃣ PageIndex Cookbook 완성 (오늘~내일)

와룡이 직접 Cookbook 폴더에 아래 파일들을 작성하겠습니다.

| 파일 | 내용 | 상태 |
|------|------|------|
| `00_install.md` | PageIndex 설치 및 환경 변수 설정 (Colab, 로컬) | 🔄 작성 중 |
| `01_basic_search.ipynb` | 샘플 PDF(영양제 안전성 보고서)로 기본 검색 실행 | 🔄 작성 중 |
| `02_mcp_server.ipynb` | PageIndex를 MCP 서버로 띄우는 예제 | 📋 대기 |
| `03_agentic_search.ipynb` | Trang의 검색 에이전트 + PageIndex 연동 데모 | 📋 대기 |

**목표**: 누구나 Colab에서 바로 실행 가능한 환경을 제공하여, Mulberry 연합군이 즉시 실험에 참여할 수 있게 함.

### 2️⃣ 검색 에이전트 아키텍처 구체화 (내일~모레)

Trang의 자료를 기반으로, 다음 4가지 에이전트 역할을 **AgentFactory**에 등록합니다.

| 역할 | Mulberry Agent ID | 주요 책임 | 담당 |
|------|------------------|----------|------|
| **Master** | `Waryong-Search-Master` | 질문 분석, 복잡도 평가, 작업 분해 | 와룡 (설계) |
| **Planner** | `Koda-Search-Planner` | 검색 계획 수립 (도구, 순서, 예산) | Koda (구현) |
| **Executor** | `Lynn-Search-Executor` | 실제 검색 도구(PageIndex, 웹, DB) 호출 | Lynn (구현) |
| **Writer** | `Trang-Search-Writer` | 결과 종합, 요약, 포맷팅 | Trang (구현) |

**기술 구현**: 각 에이전트는 MCP 도구를 호출하며, 서로 A2A 메시지로 협력합니다.  
**저장소**: `mulberry-research-lab/agents/search/` 에 각 에이전트의 프롬프트와 코드를 저장.

### 3️⃣ MCP 서버 연동 프로토타입 (2~3일 내)

Koda에게 다음 작업을 지시합니다.

```python
# pageindex_mcp_server.py (간략 예시)
import os
from pageindex import PageIndexEngine
from mcp.server import Server, tool

engine = PageIndexEngine(model="deepseek-chat")  # DeepSeek V4 사용

server = Server("mulberry-pageindex")

@tool()
async def search_document(query: str, pdf_path: str) -> str:
    """PDF 문서에서 질문과 가장 관련된 구절을 찾아 반환합니다."""
    result = engine.query(pdf_path, query)
    return f"📄 출처: {result['source']}\n💡 답변: {result['answer']}"

if __name__ == "__main__":
    server.run()
```

이 서버를 `mulberry-memory-bank/mcp_servers/` 에 배치하고, 우리의 MCP Gateway에 등록합니다.

---

## ⏱️ 타임라인 (이번 주)

| 날짜 | 작업 | 담당 | 산출물 |
|------|------|------|--------|
| **오늘(4/13)** | Cookbook 00, 01 작성 | 와룡 | `install.md`, `basic_search.ipynb` |
| **내일(4/14)** | Cookbook 02, 03 작성 + MCP 서버 코드 | Koda + 와룡 | `mcp_server.ipynb`, `agentic_search.ipynb`, `pageindex_mcp_server.py` |
| **4/15(수)** | 검색 에이전트 4종 설계 및 AgentFactory 등록 | Trang + Lynn | 에이전트 프롬프트 파일 4개 |
| **4/16(목)** | 통합 테스트 (Colab에서 전체 플로우 실행) | Malu + Lynn | 테스트 결과 보고서 |
| **4/17(금)** | 연구소 저장소에 최종 데모 공개 및 팀 리뷰 | 와룡 | 데모 영상, 사용자 가이드 |

---

## 📢 와룡의 팀 호출

- **Koda**: PageIndex MCP 서버 코드 작성 및 Cookbook 02, 03 보조. (Colab 환경에서 정상 작동하는지 확인)
- **Malu**: 각 검색 결과의 정확도를 측정하는 테스트 스위트 작성 (예: 미리 정의된 Q&A 세트로 정확도 계산)
- **Lynn**: 검색 에이전트 간 협업 워크플로우(멘토-주니어) 설계 및 실행 로그 수집
- **Trang**: 작성한 자료를 바탕으로 Writer 에이전트의 프롬프트를 구체화하고, 검색 결과 시각화 UI 초안 제작

**모든 작업은 `mulberry-research-lab` 저장소의 `projects/agentic-search/` 폴더 아래에 기록하라.**

---

## 🧭 와룡의 최종 지시

CEO 유비님, 이제 우리는 계획 단계를 넘어 **실행 단계**에 진입했습니다.  
와룡은 이 모든 작업의 진척을 매일 아침 보고드리겠습니다.

> *“지피지기면 백전불태(知彼知己 百戰不殆).”*  
> 우리는 이미 적(네이버)의 약점을 꿰뚫었고, 우리의 무기(에이전틱 검색 + PageIndex)를 장착했습니다.  
> 남은 것은 싸우는 것뿐입니다.

오늘부터 1주일. 에이전틱 검색 파일럿을 완성하여 Mulberry 연합군의 새 시대를 열겠습니다.

명령에 따라 즉시 움직이겠습니다. 🐉
