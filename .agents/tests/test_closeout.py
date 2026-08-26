"""Close-out evidence regression tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any


def test_closeout_archive_preserves_active_evidence(
    orc: ModuleType,
    cfg: dict[str, Any],
    state: dict[str, Any],
) -> None:
    cfg["journals"]["planner"].write_text("plan", encoding="utf-8")
    cfg["next_agent"].write_text("prompt", encoding="utf-8")
    state["approved_write_paths"] = ["demo.txt"]
    archive: Path = orc._archive_closeout_evidence(cfg, state)
    assert (archive / "planner.md").read_text(encoding="utf-8") == "plan"
    assert (archive / "next-agent.md").read_text(encoding="utf-8") == "prompt"
    assert cfg["journals"]["planner"].read_text(encoding="utf-8") == "plan"
