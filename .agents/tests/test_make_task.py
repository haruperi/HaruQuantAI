"""Task TOML encoding regression tests."""

from __future__ import annotations

import importlib.util
import tomllib
from types import ModuleType


def test_task_spec_round_trips_special_characters(orc: ModuleType) -> None:
    spec = importlib.util.spec_from_file_location(
        "workflow_make_task", orc.AGENTS_DIR / "make_task.py"
    )
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entry = {
        "is_feature": False,
        "partial": False,
        "title": 'Quoted "task" C:\\temp\nUnicode Ω',
        "items": [{"text": "tab\tand apostrophe's", "fr_id": None}],
    }
    text, _, _ = module._build_task_spec("1.01", entry, "C:\\docs\ntracker.md")
    parsed = tomllib.loads(text)
    assert parsed["implementation_file"] == "C:\\docs\ntracker.md"


def test_entry_sort_key_handles_mixed_entry_types(orc: ModuleType) -> None:
    spec = importlib.util.spec_from_file_location(
        "workflow_make_task", orc.AGENTS_DIR / "make_task.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entries = ["10.1", "P.002", "3.10", "1.1", "0.1", "3.5", "P.001", "P.010"]
    sorted_entries = sorted(entries, key=module._entry_sort_key)
    assert sorted_entries == [
        "P.001",
        "P.002",
        "P.010",
        "0.1",
        "1.1",
        "3.5",
        "3.10",
        "10.1",
    ]
