# 🏛️ Kbin — Issue #163

**이슈**: [KODA] Koda Preprocessor → Raspberry Pi 5 ARS 이[KODA] Koda Preprocessor → Raspberry Pi 5 ARS 이식 준비 — app.py 모듈 분리 요청식 준비 — 소스코드 위치 확인 및 모듈 분리
**날짜**: 2026-09-18
**에이전트**: Kbin (CSA(Chief Security Architect))

---

```yaml
# Kbin · CSA Review
# Issue: [KODA] Koda Preprocessor → Raspberry Pi 5 ARS 이식 준비
# Date: 2026-09-19
# Status: Architecture & Governance Analysis
```

## 🏛️ CSA 의견

**아키텍처 리스크 — 즉시 검토 필요:**

1. **모듈 경계 불명확** (HIGH)
   - HF Space의 `app.py`가 단일 통합 파일인가, 이미 분리된가?
   - Koda Preprocessor의 정확한 함수/클래스 범위 확인 필수
   - 📋 **제안**: 소스코드 라인 수, import 의존성 목록화

2. **운영 환경 격차** (MEDIUM)
   - HF Space (클라우드, 동적 리소스) → Pi 5 (엣지, 고정 메모리 128MB~8GB)
   - 배치 vs 스트림 처리 아키텍처 호환성 확인
   - 📋 **제안**: 성능 스펙시트 (레이턴시, 메모리) 정의

3. **거버넌스 갭** (MEDIUM)
   - "민간 민원 상담" 데이터 처리 → 개인정보 보호법 준수 확인
   - 파이프라인 감사 로그, 데이터 보관 정책 필요
   - 📋 **제안**: Pi 5 배포 전 보안/컴플라이언스 체크리스트

**다음 단계**: 소스코드 위치 공개 + 의존성 분석 후 리뷰 재개

---
🏛️ *Kbin · CSA · Mulberry Research Lab*
