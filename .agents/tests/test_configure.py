"""Configuration generation regression tests."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path
from types import ModuleType

import pytest


def _load_configure(orc: ModuleType) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workflow_configure", orc.AGENTS_DIR / "configure.py"
    )
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schema_v3_configuration_is_complete_toml(orc: ModuleType) -> None:
    module = _load_configure(orc)
    shared = {
        "vendor": "codex",
        "model": 'model "quoted"',
        "effort": "high",
        "provider": "",
    }
    text = module._render_config(
        mode="solo-headless",
        approval_policy="unattended",
        max_iterations=7,
        roles={role: dict(shared) for role in module.ROLES},
        allow_execute=True,
        allow_commit=True,
        allow_merge=True,
        recovery_enabled=True,
    )
    parsed = tomllib.loads(text)
    assert parsed["schema_version"] == 3
    assert parsed["mode"] == "solo-headless"
    assert parsed["approval_policy"] == "unattended"
    assert parsed["max_iterations"] == 7
    assert parsed["unattended"]["allow_execute"] is True
    assert parsed["recovery"]["model"] == "gpt-5.6-sol"
    assert set(parsed["roles"]) == set(module.ROLES)


def test_configurator_only_advertises_supported_vendors(orc: ModuleType) -> None:
    module = _load_configure(orc)
    assert set(module.VENDORS) == {"codex", "agy", "cline", "zai"}


def test_configurator_advertises_six_canonical_modes(orc: ModuleType) -> None:
    module = _load_configure(orc)
    assert tuple(name for name, _description in module.MODES) == (
        "solo",
        "solo-headless",
        "delegate",
        "delegate-headless",
        "delegate-multi",
        "manual",
    )


def test_headless_model_prompts_identify_the_selected_role(
    orc: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_configure(orc)
    labels: list[str] = []

    def fake_pick(label: str, options: tuple[str, ...], *, custom: bool = False) -> str:
        del custom
        labels.append(label)
        return options[0]

    monkeypatch.setattr(module, "_pick", fake_pick)
    module._role_spec("codex", "planner")

    assert labels == [
        "[planner / codex] model",
        "[planner / codex] reasoning effort",
    ]


@pytest.mark.parametrize("mode_index", [0, 2, 5])
def test_non_headless_modes_render_unattended_gate_permissions(
    orc: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode_index: int,
) -> None:
    module = _load_configure(orc)
    output = tmp_path / "run-config.toml"
    selections = iter(
        (
            f"{module.MODES[mode_index][0]} — {module.MODES[mode_index][1]}",
            "unattended — use frozen run preauthorization",
        )
    )
    questions: list[str] = []
    monkeypatch.setattr(module, "RUN_CONFIG", output)
    monkeypatch.setattr(module, "_pick", lambda *_args, **_kwargs: next(selections))
    monkeypatch.setattr(module, "_ask", lambda _prompt: "5")

    def allow(question: str, *, default: bool = False) -> bool:
        del default
        questions.append(question)
        return True

    monkeypatch.setattr(module, "_yes_no", allow)

    assert module.main() == 0
    parsed = tomllib.loads(output.read_text(encoding="utf-8"))
    assert parsed["approval_policy"] == "unattended"
    assert parsed["unattended"] == {
        "allow_execute": True,
        "allow_local_commit": True,
        "allow_local_merge": True,
    }
    assert parsed["recovery"]["enabled"] is False
    assert questions == [
        "Preauthorize plan execution?",
        "Preauthorize local Task commit?",
        "Preauthorize local no-ff merge?",
    ]


def test_repo_configuration_is_portable(orc: ModuleType) -> None:
    text = (orc.AGENTS_DIR / "orchestrator.toml").read_text(encoding="utf-8")
    assert "repo_path" not in text
