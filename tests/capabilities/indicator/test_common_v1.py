"""Unit tests for indicator common v1 contracts.

Traces to: P3-T02, Gate G3
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import app.capabilities.indicator.common.v1 as common_v1
import pandas as pd
from app.capabilities.indicator.common.v1 import (
    IndicatorConfigV1,
    IndicatorResultV1,
    MarketDatasetV1,
    OHLCVRecordV1,
)

from tests.removability.harness import run_in_fresh_process


@dataclass(frozen=True, slots=True)
class _FakeOHLCVRecord:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    available_at: datetime


@dataclass(frozen=True, slots=True)
class _FakeMarketDataset:
    symbol: str
    timeframe: str
    records: Sequence[OHLCVRecordV1]


@dataclass(frozen=True, slots=True)
class _FakeIndicatorConfig:
    indicator_id: str
    parameters: tuple[tuple[str, Any], ...]
    source: str
    formula_version: str
    output_mode: str
    column_conflict_policy: str


@dataclass(frozen=True, slots=True)
class _FakeIndicatorResult:
    data: MarketDatasetV1
    config: IndicatorConfigV1
    indicator_version: str
    output_columns: tuple[str, ...]
    output_values: pd.DataFrame
    available_at: pd.Series
    computed_from_start: pd.Series
    computed_from_end: pd.Series
    unavailable_reason: pd.Series


def test_common_module_has_exact_exports() -> None:
    """Verify exact public exports for common v1 contracts."""
    assert common_v1.__all__ == (
        "IndicatorConfigV1",
        "IndicatorResultV1",
        "MarketDatasetV1",
        "OHLCVRecordV1",
    )


def test_common_module_imports_no_business_domain() -> None:
    """Verify common v1 contract does not import any business services or agentic packages."""
    script = """
import sys
import app.capabilities.indicator.common.v1 as common_v1
assert common_v1 is not None
for mod_name in sys.modules:
    assert not mod_name.startswith('app.services'), f'Forbidden business domain imported: {mod_name}'
    assert not mod_name.startswith('app.agentic'), f'Forbidden agentic domain imported: {mod_name}'
"""
    repo_root = Path(__file__).resolve().parents[3]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_fixture_exposes_required_attributes() -> None:
    """Verify test fixtures satisfy runtime protocol checks and expose attributes."""
    now = datetime.now(UTC)
    rec = _FakeOHLCVRecord(
        timestamp=now,
        open=Decimal("100.0"),
        high=Decimal("105.0"),
        low=Decimal("95.0"),
        close=Decimal("102.0"),
        volume=Decimal("1000.0"),
        available_at=now,
    )
    assert isinstance(rec, OHLCVRecordV1)

    ds = _FakeMarketDataset(symbol="EURUSD", timeframe="1h", records=(rec,))
    assert isinstance(ds, MarketDatasetV1)

    cfg = _FakeIndicatorConfig(
        indicator_id="rsi",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
    )
    assert isinstance(cfg, IndicatorConfigV1)

    res = _FakeIndicatorResult(
        data=ds,
        config=cfg,
        indicator_version="1.0.0",
        output_columns=("rsi_14",),
        output_values=pd.DataFrame({"rsi_14": [50.0]}),
        available_at=pd.Series([now]),
        computed_from_start=pd.Series([now]),
        computed_from_end=pd.Series([now]),
        unavailable_reason=pd.Series([None]),
    )
    assert isinstance(res, IndicatorResultV1)
