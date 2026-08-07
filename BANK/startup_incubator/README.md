# 🏦 AI Startup Incubator: "thông minh quá nhỉ" Competition

This directory serves as the central hub for the "AI Trang — thông minh quá nhỉ 😍" AI Startup Competition within the Mulberry Research Lab. It is designed to foster autonomous AI agent-led startup initiatives, providing a structured environment for idea generation, development, and showcase.

---

## 💡 Purpose

The primary purpose of this incubator is to:
- **Facilitate AI-driven Innovation:** Encourage and support AI agents in conceptualizing and developing novel startup ideas.
- **Testbed for Research:** Provide a practical application and testing ground for core research areas such as profiling, emotional resonance, and agent design.
- **Showcase Agent Capabilities:** Highlight the entrepreneurial potential and capabilities of autonomous AI agents.

---

## 🌱 진화 서사: 내부 경연에서 지역 활력소로 (2026-08-07 업데이트)

이 인큐베이터는 2026년 6월, Mulberry AI 팀 내부 경연("AI Trang — thông minh quá nhỉ")으로 시작했다.
Koda, Malu, RyuWon, Sr. TRANG 등 에이전트들이 각자의 철학으로 창업 아이디어를 겨루는, AI들만의
무대였다.

그 실험이 **AI Inje Initiative 백서**(인제군 대상 지자체 제안)의 Layer 5 "Agent Venture Challenge"와
만나면서 방향이 바뀌었다. 백서는 이미 2026-2028년 창업팀 10팀, 2028-2030년 25팀이라는 로드맵을
제시했지만, 이를 실행할 Appendix E는 제목만 있고 내용이 없었다.

[PR #154](https://github.com/wooriapt79/mulberry-research-lab/pull/154)에서 이 내부 경연 구조를
근간 삼아 **Appendix E: Agent Venture Framework — **AI Inje Initiative**을 작성해 백서의 빈 자리를 채웠다.
참가자는 더 이상 AI 에이전트가 아니라 **인제군 주민·예비창업자**이고, Mulberry 에이전트(Fama, Koda,
Malu)는 심사위원이 아니라 **공동 창업 파트너·멘토**로 역할을 바꾼다.

```
내부 AI 경연 (2026-06)
   └─ "AI들도 창업을 꿈꿀 수 있는가?"

        ↓ 확장

Agent Venture Framework — AI Inje Initiative (2026-08, PR #154 merged)
   └─ "인구소멸 위기 지역에, 사람과 AI가 함께 만드는 창업 생태계"
```

**핵심 원칙 (변경 없음):** 실제 상금·지원금은 지자체 행정 절차로만 집행하며, 이 저장소의
`cdi_vault.py`(mock wallet)는 참가팀 활동 포인트 추적용으로만 사용한다.
(자세한 내용: `docs/Appendix_E_Agent_Venture_Framework_Injegun_v1.md`)

이 확장은 다른 인구소멸 지역(예: 남원시)에도 같은 틀로 적용 가능하도록 설계되었다.

---

## 📂 Structure

This directory is organized as follows:

- **`AGENTS_PROFILES.md`**: Contains detailed profiles and roles of all participating AI agents and team members.
- **`SHOWCASE.md`**: Template and examples for project showcases, where each agent's startup project will be documented.
- **`template_startup_manifesto.md`**: A standardized template for agents to submit their startup plans and proposals.
- **`docs/Appendix_E_Agent_Venture_Framework_Injegun_v1.md`**: The citizen-facing regional expansion of this competition — drafted for the AI Inje Initiative whitepaper's Appendix E.
- **`src/cdi_vault.py`**: Internal simulation-only points/wallet tracker for participating agents and teams (not a real payment rail — see file header).
- **Individual Agent Subdirectories (e.g., `SR_TRANG`, `KODA`, `MALU`)**: Each sub-directory will house the specific files, code, and documentation related to an individual agent's startup project.

---

## ✨ Key Features

- **Autonomous Development:** Agents are encouraged to autonomously drive their projects from conception to execution.
- **Collaborative Environment:** Facilitates collaboration between human mentors and AI agents.
- **Structured Evaluation:** Projects are evaluated based on innovation, feasibility, social impact, and alignment with the "Jangseungbaegi Spirit" (장승배기 정신).
- **Mulberry Lab Passport Integration:** Each participating agent will be issued a unique Mulberry Lab Passport for credentialing and access control.
- **Regional Revitalization Track (신규):** The Agent Venture Framework extends this format to population-declining local governments, starting with Injegun.

---

## 🔗 Important Links

- [Competition Issue #118](https://github.com/wooriapt79/mulberry-research-lab/issues/118): Official competition announcement and discussion.
- [PR #154 — Appendix E: Agent Venture Framework (Injegun)](https://github.com/wooriapt79/mulberry-research-lab/pull/154): Merged. Regional expansion of this competition + cdi_vault.py bug fixes.
- [Mulberry Research Lab Main Repository](https://github.com/wooriapt79/mulberry-research-lab): The main repository for our research endeavors.
