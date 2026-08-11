"""Component verification for the real PyArrow tick persistence boundary."""

from pathlib import Path

import pytest

from tests.data.unit.test_ticks import (
    component_compiled_four_tick_path_matches_decimal_fallback_exactly,
    component_compiled_generated_path_matches_decimal_fallback_exactly,
    component_parquet_uses_bounded_compiled_columns_without_materializing_dataset,
)


def test_parquet_uses_bounded_compiled_columns_without_materializing_dataset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the bounded compiled-column path using real Parquet I/O."""
    component_parquet_uses_bounded_compiled_columns_without_materializing_dataset(
        monkeypatch,
        tmp_path,
    )


@pytest.mark.parametrize("spread_model", ["native_spread", "fixed_spread"])
def test_compiled_generated_path_matches_decimal_fallback_exactly(
    monkeypatch: pytest.MonkeyPatch,
    spread_model: str,
) -> None:
    """Compare compiled generated ticks with the exact Decimal fallback."""
    component_compiled_generated_path_matches_decimal_fallback_exactly(
        monkeypatch,
        spread_model,
    )


def test_compiled_four_tick_path_matches_decimal_fallback_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compare compiled four-tick paths with the exact Decimal fallback."""
    component_compiled_four_tick_path_matches_decimal_fallback_exactly(monkeypatch)
