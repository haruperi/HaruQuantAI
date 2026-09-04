"""Runtime-policy modes and unattended authorization regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_policy import RuntimePolicyError, load_runtime_policy
from workflow_runtime import _ensure_runtime_policy_unchanged


def _write_policy(
    path: Path,
    *,
    mode: str = "solo",
    approval: str = "interactive",
    recovery_enabled: bool | None = None,
) -> None:
    permissions = approval == "unattended"
    recovery = permissions if recovery_enabled is None else recovery_enabled
    path.write_text(
        f"""schema_version = 2
mode = {mode!r}
approval_policy = {approval!r}
max_iterations = 4

[unattended]
allow_execute = {str(permissions).lower()}
allow_local_commit = {str(permissions).lower()}
allow_local_merge = {str(permissions).lower()}

[recovery]
enabled = {str(recovery).lower()}
max_escalations = {1 if recovery else 0}
additional_iterations = {1 if recovery else 0}
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"

[roles.planner]
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"

[roles.executor]
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"

[roles.reviewer]
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"
""",
        encoding="utf-8",
    )


def test_v2_policy_drives_transport_gates_and_recovery(tmp_path: Path) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path, approval="unattended")
    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=9)

    assert policy.max_iterations == 4
    assert policy.can_preauthorize_execute()
    assert policy.can_preauthorize_commit()
    assert policy.recovery.enabled
    assert policy.effective_mode == "solo-headless"
    assert policy.is_headless
    command = policy.role_config("planner")["command"]
    assert command[command.index("--mode") + 1] == "solo"


def test_solo_requires_one_identical_role_identity(tmp_path: Path) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path)
    text = path.read_text(encoding="utf-8").replace(
        '[roles.executor]\nvendor = "codex"\nmodel = "gpt-5.6-sol"',
        '[roles.executor]\nvendor = "codex"\nmodel = "gpt-5.6-terra"',
    )
    path.write_text(text, encoding="utf-8")

    with pytest.raises(RuntimePolicyError, match="one identical"):
        load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)


@pytest.mark.parametrize("mode", ["solo", "delegate", "multi-delegate", "manual"])
def test_schema_v2_all_modes_allow_unattended_gate_policy(
    tmp_path: Path, mode: str
) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(
        path,
        mode=mode,
        approval="unattended",
        recovery_enabled=False,
    )

    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)

    assert policy.can_preauthorize_execute()
    assert policy.can_preauthorize_commit()
    assert not policy.recovery.enabled


@pytest.mark.parametrize("mode", ["solo", "delegate", "manual"])
def test_schema_v3_interactive_modes_need_no_cli_roles(
    tmp_path: Path, mode: str
) -> None:
    path = tmp_path / "run-config.toml"
    path.write_text(
        f"""schema_version = 3
mode = "{mode}"
approval_policy = "interactive"
max_iterations = 4

[unattended]
allow_execute = false
allow_local_commit = false
allow_local_merge = false

[recovery]
enabled = false
max_escalations = 0
additional_iterations = 0
""",
        encoding="utf-8",
    )

    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)

    assert policy.effective_mode == mode
    assert policy.roles == {}
    assert policy.is_ide is (mode != "manual")
    with pytest.raises(RuntimePolicyError, match="no process-runner"):
        policy.role_config("planner")


@pytest.mark.parametrize("mode", ["solo", "delegate", "manual"])
def test_schema_v3_non_headless_modes_allow_unattended_gate_policy(
    tmp_path: Path, mode: str
) -> None:
    path = tmp_path / "run-config.toml"
    path.write_text(
        f"""schema_version = 3
mode = "{mode}"
approval_policy = "unattended"
max_iterations = 4

[unattended]
allow_execute = true
allow_local_commit = true
allow_local_merge = true

[recovery]
enabled = false
max_escalations = 0
additional_iterations = 0
""",
        encoding="utf-8",
    )

    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)

    assert policy.effective_mode == mode
    assert policy.can_preauthorize_execute()
    assert policy.can_preauthorize_commit()


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("solo", "solo-headless"),
        ("delegate", "delegate-headless"),
        ("multi-delegate", "delegate-multi"),
        ("manual", "manual"),
    ],
)
def test_schema_v2_mode_names_map_without_rewriting_policy_identity(
    tmp_path: Path, mode: str, expected: str
) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path, mode=mode)

    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)

    assert policy.mode == mode
    assert policy.effective_mode == expected
    assert policy.schema_version == 2


def test_schema_v3_headless_policy_uses_canonical_session_mode(tmp_path: Path) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path)
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace("schema_version = 2", "schema_version = 3")
        .replace("mode = 'solo'", "mode = 'solo-headless'"),
        encoding="utf-8",
    )

    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)

    assert policy.mode == "solo-headless"
    assert policy.effective_mode == "solo-headless"
    command = policy.role_config("planner")["command"]
    assert command[command.index("--mode") + 1] == "solo-headless"


def test_quick_fix_requires_interactive_policy(tmp_path: Path) -> None:
    path = tmp_path / "run-config.toml"
    path.write_text(
        """schema_version = 3
mode = "quick-fix"
approval_policy = "interactive"
max_iterations = 3

[unattended]
allow_execute = false
allow_local_commit = false
allow_local_merge = false

[recovery]
enabled = false
max_escalations = 0
additional_iterations = 0
vendor = "codex"
model = "gpt-5.6-sol"
effort = "high"
""",
        encoding="utf-8",
    )
    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)
    assert policy.effective_mode == "quick-fix"
    assert policy.is_ide
    assert not policy.can_preauthorize_execute()

    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'approval_policy = "interactive"', 'approval_policy = "unattended"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimePolicyError, match="requires interactive"):
        load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)


def test_schema_v2_never_falls_back_to_tracked_role_configs(tmp_path: Path) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path)
    text = path.read_text(encoding="utf-8").replace(
        '[roles.planner]\nvendor = "codex"',
        '[roles.planner]\nvendor = "unsupported"',
    )
    path.write_text(text, encoding="utf-8")

    with pytest.raises(RuntimePolicyError, match="unsupported vendor"):
        load_runtime_policy(
            path,
            legacy_roles={"planner": {"command": ["should-not-run"]}},
            default_max_iterations=5,
        )


def test_frozen_runtime_policy_drift_fails_closed(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    tmp_path: Path,
) -> None:
    path = tmp_path / "run-config.toml"
    _write_policy(path)
    policy = load_runtime_policy(path, legacy_roles={}, default_max_iterations=5)
    cfg.update(
        {
            "runtime_policy_path": path,
            "runtime_policy": policy,
            "legacy_roles": {},
            "max_iterations": policy.max_iterations,
        }
    )
    state["runtime_policy_fingerprint"] = policy.fingerprint
    state["scope_fingerprint"] = orc.scope_fingerprint(state["task"])
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "max_iterations = 4", "max_iterations = 5"
        ),
        encoding="utf-8",
    )

    with pytest.raises(orc.OrchestratorError, match="changed after run activation"):
        _ensure_runtime_policy_unchanged(cfg, state)


def test_legacy_policy_can_resume_but_cannot_start_a_new_run(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
    tmp_path: Path,
) -> None:
    path = tmp_path / "run-config.toml"
    path.write_text('mode = "solo"\n', encoding="utf-8")
    legacy_role = {
        "brand": "codex",
        "model": "legacy",
        "effort": "high",
        "command": ["codex", "{prompt}"],
    }
    policy = load_runtime_policy(
        path,
        legacy_roles=dict.fromkeys(("planner", "executor", "reviewer"), legacy_role),
        default_max_iterations=5,
    )
    cfg["runtime_policy"] = policy

    with pytest.raises(orc.OrchestratorError, match="continuation-only"):
        orc.prepare_task_run(cfg, state["task"])
