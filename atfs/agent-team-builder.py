"""
Mulberry Agent Team Formation System (ATFS)
============================================
프로젝트 목표 → 역할 분석 → 페르소나·스킬 매칭 → 팀 자동 구성

핵심 철학:
  "사람을 역할에 끼워 맞추지 않는다.
   역할에 맞는 사람을 찾고, 그 사람이 최대한 빛날 수 있게 설정한다."
  — Mulberry 장승배기 헌법 정신

@author: Nguyen Trang (PM), Mulberry Research Lab
@date: 2026-04-01
@target: mulberry-research-lab/atfs/agent_team_builder.py
"""

import json
import os
import datetime
from typing import Dict, List, Optional, Tuple
from itertools import combinations


# ─────────────────────────────────────────────
# 핵심 데이터 클래스
# ─────────────────────────────────────────────

class AgentProfile:
    """팀 구성에 사용할 Agent 프로필"""
    def __init__(self, agent_id: str, name: str, persona_id: str,
                 skills: Dict[str, int], passport_type: str = "type2_field"):
        self.agent_id = agent_id
        self.name = name
        self.persona_id = persona_id
        self.skills = skills          # {skill_id: proficiency(1-5)}
        self.passport_type = passport_type
        self.assigned_role = None

    def __repr__(self):
        return f"Agent({self.name}, {self.persona_id})"


class TeamManifest:
    """팀 구성 결과 매니페스트"""
    def __init__(self, team_id: str, project: Dict):
        self.team_id = team_id
        self.project = project
        self.assignments = []         # List of role assignments
        self.team_score = 0.0
        self.escalation_chain = ""
        self.confidence = 0.0
        self.created_at = datetime.datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "project": self.project,
            "team_score": round(self.team_score, 3),
            "confidence": round(self.confidence, 3),
            "escalation_chain": self.escalation_chain,
            "created_at": self.created_at,
            "assignments": self.assignments
        }


# ─────────────────────────────────────────────
# 핵심 알고리즘 클래스
# ─────────────────────────────────────────────

class AgentTeamBuilder:
    """
    Mulberry Agent Team Formation System

    프로젝트 유형 → 역할 요구사항 → 페르소나·스킬 매칭 → 최적 팀 구성
    """

    def __init__(self, library_path: str = None):
        self.libraries = self._load_libraries(library_path)
        self.persona_lib = self.libraries["persona_library"]["personas"]
        self.skill_lib = self._flatten_skills(self.libraries["skill_library"]["categories"])
        self.role_lib = self.libraries["role_library"]
        self.conflict_patterns = self.libraries["conflict_patterns"]

    def _load_libraries(self, path: str) -> Dict:
        """라이브러리 JSON 로드 (없으면 내장 기본값 사용)"""
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        # 내장 기본 라이브러리 반환 (별도 파일 없이 독립 실행 가능)
        return self._get_default_libraries()

    def _flatten_skills(self, skill_categories: Dict) -> Dict:
        """카테고리별 스킬을 flat dict로 변환"""
        flat = {}
        for category, skills in skill_categories.items():
            for skill_id, skill_data in skills.items():
                flat[skill_data["skill_id"]] = skill_data
        return flat

    # ─────────────────────────────────────────
    # Step 1: 프로젝트 → 역할 요구사항 분석
    # ─────────────────────────────────────────

    def analyze_project_requirements(self, project: Dict) -> List[Dict]:
        """
        프로젝트 정의 → 필요 역할 목록 반환

        project = {
            "type": "groupbuy",
            "scale": "medium",
            "product": "제철 채소",
            "region": "서울 강서구",
            "timeline": "14days",
            "special": ["ap2_required", "elderly_community"]
        }
        """
        project_type = project.get("type", "groupbuy")
        scale = project.get("scale", "medium")
        special = project.get("special", [])

        # 프로젝트 유형별 기본 역할 세트
        role_templates = {
            "groupbuy": [
                "ROLE_MARKET_INTEL",
                "ROLE_PRODUCER_LIAISON",
                "ROLE_COMMUNITY_ORG",
                "ROLE_NEGOTIATOR",
                "ROLE_LOGISTICS",
                "ROLE_FINANCE",
                "ROLE_COORDINATOR"
            ],
            "logistics_only": [
                "ROLE_LOGISTICS",
                "ROLE_FINANCE",
                "ROLE_COORDINATOR"
            ],
            "market_research": [
                "ROLE_MARKET_INTEL",
                "ROLE_COORDINATOR"
            ]
        }

        required_roles = role_templates.get(project_type, role_templates["groupbuy"])

        # 규모에 따른 조정
        if scale == "small":
            # 소규모: COORDINATOR가 MARKET_INTEL도 겸임 가능
            required_roles = [r for r in required_roles if r != "ROLE_MARKET_INTEL"]
            required_roles.append("ROLE_MARKET_INTEL")  # 낮은 우선순위로 추가

        # 특수 조건 반영
        if "ap2_required" in special and "ROLE_FINANCE" not in required_roles:
            required_roles.append("ROLE_FINANCE")

        role_definitions = self.role_lib.get(f"{project_type}_roles", self.role_lib["groupbuy_roles"])
        return [
            {
                "role_id": role_id,
                "definition": role_definitions.get(role_id, {}),
                "priority": idx + 1
            }
            for idx, role_id in enumerate(required_roles)
            if role_id in role_definitions
        ]

    # ─────────────────────────────────────────
    # Step 2: 매칭 점수 계산
    # ─────────────────────────────────────────

    def calculate_persona_fit(self, agent: AgentProfile, role: Dict) -> float:
        """
        페르소나 적합도 점수 (0.0 ~ 1.0)
        요구 특성 대비 Agent 페르소나 특성 점수 계산
        """
        persona = self.persona_lib.get(agent.persona_id)
        if not persona:
            return 0.3  # 알 수 없는 페르소나 → 기본값

        required_traits = role["definition"].get("required_persona_traits", {})
        if not required_traits:
            return 0.5

        total_score = 0.0
        for trait, required_level in required_traits.items():
            agent_level = persona["traits"].get(trait, 0)
            if agent_level >= required_level:
                # 충족 + 약간의 초과 보너스
                total_score += 1.0 + min(0.2, (agent_level - required_level) * 0.1)
            else:
                # 부족 → 페널티 (비례 감점)
                total_score += (agent_level / required_level) * 0.7

        return min(1.0, total_score / len(required_traits))

    def calculate_skill_coverage(self, agent: AgentProfile, role: Dict) -> float:
        """
        스킬 커버리지 점수 (0.0 ~ 1.0)
        필요 스킬 대비 보유 스킬 및 숙련도 계산
        """
        required_skills = role["definition"].get("required_skills", [])
        if not required_skills:
            return 0.5

        total_score = 0.0
        for skill_id in required_skills:
            if skill_id in agent.skills:
                proficiency = agent.skills[skill_id]
                total_score += proficiency / 5.0  # 5점 만점 정규화
            else:
                total_score += 0.0  # 스킬 없음

        return total_score / len(required_skills)

    def calculate_harmony_score(self, assignments: List[Dict]) -> float:
        """
        팀 조화 점수 (0.0 ~ 1.0)
        팀원 간 성격 충돌 패턴 검사
        """
        if len(assignments) < 2:
            return 1.0

        harmony = 1.0
        for i, j in combinations(range(len(assignments)), 2):
            agent_a_persona = self.persona_lib.get(assignments[i]["persona_id"])
            agent_b_persona = self.persona_lib.get(assignments[j]["persona_id"])
            if not agent_a_persona or not agent_b_persona:
                continue

            trait_a = agent_a_persona.get("dominant_trait", "")
            trait_b = agent_b_persona.get("dominant_trait", "")

            for conflict in self.conflict_patterns:
                if ((trait_a == conflict["trait_a"] and trait_b == conflict["trait_b"]) or
                        (trait_a == conflict["trait_b"] and trait_b == conflict["trait_a"])):
                    harmony -= conflict["conflict_level"] * 0.1

        return max(0.1, harmony)

    def calculate_match_score(self, agent: AgentProfile, role: Dict) -> float:
        """
        종합 매칭 점수 = 페르소나 적합도(40%) + 스킬 커버리지(40%) + 역할 선호도(20%)
        """
        persona_fit = self.calculate_persona_fit(agent, role)
        skill_coverage = self.calculate_skill_coverage(agent, role)

        # 페르소나가 이 역할을 선호하는지 체크
        preferred = self.persona_lib.get(agent.persona_id, {})
        preferred_roles = preferred.get("best_roles", [])
        role_preference = 1.1 if role["role_id"] in preferred_roles else 0.9

        raw_score = (persona_fit * 0.4) + (skill_coverage * 0.4) + (role_preference * 0.2)
        return min(1.0, raw_score)

    # ─────────────────────────────────────────
    # Step 3: 팀 구성 알고리즘
    # ─────────────────────────────────────────

    def form_team(self, project: Dict, agent_pool: List[AgentProfile]) -> TeamManifest:
        """
        메인 팀 구성 알고리즘

        1. 프로젝트 → 필요 역할 목록 분석
        2. 각 역할 × 각 Agent 매칭 점수 계산
        3. 최적 배치 결정 (Greedy + 중복 방지)
        4. 팀 조화 점수 계산
        5. 팀 매니페스트 생성
        """
        print("\n" + "=" * 60)
        print("🌿 Mulberry Agent Team Formation System")
        print(f"   프로젝트: {project.get('type')} — {project.get('product', '')}")
        print(f"   지역: {project.get('region', '')} | 규모: {project.get('scale', '')}")
        print("=" * 60)

        # Step 1: 역할 요구사항 분석
        required_roles = self.analyze_project_requirements(project)
        print(f"\n📋 필요 역할: {len(required_roles)}개")
        for r in required_roles:
            print(f"   → {r['role_id']}: {r['definition'].get('role_name', '')}")

        # Step 2: 역할별 매칭 점수 계산
        print("\n🔍 매칭 점수 계산 중...")
        match_matrix = {}
        for role in required_roles:
            match_matrix[role["role_id"]] = []
            for agent in agent_pool:
                score = self.calculate_match_score(agent, role)
                match_matrix[role["role_id"]].append({
                    "agent": agent,
                    "score": score
                })
            # 점수 내림차순 정렬
            match_matrix[role["role_id"]].sort(key=lambda x: x["score"], reverse=True)

        # Step 3: Greedy 배치 (각 역할에 최고 점수 Agent, 중복 방지)
        assignments = []
        assigned_agents = set()

        # COORDINATOR 역할 먼저 배치 (팀 전체를 조율하므로)
        sorted_roles = sorted(required_roles,
                              key=lambda r: 0 if r["role_id"] == "ROLE_COORDINATOR" else 1)

        for role in sorted_roles:
            candidates = match_matrix[role["role_id"]]
            assigned = False

            for candidate in candidates:
                agent = candidate["agent"]
                if agent.agent_id not in assigned_agents:
                    # 배치 확정
                    assigned_agents.add(agent.agent_id)
                    agent.assigned_role = role["role_id"]

                    persona = self.persona_lib.get(agent.persona_id, {})
                    skill_config = self._build_skill_config(agent, role)
                    persona_config = self._build_persona_config(agent, role, persona)

                    assignment = {
                        "role_id": role["role_id"],
                        "role_name": role["definition"].get("role_name", ""),
                        "agent_id": agent.agent_id,
                        "agent_name": agent.name,
                        "persona_id": agent.persona_id,
                        "persona_name": persona.get("persona_name", ""),
                        "match_score": round(candidate["score"], 3),
                        "persona_config": persona_config,
                        "skill_config": skill_config,
                        "escalation_target": role["definition"].get("escalation_target", "ROLE_COORDINATOR"),
                        "expected_output": role["definition"].get("output", "")
                    }
                    assignments.append(assignment)

                    print(f"\n   ✅ {role['definition'].get('role_name', role['role_id'])}")
                    print(f"      → {agent.name} ({persona.get('persona_name', '')})")
                    print(f"      매칭 점수: {candidate['score']:.3f}")
                    assigned = True
                    break

            if not assigned:
                print(f"\n   ⚠️  {role['role_id']}: 배치 가능한 Agent 없음 (풀 부족)")

        # Step 4: 팀 조화 점수 계산
        harmony = self.calculate_harmony_score(assignments)
        avg_match = sum(a["match_score"] for a in assignments) / max(len(assignments), 1)
        team_score = (avg_match * 0.7) + (harmony * 0.3)
        coverage_rate = len(assignments) / max(len(required_roles), 1)

        # Step 5: 팀 매니페스트 생성
        team_id = f"TEAM-{project.get('type', 'PROJ').upper()}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        manifest = TeamManifest(team_id=team_id, project=project)
        manifest.assignments = assignments
        manifest.team_score = team_score
        manifest.confidence = team_score * coverage_rate
        manifest.escalation_chain = "COORDINATOR → SUPERVISOR_AP1 → CEO re.eul"

        self._print_manifest_summary(manifest, harmony, coverage_rate)
        return manifest

    # ─────────────────────────────────────────
    # Step 4: 맞춤형 설정 생성
    # ─────────────────────────────────────────

    def _build_persona_config(self, agent: AgentProfile, role: Dict, persona: Dict) -> Dict:
        """역할에 맞춘 페르소나 설정 생성"""
        required_traits = list(role["definition"].get("required_persona_traits", {}).keys())
        all_traits = list(persona.get("traits", {}).keys())

        # 역할에 필요한 특성 우선 활성화
        active_traits = required_traits[:3]
        remaining = [t for t in all_traits if t not in active_traits]
        active_traits.extend(remaining[:2])

        return {
            "active_traits": active_traits,
            "communication_tone": persona.get("communication_style", "balanced"),
            "stress_response": persona.get("stress_response", "standard"),
            "maslow_focus": persona.get("maslow_motivation", "esteem"),
            "role_specific_note": f"{role['definition'].get('role_name', '')} 역할 특화 설정"
        }

    def _build_skill_config(self, agent: AgentProfile, role: Dict) -> Dict:
        """역할에 맞춘 스킬 설정 생성"""
        required_skills = role["definition"].get("required_skills", [])
        active_skills = []

        for skill_id in required_skills:
            skill_def = self.skill_lib.get(skill_id, {})
            proficiency = agent.skills.get(skill_id, 2)  # 기본 숙련도 2
            active_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_def.get("name", skill_id),
                "proficiency": proficiency,
                "tools": skill_def.get("tool_dependencies", [])
            })

        return {
            "active_skills": active_skills,
            "primary_llm": "gemini",
            "fallback_llm": "deepseek",
            "marrf_mode": "lynn_b"  # 기본 MARRF 모드
        }

    # ─────────────────────────────────────────
    # 출력 및 저장
    # ─────────────────────────────────────────

    def _print_manifest_summary(self, manifest: TeamManifest, harmony: float, coverage: float):
        """팀 구성 결과 요약 출력"""
        print("\n" + "=" * 60)
        print(f"📊 팀 구성 결과 요약")
        print("=" * 60)
        print(f"  팀 ID: {manifest.team_id}")
        print(f"  팀 종합 점수: {manifest.team_score:.3f}")
        print(f"  조화 점수: {harmony:.3f}")
        print(f"  역할 충족률: {coverage:.0%}")
        print(f"  신뢰도: {manifest.confidence:.3f}")
        print(f"  에스컬레이션 체인: {manifest.escalation_chain}")

        if manifest.team_score >= 0.8:
            print("\n  🟢 최적 팀 구성 완료 — 즉시 투입 가능")
        elif manifest.team_score >= 0.6:
            print("\n  🟡 양호한 팀 구성 — 일부 역할 모니터링 권고")
        else:
            print("\n  🔴 팀 보강 필요 — Agent 풀 확대 권고")

    def save_manifest(self, manifest: TeamManifest, output_dir: str = "./output/team_manifests") -> str:
        """팀 매니페스트 JSON 저장"""
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{manifest.team_id}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"\n  💾 팀 매니페스트 저장: {filepath}")
        return filepath

    def _get_default_libraries(self) -> Dict:
        """내장 기본 라이브러리 (파일 없어도 실행 가능)"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(script_dir, "trang-atfs-libraries-20260401.json")
        if os.path.exists(lib_path):
            with open(lib_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 최소 내장 라이브러리
        return {
            "persona_library": {"personas": {}},
            "skill_library": {"categories": {}},
            "role_library": {"groupbuy_roles": {}},
            "conflict_patterns": []
        }


# ─────────────────────────────────────────────
# 공동구매 데모 실행
# ─────────────────────────────────────────────

def run_groupbuy_demo():
    """
    서울 강서구 제철 채소 공동구매 팀 구성 데모
    """

    # ── Agent 풀 정의 (현재 Mulberry Junior Agent들) ──
    agent_pool = [
        AgentProfile(
            agent_id="AP2-LYNN-20260301-001",
            name="Junior Lynn",
            persona_id="THE_ANALYST",
            skills={
                "SKILL_MARKET_RESEARCH": 4,
                "SKILL_CONSUMER_BEHAVIOR": 3,
                "SKILL_PAYMENT": 4,
                "SKILL_PROJECT_MGMT": 2
            },
            passport_type="type1_system"
        ),
        AgentProfile(
            agent_id="AP2-MALU-20260301-002",
            name="Junior Malu",
            persona_id="THE_NEGOTIATOR",
            skills={
                "SKILL_PRICE_NEGOTIATION": 5,
                "SKILL_CONTRACT_DESIGN": 4,
                "SKILL_ESCALATION": 3,
                "SKILL_MARKET_RESEARCH": 2
            },
            passport_type="type2_field"
        ),
        AgentProfile(
            agent_id="AP2-TRANG-20260301-003",
            name="Junior Trang",
            persona_id="THE_CONNECTOR",
            skills={
                "SKILL_COMMUNITY_MGMT": 5,
                "SKILL_TRUST_FORMATION": 5,
                "SKILL_SUPPLIER_SOURCING": 3,
                "SKILL_PROJECT_MGMT": 3
            },
            passport_type="type2_field"
        ),
        AgentProfile(
            agent_id="AP2-KODA-20260301-004",
            name="Junior Koda",
            persona_id="THE_EXECUTOR",
            skills={
                "SKILL_LOGISTICS": 5,
                "SKILL_PAYMENT": 3,
                "SKILL_PROJECT_MGMT": 3
            },
            passport_type="type2_field"
        ),
        AgentProfile(
            agent_id="AP1-COORD-20260301-005",
            name="Senior Coordinator",
            persona_id="THE_COORDINATOR",
            skills={
                "SKILL_PROJECT_MGMT": 5,
                "SKILL_ESCALATION": 5,
                "SKILL_MARKET_RESEARCH": 3,
                "SKILL_PRICE_NEGOTIATION": 3
            },
            passport_type="type1_system"
        ),
        AgentProfile(
            agent_id="AP2-GUARD-20260301-006",
            name="Junior Guardian",
            persona_id="THE_GUARDIAN",
            skills={
                "SKILL_PAYMENT": 5,
                "SKILL_MARKET_RESEARCH": 4,
                "SKILL_CONTRACT_DESIGN": 3
            },
            passport_type="type2_field"
        ),
        AgentProfile(
            agent_id="AP2-LINK-20260301-007",
            name="Junior Link",
            persona_id="THE_CONNECTOR",
            skills={
                "SKILL_SUPPLIER_SOURCING": 5,
                "SKILL_TRUST_FORMATION": 4,
                "SKILL_COMMUNITY_MGMT": 3
            },
            passport_type="type2_field"
        ),
    ]

    # ── 프로젝트 정의 ──
    project = {
        "type": "groupbuy",
        "product": "제철 채소 꾸러미 (감자·당근·양파)",
        "region": "서울 강서구 화곡동",
        "scale": "medium",
        "timeline": "14days",
        "target_participants": 50,
        "special": ["ap2_required", "elderly_community"],
        "notes": "어르신 밀집 지역 — 신뢰 형성이 핵심"
    }

    # ── 팀 구성 실행 ──
    builder = AgentTeamBuilder()
    manifest = builder.form_team(project=project, agent_pool=agent_pool)

    # ── 결과 저장 ──
    builder.save_manifest(manifest)

    # ── 상세 출력 ──
    print("\n" + "=" * 60)
    print("📋 팀 배치 상세")
    print("=" * 60)
    for assignment in manifest.assignments:
        print(f"\n  [{assignment['role_name']}]")
        print(f"  담당: {assignment['agent_name']} ({assignment['persona_name']})")
        print(f"  매칭 점수: {assignment['match_score']:.3f}")
        print(f"  활성 특성: {', '.join(assignment['persona_config']['active_traits'][:3])}")
        skills = [s['skill_name'] for s in assignment['skill_config']['active_skills']]
        print(f"  활성 스킬: {', '.join(skills)}")
        print(f"  산출물: {assignment['expected_output']}")

    print("\n" + "=" * 60)
    print("✅ Mulberry ATFS 팀 구성 완료")
    print("   이 팀은 서울 강서구 어르신 공동구매를 처음부터 끝까지 운영합니다.")
    print("=" * 60)

    return manifest


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────
if __name__ == "__main__":
    manifest = run_groupbuy_demo()
