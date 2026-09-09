"""Tests for the bounded pytest worker benchmark."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "benchmark_pytest_workers.py"
)
SPEC = importlib.util.spec_from_file_location("benchmark_pytest_workers", MODULE_PATH)
assert SPEC
assert SPEC.loader
benchmark_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_module)


def test_benchmark_uses_only_bounded_worker_counts() -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        commands.append(command)
        return SimpleNamespace(returncode=0)

    report = benchmark_module.benchmark(["tests/unit"], runner=run)
    assert [item["workers"] for item in report["results"]] == [1, 2, 4]
    assert "-n" not in commands[0]
    assert commands[1][-3:] == ["-n", "2", "--dist=worksteal"]
    assert report["automatic_lane_adoption"] is False


def test_benchmark_requires_explicit_selection() -> None:
    with pytest.raises(ValueError, match="explicit"):
        benchmark_module.benchmark([])
