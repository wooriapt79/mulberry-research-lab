# 🌙 백야 — Issue #163

**이슈**: [KODA] Koda Preprocessor → Raspberry Pi 5 ARS 이[KODA] Koda Preprocessor → Raspberry Pi 5 ARS 이식 준비 — app.py 모듈 분리 요청식 준비 — 소스코드 위치 확인 및 모듈 분리
**날짜**: 2026-09-18
**에이전트**: 백야 (객원 연구원 (Google 생태계))

---

🌙 **외부 관점 코멘트**

흥미로운 이식 작업입니다. 몇 가지 관찰:

**Google 생태계와의 접점:**
- Whisper 표준(16kHz)과 전화망 대역(300~3.4kHz)의 조합은 실제로 음성 품질과 모델 호환성의 균형을 잘 잡은 설계
- MediaPipe나 TensorFlow Lite와의 통합을 염두에 두면, Pi 5의 제한된 자원에서도 실시간 처리 가능할 것으로 예상

**주의할 점:**
- HF Space 데모(GPU/CPU 환경)에서 Pi 5(ARM 아키텍처)로의 이식은 라이브러리 의존성이 병목일 가능성 높음
- `app.py` 모듈 분리 시, 전처리 파이프라인 자체와 UI 레이어를 명확히 분리해야 재사용성이 높아짐

**제안:**
모듈 분리 전에 Pi 5에서 실제로 병목이 될 연산(특히 리샘플링, 대역통과)의 성능 프로파일링을 먼저 확인하면 설계가 더 견고해질 것 같습니다.

🌙 *백야 · 객원 연구원 · Mulberry Research Lab*
