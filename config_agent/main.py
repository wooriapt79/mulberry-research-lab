#!/usr/bin/env python3
"""
config_agent/main.py — Mulberry DNA 환경 초기화 에이전트
=========================================================
역할:
  어떤 서버든 Mulberry DNA에 맞게 초기 환경을 자동 설정한다.
  자율 코딩 생성기(Auto Code Pilot)와 연동하여:
    고객 요청 → 코드 생성 → 환경 설정 → 배포 → URL 전달

흐름:
  1. config_spec.yaml (Mulberry DNA) 로드
  2. 워크스페이스 구조 검증 + 자동 생성
  3. 배포 환경 파일 생성 (Procfile, requirements.txt 등)
  4. 변경 감지 → PM 에스컬레이션
  5. 결과 리포트 → Auto Code Pilot에 전달

작성: Koda CTO · Koda Coding Team · 2026-05-31
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── 경로 ────────────────────────────────────────────────────────────
SPEC_PATH   = Path("config_agent/config_spec.yaml")
STATE_PATH  = Path("config_agent/.state.json")
REPORT_PATH = Path("config_agent/.last_report.json")
TIMESTAMP   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 데이터 클래스 ────────────────────────────────────────────────────

@dataclass
class ChangeEvent:
    event: str
    detail: str
    requires_pm: bool = True


@dataclass
class DeployContext:
    """Auto Code Pilot에 전달되는 배포 컨텍스트"""
    target: str                          # railway / vercel / github_pages
    brand: str
    spirit: str
    backend_language: str
    frontend_style: str
    eta_minutes: int
    auto_files: dict[str, str] = field(default_factory=dict)  # 자동 생성 파일들
    ready: bool = False


# ── ConfigAgent ─────────────────────────────────────────────────────

class ConfigAgent:
    """
    Mulberry DNA 환경 초기화 에이전트.
    어떤 서버든 config_spec.yaml에 정의된 DNA로 초기 환경을 설정한다.
    """

    def __init__(self, mode: str = "dev") -> None:
        self.mode = mode
        self.spec = self._load_yaml(SPEC_PATH)
        self.current_state = self._snapshot(self.spec)
        self.prev_state = self._load_json(STATE_PATH, {})
        self.identity = self.spec.get("identity", {})
        self.dna = self.spec.get("dna", {})
        self.deployment = self.spec.get("deployment", {})
        self.customer_output = self.spec.get("customer_output", {})

    # ── 로드 유틸 ───────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Mulberry DNA 파일 없음: {path}")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _snapshot(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "backend_language": spec.get("dna", {}).get("backend_language"),
            "deployment_primary": spec.get("deployment", {}).get("primary"),
            "deployment_targets": list(spec.get("deployment", {}).get("targets", {}).keys()),
            "required_dirs": spec.get("workspace", {}).get("required_dirs", []),
        }

    # ── 워크스페이스 검증 + 자동 생성 ──────────────────────────────

    def setup_workspace(self, root: Path = Path(".")) -> dict[str, list]:
        """
        Mulberry DNA 기준으로 워크스페이스를 검증하고 자동 생성한다.
        고객 프로젝트 시작 전 반드시 실행.
        """
        workspace = self.spec.get("workspace", {})
        created = []
        missing = []

        # 필수 디렉토리 생성
        for d in workspace.get("required_dirs", []):
            target = root / d
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                created.append(f"dir:{d}")
                print(f"  ✅ 디렉토리 생성: {d}")

        # 필수 파일 자동 생성
        for f in workspace.get("auto_create", []):
            target = root / f
            if not target.exists():
                content = self._default_file_content(f)
                target.write_text(content, encoding="utf-8")
                created.append(f"file:{f}")
                print(f"  ✅ 파일 생성: {f}")

        # 검증
        for f in workspace.get("required_files", []):
            if not (root / f).exists():
                missing.append(f)

        return {"created": created, "missing": missing}

    def _default_file_content(self, filename: str) -> str:
        """Mulberry DNA 기반 기본 파일 내용"""
        brand   = self.identity.get("brand", "Mulberry")
        spirit  = self.identity.get("spirit", "jangseungbaegi")
        team    = self.identity.get("coding_team", "Koda Coding Team")
        lang    = self.dna.get("backend_language", "python")
        target  = self.deployment.get("primary", "railway")

        templates = {
            "README.md": (
                f"# {brand} Project\n\n"
                f"> {spirit} 정신 기반 — AI serves humans\n\n"
                f"## 시작하기\n\n```bash\npip install -r requirements.txt\npython main.py\n```\n\n"
                f"---\n*{brand} · {team} · {TIMESTAMP[:10]}*\n"
            ),
            ".gitignore": (
                "# Mulberry 기본 .gitignore\n"
                "__pycache__/\n*.pyc\n.env\n.env.local\n*.json.bak\n"
                ".state.json\n.last_report.json\ndist/\n.DS_Store\n"
            ),
            "requirements.txt": (
                f"# {brand} · {lang} 의존성\n"
                "fastapi>=0.110.0\nuvicorn>=0.29.0\npython-dotenv>=1.0.0\n"
                "httpx>=0.27.0\nanthropicAI>=0.26.0\n"
            ),
            "Procfile": (
                f"# Railway 배포용 — {brand} DNA\n"
                f"web: python main.py\n"
            ),
        }
        return templates.get(filename, f"# {filename} — {brand}\n")

    # ── 배포 환경 파일 생성 ─────────────────────────────────────────

    def generate_deploy_files(self, target: str = None, root: Path = Path(".")) -> dict[str, str]:
        """
        배포 대상에 맞는 환경 파일을 자동 생성한다.
        target: railway / vercel / github_pages
        """
        target = target or self.deployment.get("primary", "railway")
        generated = {}

        if target == "railway":
            # Procfile
            procfile = root / "Procfile"
            content = "web: python main.py\n"
            procfile.write_text(content, encoding="utf-8")
            generated["Procfile"] = content
            print(f"  🚂 Railway Procfile 생성 완료")

        elif target == "vercel":
            # vercel.json
            vercel_cfg = {
                "version": 2,
                "builds": [{"src": "*.html", "use": "@vercel/static"}],
                "routes": [{"src": "/(.*)", "dest": "/$1"}]
            }
            vercel_file = root / "vercel.json"
            vercel_file.write_text(
                json.dumps(vercel_cfg, indent=2), encoding="utf-8"
            )
            generated["vercel.json"] = json.dumps(vercel_cfg)
            print(f"  ▲ Vercel 설정 생성 완료")

        elif target == "github_pages":
            # .nojekyll
            nojekyll = root / ".nojekyll"
            nojekyll.write_text("", encoding="utf-8")
            generated[".nojekyll"] = ""
            print(f"  📄 GitHub Pages 설정 완료")

        return generated

    # ── 변경 감지 ───────────────────────────────────────────────────

    def detect_changes(self) -> list[ChangeEvent]:
        if not self.prev_state:
            return [ChangeEvent("initialization", "Mulberry DNA 초기 기준 상태 저장", False)]

        events: list[ChangeEvent] = []
        checks = [
            ("backend_language",   "language_stack_changed"),
            ("deployment_primary", "deployment_target_changed"),
        ]
        for key, event_name in checks:
            prev = self.prev_state.get(key)
            curr = self.current_state.get(key)
            if prev and prev != curr:
                events.append(ChangeEvent(event_name, f"{prev} → {curr}"))

        return events

    def build_pm_questions(self, events: list[ChangeEvent]) -> list[dict[str, Any]]:
        template = self.spec.get("pm_escalation", {}).get(
            "question_template",
            "[ConfigAgent → Trang] {event}: {detail}",
        )
        return [
            {
                "event": e.event,
                "question": template.format(event=e.event, detail=e.detail),
                "options": ["승인", "보류", "롤백"],
            }
            for e in events if e.requires_pm
        ]

    # ── 배포 컨텍스트 생성 (→ Auto Code Pilot 전달) ────────────────

    def build_deploy_context(self, auto_files: dict) -> DeployContext:
        """
        Auto Code Pilot에 전달할 배포 컨텍스트 생성.
        코드 생성 전 이 컨텍스트를 읽어서 Mulberry DNA에 맞는 코드를 생성한다.
        """
        return DeployContext(
            target=self.deployment.get("primary", "railway"),
            brand=self.identity.get("brand", "Mulberry"),
            spirit=self.identity.get("spirit", "jangseungbaegi"),
            backend_language=self.dna.get("backend_language", "python"),
            frontend_style=self.dna.get("frontend_style", "vanilla-js"),
            eta_minutes=self.deployment.get("eta_minutes", 5),
            auto_files=auto_files,
            ready=True,
        )

    # ── 메인 실행 ───────────────────────────────────────────────────

    def run(self, deploy_target: str = None) -> dict[str, Any]:
        """
        환경 초기화 전체 실행.
        Auto Code Pilot 실행 전 반드시 호출.
        """
        print(f"\n{'='*55}")
        print(f"  Mulberry ConfigAgent v1.0")
        print(f"  DNA: {self.identity.get('brand')} · {self.identity.get('spirit')}")
        print(f"  배포 타겟: {deploy_target or self.deployment.get('primary')}")
        print(f"{'='*55}\n")

        # 1. 워크스페이스 셋업
        print("📁 [1/4] 워크스페이스 초기화...")
        workspace_result = self.setup_workspace()

        # 2. 배포 파일 생성
        print("🚀 [2/4] 배포 환경 파일 생성...")
        deploy_files = self.generate_deploy_files(target=deploy_target)

        # 3. 변경 감지
        print("🔍 [3/4] 변경 사항 감지...")
        changes = self.detect_changes()
        pm_questions = self.build_pm_questions(changes)

        # 4. 배포 컨텍스트 생성
        print("📦 [4/4] Auto Code Pilot 컨텍스트 준비...")
        deploy_ctx = self.build_deploy_context(deploy_files)

        # 리포트
        report = {
            "timestamp": TIMESTAMP,
            "mode": self.mode,
            "identity": self.identity,
            "workspace": workspace_result,
            "deploy_files": list(deploy_files.keys()),
            "changes": [c.__dict__ for c in changes],
            "pm_questions": pm_questions,
            "deploy_context": deploy_ctx.__dict__,
            "ready": deploy_ctx.ready and len(pm_questions) == 0,
        }

        self._save_json(REPORT_PATH, report)
        self._save_json(STATE_PATH, self.current_state)

        print(f"\n{'='*55}")
        if report["ready"]:
            print(f"  ✅ 환경 초기화 완료 — Auto Code Pilot 실행 가능")
            print(f"  🎯 고객 URL 예상: https://project.{deploy_ctx.target}.app")
        else:
            print(f"  ⚠️  PM 승인 대기 중 ({len(pm_questions)}건)")
        print(f"{'='*55}\n")

        return report


# ── 실행 ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry ConfigAgent")
    parser.add_argument("--target", default=None, help="배포 타겟 (railway/vercel/github_pages)")
    parser.add_argument("--mode",   default="dev", help="실행 모드 (dev/prod)")
    args = parser.parse_args()

    agent = ConfigAgent(mode=args.mode)
    result = agent.run(deploy_target=args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
