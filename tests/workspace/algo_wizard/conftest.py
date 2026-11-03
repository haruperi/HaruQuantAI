"""Isolated host persistence for HSL workspace integration tests.

Description:
    Verify declared strategy behavior and explicit rejection of unavailable inputs.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Regression evidence for shared strategy execution.
Key Capabilities:
    - FR-hsl-regression-evidence: Assert observable results and failure boundaries.
Python API Usage:
    Run this module through pytest.
CLI Usage:
    uv run pytest tests/workspace/algo_wizard --no-cov
"""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_hsl_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test gets a fresh durable store; never use the owner's files."""
    monkeypatch.setenv("HARU_STRATEGY_STORAGE_DIR", str(tmp_path / "hsl"))
