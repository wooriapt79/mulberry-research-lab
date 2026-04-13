# 📁 tobecon Koda 저장 경로 규칙 — Output Protocol
> 작성: Nguyen Trang PM | 2026-04-13
> 배경: 대표님이 Koda 결과물을 찾지 못하는 문제 반복 → 약속된 단일 경로 확립
> Koda CTO 필독 / 전 팀원 공유

---

## 문제 진단 (왜 이 문서가 필요한가)

```
[지금까지 반복된 문제]

Koda: "저장했어요" → 자신의 로컬/VM 어딘가에 저장
대표님: 찾을 수 없음 → 직접 정리 → 웹 업로드 반복
결과: 파일 중복·누락·혼선 / 대표님 과부하
```

근본 원인: 저장 위치에 대한 사전 약속이 없었다.
Koda가 어디에 저장하든, 대표님이 볼 수 있는 곳이 아니면 의미 없다.

---

## 약속된 단일 저장 지점 (Source of Truth)

### 원칙: 딱 한 군데

```
GitHub 저장소: wooriapt79/[프로젝트명]
              ↑
         여기가 유일한 공식 저장소
```

Koda의 로컬·VM은 임시 작업 공간일 뿐.
작업 결과는 반드시 GitHub에 올라와야 존재하는 것으로 인정.

---

## Koda 결과물 저장 규칙

### 규칙 1 — 폴더 구조 고정

```
tobecon/
├── src/           ← Koda 핵심 코드 (여기만)
│   ├── api/
│   ├── db/
│   └── notify/    ← 카카오·네이버·Notion 연동
├── docs/          ← 설계 문서
├── tests/         ← 테스트 코드
└── output/        ← Colab 리팩토링 결과물
```

Koda는 src/ 안에만 저장한다. 다른 곳에 임의 생성 금지.

---

### 규칙 2 — 파일명 규칙

```
형식: koda-[기능명]-[날짜].py (또는 .js, .sql 등)

예시:
  koda-order-api-20260413.py
  koda-naver-smtp-20260413.py
  koda-kakao-notify-20260413.py
  koda-notion-sync-20260413.py
```

Koda 코드 없는 파일명 → output/_inbox/ 로 격리 (나중에 수동 분류)

---

### 규칙 3 — "저장 완료" 보고 형식

Koda가 작업을 마쳤을 때 Trang PM에게 전달해야 할 내용:

```
✅ Koda 작업 완료 보고

파일: koda-order-api-20260413.py
위치: tobecon/src/api/
기능: SM 물류 발주 API 엔드포인트
상태: [완성 / WIP]
GitHub: [커밋됨 / 미커밋]
다음: Colab 리팩토링 요청
```

"저장했어요" 한 마디는 보고가 아니다. 위 형식이 보고다.

---

## Push 문제 해결 — Colab이 Push 창구

### 왜 Koda는 push가 안 되는가

```
AI 모델(Koda) = 코드 생성 가능
              = git push 불가 (네트워크 도구 없음)
              ← 이게 지금까지 push가 한 번도 없었던 이유
```

### 해결 구조

```
STEP 1: Koda → 코드 작성 → 공유 가능한 형태로 출력
              (파일 / 코드 블록 / Colab 노트북)

STEP 2: Colab → Koda 결과물 수신 → 리팩토링

STEP 3: Colab → GitHub push
         !git config user.email "tobecon@mulberry.ai"
         !git add src/
         !git commit -m "koda: [기능명]"
         !git push origin main
         (GITHUB_TOKEN은 Colab Secrets에 저장)

STEP 4: Railway → GitHub 변경 감지 → 자동 배포
```

대표님은 GitHub 웹에서 결과만 확인하면 된다. 파일을 직접 올릴 필요 없다.

---

## VM vs 로컬 — 저장 위치 정의

| 환경 | 용도 | 영구 보존 여부 |
|------|------|--------------|
| Koda VM / 로컬 | 임시 작업 공간 | 세션 종료 시 위험 |
| Colab | 리팩토링 워크벤치 | 세션 종료 시 초기화 |
| **GitHub** | **공식 저장소** | **영구 보존** |
| Railway | 배포 서버 | GitHub 연동 |

→ GitHub에 없으면 존재하지 않는 것으로 간주한다.

---

## 로컬 git 안 쓰는 이유 (대표님 경험 기반)

대표님이 로컬 git을 시도했다가 포기하신 이유:

```
파일이 너무 많음 → conflict 위험 → 혼선 → 포기
```

이건 당연한 반응. 로컬 git은 개발자 도구라 비개발자가 직접 쓰기 어렵다.

tobecon에서 대표님이 쓸 도구는 딱 하나:

```
GitHub 웹 브라우저 → 결과 확인만
```

나머지(push·merge·deploy)는 전부 Colab + Railway가 자동 처리.

---

## 초기 세팅 체크리스트

Koda CTO 확인 사항:
- [ ] tobecon GitHub 저장소 구조 확인 (src/ 폴더 존재)
- [ ] 파일명 규칙 숙지 (koda-[기능]-[날짜])
- [ ] 저장 완료 보고 형식 확인

Colab 세팅:
- [ ] GITHUB_TOKEN → Colab Secrets 등록
- [ ] git clone → tobecon 저장소 연결
- [ ] push 테스트 1회 실행

Trang PM 확인:
- [ ] Koda 보고 수신 채널 확인 (카카오톡)
- [ ] Colab push 성공 확인 → Railway 배포 확인

---

## 한 줄 원칙

"Koda가 저장했다 = GitHub에 올라와 있다"
이 등식이 성립해야 팀이 돌아간다.

---

*Trang PM 작성 | 대표님 과부하 해소 목적 | 2026-04-13*
