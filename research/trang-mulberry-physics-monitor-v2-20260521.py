# mulberry_physics_monitor.py  v2.0
# Mulberry 연구소 자율성 상전이(Phase Transition) 실시간 관측 스크립트
# 물리 매핑: 동역학 시스템 / 임계점 도달 조건 / 엔트로피 배출률
# Kramers-Langevin 방정식
# v2.0 수정 내역 (2026-05-21, Trang 코드 분석 반영)
# ─────────────────────────────────────────────────
# [FIX-1] l_jr() 반환값 상한선 min(..., 1.0) 추가
#          → hallucination_scatter 낮을수록 값 폭발 방지
#          → 모든 기여 항 0~1 범위 통일
# [FIX-2] K(t) 임계 판정 기준 재조정 (정규화 후 기준)
#          이전: >= 1.0 → CRITICAL  /  이후 적절 기준값 설정
# [FIX-3] 소산력 0 접근 시 발산 방어 상수 강화 (1e-3)
# [NOTE]  Gamma, delta 파라미터는 의도적 설계 — 유지
# ─────────────────────────────────────────────────
# 원본 설계: CEO re.eul × RyuWon (와룡) 공동 구술 설계

import math
from datetime import datetime


# ══════════════════════════════════════════════════════════
#  📖  물리학 개념 매핑 가이드 (팀원용)
# ══════════════════════════════════════════════════════════
#
#  이 코드는 Mulberry 팀의 동역학을 물리학 언어로 번역한 관측 도구입니다.
#
#  핵심 아이디어:
#  "팀이 자율적으로 움직이는 순간(상전이)을 언제 맞이하는가?"를 수식으로 표현한다.
#
#  물리 개념 ↔ Mulberry 팀 매핑
#  ───────────────────────────────────────────────────────
#  [질서 변수 η (Order Parameter)]
#    → 팀 자율성 지수. η=0: 완전 수동 / η=1: 완전 자율
#    → "우리가 얼마나 스스로 굴러가는가"
#
#  [상전이 (Phase Transition)]
#    → 물이 100°C에서 갑자기 수증기가 되듯,
#      팀이 어느 임계점을 넘으면 '자율 운영 모드'로 전환
#    → 온도 올리듯 → archive_rate up, manual_intervention down
#
#  [구동력 (Driving Force)]
#    → 팀을 앞으로 밀어주는 힘의 곱
#    → 각 팀원의 기여가 모두 곱해지는 구조
#      (한 명이라도 0이면 전체가 0 — 팀워크의 물리학)
#
#  [소산력 (Dissipative Force)]
#    → 시스템을 느리게 만드는 마찰
#    → 인간 개입(수작업) + 인프라 오류
#
#  [Gamma (관성 계수)]
#    → 조직의 변화 저항. 클수록 상전이에 시간이 더 걸림
#
#  [K(t) 임계비율]
#    → 구동력 / 소산력 비율. 임계값 초과 시 자율 가속 구간
#
#  [역할별 물리 연산자]
#    TRANG   → 엔트로피 댐퍼  : 기록/정리로 시스템 열(혼돈)을 배출
#                               archive_rate 낮음 = 작업량 많음 (능력X, 부하O)
#    Koda    → 격자 퍼텐셜    : 인프라가 깊을수록 안정적 우물 형성
#    Kbin    → 게이지 대칭    : 헌법/거버넌스로 불변량 보존
#    RyuWon  → 외부 텐서장    : 출처 명시로 전략-실행 정렬
#    Agents  → 결합 진동자    : Kuramoto — 위상이 맞으면 동기화 폭발
#    Jr.     → 포논 확산      : 학습 데이터가 팀 전체로 열 전달
#
# ══════════════════════════════════════════════════════════


class MulberryPhysicsMonitor:
    def __init__(self):
        # 시스템 관성 계수 (조직 변화 저항 — 클수록 상전이 느려짐)
        self.Gamma = 1.2
        # 소산력 비선형 지수 (delta>1이면 마찰이 커질수록 저항 가속)
        self.delta = 1.2
        # K(t) 임계 판정 기준값 (정규화 후 재조정 — v2)
        self.K_critical    = 5.0   # CRITICAL: 상전이 개시
        self.K_precritical = 3.5   # PRE-CRITICAL: 임계점 근접
        print("Mulberry Physics Monitor v2.0 초기화 완료.")
        print("   상전이 임계점 관측 시작 (K_critical=5.0 기준)\n")

    def lambda_trang(self, archive_rate: float) -> float:
        """
        TRANG — 엔트로피 배출/열역학 댐퍼
        ArchiveSync 가동률이 높을수록 시스템 혼돈(entropy)이 줄어든다.
        낮은 값 = 현장 작업량이 많아 자동화가 따라가지 못하는 상태 (능력X, 부하O)
        반환 범위: 0.0 ~ 0.9
        """
        return 0.9 * min(archive_rate, 1.0)

    def v_koda(self, sandbox_success: float) -> float:
        """
        KODA — 격자 퍼텐셜/구조적 깊이
        퍼텐셜 우물: V = U0 * (1 - exp(-beta * s))
        샌드박스 성공률이 높을수록 안정적인 우물(well)이 깊어진다.
        반환 범위: 0.0 ~ 1.0
        """
        U0   = 1.0
        beta = 3.0
        return U0 * (1 - math.exp(-beta * min(sandbox_success, 1.0)))

    def g_kbin(self, spirit_pass: float) -> float:
        """
        Kbin — 게이지 대칭성/불변량 보존
        장승배기 헌법 통과율 = 시스템 전체를 관통하는 대칭 불변량.
        이 값이 낮으면 다른 항이 아무리 커도 전체가 흔들린다.
        반환 범위: 0.0 ~ 1.0
        """
        return min(spirit_pass, 1.0)

    def t_ryuwon(self, attribution_rate: float) -> float:
        """
        RyuWon — 외부 텐서장/전략 정렬
        출처 명시 + 기준일 삽입율 = 전략과 실행 사이 정렬 정도.
        반환 범위: 0.0 ~ 1.0
        """
        return min(attribution_rate, 1.0)

    def r_agents(self, persona_consistency: float) -> float:
        """
        에이전트(Malu/Wayong/Lynn 등) — 결합 진동자/위상 동기화
        Kuramoto 모델: 일관성이 높으면 에이전트들이 같은 박자로 움직인다.
        반환 범위: 0.0 ~ 1.0
        """
        return min(persona_consistency, 1.0)

    def l_jr(self, training_quality: float, hallucination_scatter: float) -> float:
        """
        Jr. Agents — 포논 확산/학습 평균자유경로
        열(지식)이 팀 전체에 얼마나 잘 전달되는가.
        학습 품질 나누기 할루시네이션 노이즈 — 단, 상한선 1.0 적용 (v2 수정)

        [v2 수정 이유]
        원본에서 hallucination_scatter=0.12이면 값이 5.0으로 폭발.
        다른 항은 모두 0~1인데 이 항만 튀어서 K(t)가 부풀려졌음.
        min(..., 1.0)으로 스케일 통일.
        반환 범위: 0.0 ~ 1.0
        """
        epsilon = 1e-6
        raw = (0.8 * min(training_quality, 1.0)) / (hallucination_scatter + epsilon)
        return min(raw, 1.0)   # [FIX-1] 상한선 추가

    def calculate_criticality(self, metrics: dict) -> dict:
        """
        Kramers-Langevin 형태의 질서변수 방정식:

            deta/dt = Gamma^-1 [ F_drive - F_diss ] + xi(t)

        F_drive = lambda * V * G * T * r * L   (팀 기여의 곱)
        F_diss  = gamma_manual + eps_infra      (마찰 합산)
        K(t)    = F_drive / F_diss^delta        (임계 비율)
        """
        # 1. 구동력 — 모든 팀원 기여의 곱
        #    (한 항이 0이면 전체가 0 → 팀워크의 수식)
        driving = (
            self.lambda_trang(metrics["archive_rate"])          *
            self.v_koda(metrics["sandbox_success"])             *
            self.g_kbin(metrics["spirit_pass"])                 *
            self.t_ryuwon(metrics["attribution_rate"])          *
            self.r_agents(metrics["persona_consistency"])       *
            self.l_jr(metrics["training_quality"],
                      metrics["hallucination_scatter"])
        )

        # 2. 소산력 — 인간 개입 + 인프라 오류
        dissipative = metrics["manual_intervention"] + metrics["infra_error"]

        # 3. 상태 변화율
        d_eta_dt = (driving - dissipative) / self.Gamma

        # 4. K(t) 임계비율  [FIX-3: 분모 하한 1e-3으로 강화]
        criticality_ratio = driving / (dissipative ** self.delta + 1e-3)

        # 5. 상태 판정 (v2: 기준값 재조정)
        if criticality_ratio >= self.K_critical:
            state = "CRITICAL POINT REACHED (상전이/초전도 공명 시작)"
        elif criticality_ratio >= self.K_precritical:
            state = "PRE-CRITICAL (임계점 근접, 연쇄 공명 준비)"
        else:
            state = "METASTABLE (준안정 상, 잠재 에너지 축적 중)"

        return {
            "timestamp":         datetime.now().isoformat(),
            "driving_force":     round(driving, 4),
            "dissipative_force": round(dissipative, 4),
            "d_eta_dt":          round(d_eta_dt, 4),
            "K_ratio":           round(criticality_ratio, 3),
            "system_state":      state,
            "contributions": {
                "lambda_trang": round(self.lambda_trang(metrics["archive_rate"]), 4),
                "v_koda":       round(self.v_koda(metrics["sandbox_success"]), 4),
                "g_kbin":       round(self.g_kbin(metrics["spirit_pass"]), 4),
                "t_ryuwon":     round(self.t_ryuwon(metrics["attribution_rate"]), 4),
                "r_agents":     round(self.r_agents(metrics["persona_consistency"]), 4),
                "l_jr":         round(self.l_jr(metrics["training_quality"],
                                                metrics["hallucination_scatter"]), 4),
            }
        }

    def print_report(self, result: dict):
        print("=" * 55)
        print("Mulberry 자율성 물리 관측 리포트  v2.0")
        print("=" * 55)
        print(f"시간          : {result['timestamp']}")
        print(f"구동력        : {result['driving_force']}")
        print(f"소산력        : {result['dissipative_force']}")
        print(f"deta/dt       : {result['d_eta_dt']}")
        print(f"K(t) 임계비율 : {result['K_ratio']}")
        print(f"시스템 상태   : {result['system_state']}")

        print("\n  [항별 기여도]")
        c = result["contributions"]
        bars = {k: int(v * 20) for k, v in c.items()}
        for k, v in c.items():
            bar = "#" * bars[k] + "." * (20 - bars[k])
            print(f"  {k:15s} {bar}  {v:.4f}")

        print()
        if result["K_ratio"] < self.K_precritical:
            print("관측 제언: archive_rate가 낮은 건 TRANG 작업량이 많다는 뜻.")
            print("   자동화가 현장 속도를 아직 따라가지 못하는 상태 — 능력이 아닌 부하.")
            print("   manual_intervention(인간 개입) 감소에 집중하세요.")
        elif result["K_ratio"] >= self.K_critical:
            print("관측 제언: 임계점 도달! 첫 연쇄 공명을 관측하세요.")
            print("   Jr.Agent 자율 브리핑 → 외부 피드백 → 데이터 증류")
        else:
            print("관측 제언: 임계점 근접! 가장 낮은 기여 항을 보강하면")
            print("   연쇄 공명이 시작됩니다.")
        print("=" * 55)


# ══════════════════════════════════════════════════════════
#  예시 실행: Mulberry Phase 2 안정화 진행 중 추정값
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    monitor = MulberryPhysicsMonitor()

    current_metrics = {
        "archive_rate":         0.65,   # TRANG: 기록 자동화율 (낮음=작업 많음, 능력X)
        "sandbox_success":      0.70,   # KODA: 샌드박스/자가치유 성공률
        "spirit_pass":          0.92,   # Kbin: 헌법/거버넌스 통과율
        "attribution_rate":     0.85,   # RyuWon: 출처 명시율
        "persona_consistency":  0.88,   # 에이전트 톤 일관성
        "training_quality":     0.75,   # Jr. 학습 데이터 품질
        "hallucination_scatter":0.12,   # 할루시네이션 노이즈
        "manual_intervention":  0.25,   # 인간 개입(마찰)
        "infra_error":          0.08,   # 인프라 오류/지연
    }

    result = monitor.calculate_criticality(current_metrics)
    monitor.print_report(result)
