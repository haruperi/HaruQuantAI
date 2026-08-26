"""Transport-mode regression tests."""

from __future__ import annotations

from types import ModuleType

import pytest


@pytest.mark.parametrize("mode", ["solo", "delegate", "manual", "UNCONFIGURED"])
def test_cli_runner_rejects_non_process_modes(orc: ModuleType, mode: str) -> None:
    with pytest.raises(orc.OrchestratorError):
        orc._require_cli_mode({"mode": mode})


def test_cli_runner_accepts_multi_delegate(orc: ModuleType) -> None:
    orc._require_cli_mode({"mode": "multi-delegate"})
