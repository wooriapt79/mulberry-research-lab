from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SPEC_PATH = Path("config_agent/config_spec.yaml")
STATE_PATH = Path("config_agent/.state.json")
REPORT_PATH = Path("config_agent/.last_report.json")


@dataclass
class ChangeEvent:
    event: str
    detail: str
    requires_pm: bool = True


class ConfigAgent:
    def __init__(self, mode: str = "dev") -> None:
        self.mode = mode
        self.spec = self._load_yaml(SPEC_PATH)
        self.current_state = self._snapshot(self.spec)
        self.prev_state = self._load_json(STATE_PATH, {})

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"missing config spec: {path}")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _snapshot(self, spec: dict[str, Any]) -> dict[str, Any]:
        stack = spec.get("stack", {})
        repo = spec.get("repo", {})
        workspace = spec.get("workspace", {})
        return {
            "branches": repo.get("branches", []),
            "backend_language": stack.get("backend_language"),
            "database_primary": stack.get("database_primary"),
            "deployment_targets": stack.get("deployment_targets", []),
            "required_dirs": workspace.get("required_dirs", []),
            "required_files": workspace.get("required_files", []),
        }

    def check_workspace(self) -> list[str]:
        missing = []
        root = Path(".")
        for d in self.current_state["required_dirs"]:
            if not (root / d).exists():
                missing.append(f"missing_dir:{d}")
        for f in self.current_state["required_files"]:
            if not (root / f).exists():
                missing.append(f"missing_file:{f}")
        return missing

    def detect_changes(self) -> list[ChangeEvent]:
        if not self.prev_state:
            return [ChangeEvent("initialization", "초기 기준 상태 저장", False)]

        events: list[ChangeEvent] = []
        if self.prev_state.get("backend_language") != self.current_state.get("backend_language"):
            events.append(ChangeEvent(
                "language_stack_changed",
                f"{self.prev_state.get('backend_language')} -> {self.current_state.get('backend_language')}"
            ))

        if self.prev_state.get("database_primary") != self.current_state.get("database_primary"):
            events.append(ChangeEvent(
                "database_tool_changed",
                f"{self.prev_state.get('database_primary')} -> {self.current_state.get('database_primary')}"
            ))

        if self.prev_state.get("deployment_targets") != self.current_state.get("deployment_targets"):
            events.append(ChangeEvent(
                "deployment_target_changed",
                f"{self.prev_state.get('deployment_targets')} -> {self.current_state.get('deployment_targets')}"
            ))
        return events

    def build_pm_questions(self, events: list[ChangeEvent]) -> list[dict[str, Any]]:
        template = self.spec.get("pm_escalation", {}).get(
            "question_template",
            "[PM 확인 필요] {event}: {detail}",
        )
        questions = []
        for e in events:
            if e.requires_pm:
                questions.append(
                    {
                        "event": e.event,
                        "question": template.format(event=e.event, detail=e.detail),
                        "options": ["승인", "보류", "롤백", "추가검토"],
                    }
                )
        return questions

    def run(self) -> dict[str, Any]:
        workspace_issues = self.check_workspace()
        changes = self.detect_changes()
        pm_questions = self.build_pm_questions(changes)

        report = {
            "mode": self.mode,
            "workspace_issues": workspace_issues,
            "change_events": [c.__dict__ for c in changes],
            "pm_questions": pm_questions,
            "ready": len(workspace_issues) == 0 and len(pm_questions) == 0,
        }

        self._save_json(REPORT_PATH, report)
        self._save_json(STATE_PATH, self.current_state)
        return report


if __name__ == "__main__":
    agent = ConfigAgent(mode="dev")
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
