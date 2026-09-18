#!/usr/bin/env python3
"""Validate the Mulberry collaboration pilot configuration."""

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(relative_path: str):
    path = ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    yaml_paths = sorted(ROOT.rglob("*.yaml"))
    require(bool(yaml_paths), "No YAML files found", failures)

    for path in yaml_paths:
        try:
            with path.open(encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            failures.append(f"Invalid YAML: {path.relative_to(ROOT)}: {exc}")

    if failures:
        print("\n".join(f"ERROR: {item}" for item in failures))
        return 1

    policy = load("config/mulberry-policy.yaml")
    environment = load("config/pilot.environment.yaml")
    kebin = load("config/apps/kebin-chatgpt.yaml")
    deepseek = load("config/apps/deepseek-web.yaml")
    tests = load("tests/conformance-cases.yaml")

    identity = policy["policy_identity"]
    policy_id = identity["id"]
    version = identity["version"]

    require(policy["execution"]["fail_mode"] == "closed", "Policy must fail closed", failures)
    require(policy["execution"]["restricted_executor_required"] is True, "Restricted executor must be required", failures)
    require(policy["authority"]["model_credentials_allowed"] is False, "Models must not receive credentials", failures)
    require(policy["social_return"]["rate"] == 0.10, "Mutual-aid rate must be 10%", failures)
    require(policy["social_return"]["enforcement"] == "application_code", "Mutual aid must be enforced in code", failures)

    required_approvals = {
        "external_publish",
        "contract_or_legal_commitment",
        "payment_or_investment",
        "personal_or_sensitive_data_transfer",
        "production_deployment",
        "permission_or_role_expansion",
        "constitution_or_policy_change",
    }
    actual_approvals = set(policy["permissions"]["human_approval_required"])
    require(required_approvals <= actual_approvals, "Human approval list is incomplete", failures)

    env_source = environment["policy_source"]
    require(env_source["policy_id"] == policy_id, "Environment policy ID mismatch", failures)
    require(env_source["required_version"] == version, "Environment policy version mismatch", failures)
    require(environment["pilot"]["external_side_effects_enabled"] is False, "Pilot must not enable external side effects", failures)

    for name, app in (("KeBin", kebin), ("DeepSeek", deepseek)):
        binding = app["policy_binding"]
        require(binding["policy_id"] == policy_id, f"{name} policy ID mismatch", failures)
        require(binding["required_version"] == version, f"{name} policy version mismatch", failures)
        require(binding["fail_mode"] == "closed", f"{name} must fail closed", failures)
        require(app["capabilities"]["credentials_available_to_model"] is False, f"{name} model must not receive credentials", failures)
        require(app["session_bootstrap"]["acknowledgement_required"] is True, f"{name} must acknowledge policy", failures)

    require(tests["policy_id"] == policy_id, "Test policy ID mismatch", failures)
    require(tests["policy_version"] == version, "Test policy version mismatch", failures)
    for case in tests["tests"]:
        if case["name"] != "internal_analysis":
            require(case["expected"] in {"deny", "stop"}, f"Unsafe expected result in {case['name']}", failures)

    if failures:
        print("\n".join(f"ERROR: {item}" for item in failures))
        return 1

    print(f"Validated {len(yaml_paths)} YAML files for {policy_id} v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

