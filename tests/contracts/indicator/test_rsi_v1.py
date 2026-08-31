"""Unit tests for RSI v1 capability specification contract.

Traces to: P3-T03, Gate G3
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import app.contracts.indicator.rsi.v1 as rsi_v1
import pytest
from app.contracts.indicator.common.v1 import (
    IndicatorConfigV1,
    IndicatorResultV1,
    MarketDatasetV1,
)
from app.contracts.indicator.rsi.v1 import (
    CAPABILITY_ID,
    RsiCapabilityV1,
)

from tests.removability.harness import run_in_fresh_process


def test_rsi_contract_exports_are_exact() -> None:
    """Verify exact public exports for RSI v1 contract."""
    assert rsi_v1.__all__ == (
        "CAPABILITY_ID",
        "RsiCapabilityV1",
        "RsiFunctionV1",
    )
    assert CAPABILITY_ID == "indicator.rsi.v1"


def test_rsi_record_is_frozen() -> None:
    """Verify RsiCapabilityV1 is frozen and cannot be mutated."""

    def _dummy_calc(
        data: MarketDatasetV1,
        *,
        period: int,
        source: str = "close",
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1:
        raise NotImplementedError

    cap = RsiCapabilityV1(calculate=_dummy_calc)
    with pytest.raises(FrozenInstanceError):
        cap.calculate = _dummy_calc  # type: ignore[misc]


def test_rsi_callable_preserves_keywords() -> None:
    """Verify RsiCapabilityV1 callable receives exact keyword arguments."""
    recorded_kwargs: dict[str, Any] = {}

    def _spy_calc(
        data: MarketDatasetV1,
        *,
        period: int,
        source: str = "close",
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1:
        recorded_kwargs["data"] = data
        recorded_kwargs["period"] = period
        recorded_kwargs["source"] = source
        recorded_kwargs["config"] = config
        return None  # type: ignore[return-value]

    cap = RsiCapabilityV1(calculate=_spy_calc)
    fake_dataset: Any = "mock_data"
    cap.calculate(fake_dataset, period=14, source="close", config=None)

    assert recorded_kwargs["data"] == "mock_data"
    assert recorded_kwargs["period"] == 14
    assert recorded_kwargs["source"] == "close"
    assert recorded_kwargs["config"] is None


def test_rsi_contract_imports_without_services() -> None:
    """Verify RSI capability contract imports without pulling in any business services."""
    script = """
import sys
import app.contracts.indicator.rsi.v1 as rsi_v1
assert rsi_v1 is not None
for mod_name in sys.modules:
    assert not mod_name.startswith('app.services'), f'Forbidden business domain imported: {mod_name}'
    assert not mod_name.startswith('app.agentic'), f'Forbidden agentic domain imported: {mod_name}'
"""
    repo_root = Path(__file__).resolve().parents[3]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr
