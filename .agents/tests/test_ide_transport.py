"""IDE-native role transport and delegate-handle regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ide_transport import _bind_delegate_handle, expected_delegate_handle
from workflow_protocol import OrchestratorError


def _identity(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = {"runs_dir": tmp_path / "runs"}
    state = {"run_id": "run-1", "iteration": 1}
    return cfg, state


def test_delegate_handle_is_required_and_reused_per_role(tmp_path: Path) -> None:
    cfg, state = _identity(tmp_path)

    with pytest.raises(OrchestratorError, match="requires --app-agent-id"):
        _bind_delegate_handle(cfg, state, "PLANNER", None)

    assert _bind_delegate_handle(cfg, state, "PLANNER", "agent-planner") == (
        "agent-planner"
    )
    state["iteration"] = 2
    assert _bind_delegate_handle(cfg, state, "PLANNER", "agent-planner") == (
        "agent-planner"
    )
    assert expected_delegate_handle(cfg, state, "PLANNER") == "agent-planner"


def test_delegate_handles_cannot_change_or_cross_roles(tmp_path: Path) -> None:
    cfg, state = _identity(tmp_path)
    _bind_delegate_handle(cfg, state, "PLANNER", "agent-planner")

    with pytest.raises(OrchestratorError, match="handle changed"):
        _bind_delegate_handle(cfg, state, "PLANNER", "agent-other")
    with pytest.raises(OrchestratorError, match="already bound to PLANNER"):
        _bind_delegate_handle(cfg, state, "EXECUTOR", "agent-planner")
