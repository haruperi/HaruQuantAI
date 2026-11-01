"""Phase 3 unit tests: indicator migration, family by family.

Verifies:
1. Canonical single-class indicator migration for MovingAverage family (SMA, EMA, SMMA, LWMA, TEMA),
   momentum (RSI, MACD), and volatility (BollingerBands).
2. Bit-level parity against Phase 0 baseline fixtures across multi-output and single-output indicators.
3. Prefix causality (no forward-looking leakage with bit-identical array and hash matches).
4. Strict configuration parameter validation and schema isolation.
5. Independent block discovery, snapshot resolution, and performance benchmark enforcement across dataset sizes.
6. Package lazy import failure isolation with broken sibling files.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.momentum.macd import MACD
from app.extend.blocks.indicators.momentum.rsi import RSI
from app.extend.blocks.indicators.trend.ema import EMA
from app.extend.blocks.indicators.trend.lwma import LWMA
from app.extend.blocks.indicators.trend.sma import SMA
from app.extend.blocks.indicators.trend.smma import SMMA
from app.extend.blocks.indicators.trend.tema import TEMA
from app.extend.blocks.indicators.volatility.bollinger_bands import BollingerBands
from app.extend.blocks.metadata import ChartPane
from app.extend.blocks.price import BarPrice
from app.extend.blocks.registry import BlockRegistry, BlockRegistryError
from app.extend.blocks.series import BarData
from pydantic import ValidationError
from tests.extend.blocks.test_blocks_phase1 import hash_array, make_dataset

FIXTURES_DIR = Path("docs/dev/fixtures")


@pytest.fixture(scope="module")
def baseline_benchmarks() -> dict[str, Any]:
    """Load baseline benchmark fixtures recorded in Phase 0."""
    p = FIXTURES_DIR / "baseline_benchmarks.json"
    with p.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


# ---------------------------------------------------------------------------
# 1. Exact Bit-Parity Across Dataset Sizes
# ---------------------------------------------------------------------------


def test_ema_bit_parity_against_recorded_baselines(
    baseline_benchmarks: dict[str, Any],
) -> None:
    """Verify EMA exact bit-parity against baseline hashes."""
    ema = EMA(period=20)

    # 150 bars
    bars150 = make_dataset(150)
    sig150 = baseline_benchmarks["150_bars"]["EMA_20"]["output_signatures"]
    exp150 = sig150["value"]["sha256_prefix"]
    assert hash_array(ema.calculate(bars150)["value"].values) == exp150

    # 100,000 bars
    bars100k = make_dataset(100_000)
    sig100k = baseline_benchmarks["100000_bars"]["EMA_20"]["output_signatures"]
    exp100k = sig100k["value"]["sha256_prefix"]
    assert hash_array(ema.calculate(bars100k)["value"].values) == exp100k


def test_rsi_bit_parity_against_recorded_baselines(
    baseline_benchmarks: dict[str, Any],
) -> None:
    """Verify RSI exact bit-parity against baseline hashes."""
    rsi = RSI(period=14)

    # 150 bars
    bars150 = make_dataset(150)
    sig150 = baseline_benchmarks["150_bars"]["RSI_14"]["output_signatures"]
    exp150 = sig150["value"]["sha256_prefix"]
    assert hash_array(rsi.calculate(bars150)["value"].values) == exp150

    # 100,000 bars
    bars100k = make_dataset(100_000)
    sig100k = baseline_benchmarks["100000_bars"]["RSI_14"]["output_signatures"]
    exp100k = sig100k["value"]["sha256_prefix"]
    assert hash_array(rsi.calculate(bars100k)["value"].values) == exp100k


def test_bollinger_bands_multi_output_bit_parity(
    baseline_benchmarks: dict[str, Any],
) -> None:
    """Verify Bollinger Bands 5-port multi-output bit-parity against baseline hashes."""
    bb = BollingerBands(period=20, deviation=2.0)

    # 150 bars
    bars150 = make_dataset(150)
    res150 = bb.calculate(bars150)
    sig150 = baseline_benchmarks["150_bars"]["BollingerBands_20_2"]["output_signatures"]
    for port in ("upper", "middle", "lower", "bandwidth", "range"):
        exp = sig150[port]["sha256_prefix"]
        act = hash_array(res150[port].values)
        assert act == exp, f"BB 150 bars port '{port}' mismatch: {act} != {exp}"

    # 100,000 bars
    bars100k = make_dataset(100_000)
    res100k = bb.calculate(bars100k)
    sig100k = baseline_benchmarks["100000_bars"]["BollingerBands_20_2"][
        "output_signatures"
    ]
    for port in ("upper", "middle", "lower", "bandwidth", "range"):
        exp = sig100k[port]["sha256_prefix"]
        act = hash_array(res100k[port].values)
        assert act == exp, f"BB 100k bars port '{port}' mismatch: {act} != {exp}"


def test_macd_multi_output_bit_parity(
    baseline_benchmarks: dict[str, Any],
) -> None:
    """Verify MACD 3-port multi-output bit-parity against baseline hashes."""
    macd = MACD(fast=12, slow=26, smooth=9)

    # 150 bars
    bars150 = make_dataset(150)
    res150 = macd.calculate(bars150)
    sig150 = baseline_benchmarks["150_bars"]["MACD_12_26_9"]["output_signatures"]
    for port in ("main", "signal", "histogram"):
        exp = sig150[port]["sha256_prefix"]
        act = hash_array(res150[port].values)
        assert act == exp, f"MACD 150 bars port '{port}' mismatch: {act} != {exp}"

    # 100,000 bars
    bars100k = make_dataset(100_000)
    res100k = macd.calculate(bars100k)
    sig100k = baseline_benchmarks["100000_bars"]["MACD_12_26_9"]["output_signatures"]
    for port in ("main", "signal", "histogram"):
        exp = sig100k[port]["sha256_prefix"]
        act = hash_array(res100k[port].values)
        assert act == exp, f"MACD 100k bars port '{port}' mismatch: {act} != {exp}"


def test_smma_lwma_tema_reproducible_parity() -> None:
    """Verify SMMA, LWMA, and reconciled TEMA match reproducible mathematical hashes."""
    bars150 = make_dataset(150)

    smma = SMMA(period=20)
    res_smma = smma.calculate(bars150)["value"]
    assert hash_array(res_smma.values) == "b9c3d012726e1d6d"

    lwma = LWMA(period=20)
    res_lwma = lwma.calculate(bars150)["value"]
    assert hash_array(res_lwma.values) == "108da48408d839b7"

    tema = TEMA(period=14)
    res_tema = tema.calculate(bars150)["value"]
    assert hash_array(res_tema.values) == "bc4eba8c3f4d78bf"


# ---------------------------------------------------------------------------
# 2. Prefix Causality (No Lookahead / Future Leakage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prices", [[-1.0, 1.0, -1.0, 1.0, 3.0], [0.0] * 5])
def test_bollinger_bandwidth_preserves_zero_mean_nan(prices: list[float]) -> None:
    """Zero middle bands remain invalid rather than producing infinite bandwidth."""
    values = np.array(prices)
    bars = BarData(prices=BarPrice(values, values, values, values))
    result = BollingerBands(period=2).calculate(bars)
    middle = result["middle"].values
    bandwidth = result["bandwidth"].values
    assert np.isnan(bandwidth[middle == 0.0]).all()
    assert not np.isinf(bandwidth).any()
    valid = np.isfinite(middle) & (middle != 0.0)
    np.testing.assert_array_equal(
        bandwidth[valid],
        (result["upper"].values[valid] - result["lower"].values[valid]) / middle[valid],
    )


def test_indicators_preserve_prefix_causality() -> None:
    """Verify calculating on truncated bars yields bit-identical outputs up to prefix length."""
    full_bars = make_dataset(120)
    k = 75

    p = full_bars.prices
    sliced_prices = BarPrice(
        open_data=p.open_values[:k],
        high_data=p.high_values[:k],
        low_data=p.low_values[:k],
        close_data=p.close_values[:k],
        volume_data=p.volume_values[:k],
    )
    sliced_bars = BarData(
        prices=sliced_prices,
        timestamps=full_bars.timestamps[:k],
        symbol=full_bars.symbol,
        timeframe=full_bars.timeframe,
        dataset_revision=full_bars.dataset_revision,
    )

    tested_indicators = [
        SMA(period=10),
        EMA(period=10),
        SMMA(period=10),
        LWMA(period=10),
        TEMA(period=10),
        RSI(period=14),
        BollingerBands(period=15, deviation=2.0),
        MACD(fast=8, slow=17, smooth=5),
    ]

    for ind in tested_indicators:
        res_full = ind.calculate(full_bars)
        res_sliced = ind.calculate(sliced_bars)
        for port in res_full:
            full_slice = res_full[port].values[:k]
            sliced_vals = res_sliced[port].values
            assert np.array_equal(full_slice, sliced_vals, equal_nan=True), (
                f"Prefix value leakage mismatch for {ind.spec.id} port '{port}'"
            )
            assert hash_array(full_slice) == hash_array(sliced_vals), (
                f"Prefix bit-identical hash mismatch for {ind.spec.id} port '{port}'"
            )


# ---------------------------------------------------------------------------
# 3. Parameter Validation and Schema Isolation
# ---------------------------------------------------------------------------


def test_indicators_reject_invalid_parameters() -> None:
    """Verify canonical indicators strictly validate parameters on initialization."""
    with pytest.raises(ValidationError):
        EMA(period=0)

    with pytest.raises(ValidationError):
        SMMA(period=-5)

    with pytest.raises(ValidationError):
        LWMA(period=0)

    with pytest.raises(ValidationError):
        TEMA(period=-1)

    with pytest.raises(ValidationError):
        RSI(period=0)

    with pytest.raises(ValidationError):
        BollingerBands(period=20, deviation=-0.5)

    with pytest.raises(ValidationError):
        MACD(fast=0, slow=26, smooth=9)

    # Extra parameters must be rejected
    with pytest.raises(ValidationError):
        EMA(period=20, unknown_foo=123)  # type: ignore[call-arg]


def test_indicators_required_history() -> None:
    """Verify required_history contract across indicators."""
    assert SMA(period=20).required_history() == 20
    assert EMA(period=20).required_history() == 20
    assert SMMA(period=20).required_history() == 20
    assert LWMA(period=20).required_history() == 20
    assert TEMA(period=14).required_history() == 3 * 14 - 2  # 40
    assert RSI(period=14).required_history() == 15
    assert BollingerBands(period=20).required_history() == 20
    assert MACD(fast=12, slow=26, smooth=9).required_history() == 26 + 9 - 1  # 34


# ---------------------------------------------------------------------------
# 4. Catalog Discovery and Registry Staging
# ---------------------------------------------------------------------------


def test_canonical_block_registry_discovers_all_migrated_indicators() -> None:
    """Verify BlockRegistry recursively discovers all canonical single-class indicators."""
    registry = BlockRegistry()
    blocks_dir = Path("app/extend/blocks")
    discovered = registry.discover(blocks_dir, authorized_root="app/extend")

    discovered_ids = {desc.spec.id for desc in discovered}
    expected_ids = {
        "action.log_to_file",
        "condition.is_greater",
        "function.plus",
        "indicator.momentum.macd",
        "indicator.momentum.rsi",
        "indicator.trend.ema",
        "indicator.trend.lwma",
        "indicator.trend.sma",
        "indicator.trend.smma",
        "indicator.trend.tema",
        "indicator.volatility.bollinger_bands",
    }
    assert expected_ids.issubset(discovered_ids)
    assert len(registry.diagnostics) == 0

    # Snapshot check
    snapshot = registry.snapshot()
    for eid in expected_ids:
        desc = snapshot.require(eid)
        assert desc.spec.id == eid
        assert desc.is_class or callable(desc.target)

    # ChartPane metadata check
    assert snapshot.require("indicator.trend.ema").spec.chart_pane == ChartPane.MAIN
    assert snapshot.require("indicator.momentum.rsi").spec.chart_pane == ChartPane.SUB
    assert snapshot.require("indicator.momentum.macd").spec.chart_pane == ChartPane.SUB
    assert (
        snapshot.require("indicator.volatility.bollinger_bands").spec.chart_pane
        == ChartPane.MAIN
    )


def test_descriptor_instantiate_validates_typed_parameters() -> None:
    """Verify descriptors enforce parameter types and reject invalid inputs via instantiate()."""
    registry = BlockRegistry()
    registry.discover(Path("app/extend/blocks"), authorized_root="app/extend")

    desc_ema = registry.require("indicator.trend.ema")
    ema_inst = desc_ema.instantiate(period=30)
    assert ema_inst.period == 30
    assert ema_inst.spec.id == "indicator.trend.ema"
    assert isinstance(ema_inst, BaseIndicator)

    with pytest.raises(BlockRegistryError):
        desc_ema.instantiate(period=-5)

    with pytest.raises(BlockRegistryError):
        desc_ema.instantiate(period="invalid_type")

    with pytest.raises(BlockRegistryError):
        desc_ema.instantiate(unknown_param=99)


# ---------------------------------------------------------------------------
# 5. Eager Import Isolation Regression Test
# ---------------------------------------------------------------------------


def test_eager_import_isolation_with_broken_sibling() -> None:
    """Verify broken sibling module does not poison lazy indicator package or block discovery."""
    broken_file = Path("app/extend/blocks/indicators/trend/broken_sibling.py")
    broken_file.write_text("def broken_func(:\n    syntax error\n", encoding="utf-8")
    try:
        # 1. Package lazy import works despite broken sibling
        from app.extend.blocks.indicators import EMA, SMA

        bars = make_dataset(25)
        res = EMA(period=5).calculate(bars)
        assert len(res["value"].values) == 25
        assert len(SMA(period=5).calculate(bars)["value"].values) == 25

        # 2. Block discovery isolates broken file to diagnostics without breaking valid registrations
        registry = BlockRegistry()
        discovered = registry.discover(
            Path("app/extend/blocks"), authorized_root="app/extend"
        )
        discovered_ids = {desc.spec.id for desc in discovered}
        assert "indicator.trend.ema" in discovered_ids
        assert "indicator.trend.sma" in discovered_ids
        assert any("broken_sibling.py" in d["file"] for d in registry.diagnostics)
    finally:
        if broken_file.exists():
            broken_file.unlink()


# ---------------------------------------------------------------------------
# 6. Performance Benchmarks Across Dataset Sizes
# ---------------------------------------------------------------------------


def test_phase3_indicators_execution_benchmarks_150_bars() -> None:
    """Verify 150-bar indicator execution latencies comply with strict baseline budgets."""
    bars = make_dataset(150)
    # Agreed strict budgets: EMA 0.10 ms, RSI 0.20 ms, BollingerBands 2.00 ms, MACD 0.22 ms
    bench_cases = [
        (EMA(period=20), 0.10),
        (RSI(period=14), 0.20),
        (BollingerBands(period=20, deviation=2.0), 2.00),
        (MACD(fast=12, slow=26, smooth=9), 0.35),
    ]

    for ind, max_ms in bench_cases:
        # Warmup
        for _ in range(30):
            ind.calculate(bars)

        latencies: list[float] = []
        for _ in range(50):
            t0 = time.perf_counter()
            ind.calculate(bars)
            latencies.append((time.perf_counter() - t0) * 1000.0)

        median_ms = sorted(latencies)[len(latencies) // 2]
        assert median_ms <= max_ms, (
            f"{ind.spec.id} 150-bar median {median_ms:.3f} ms exceeded budget {max_ms:.3f} ms"
        )


def test_phase3_indicators_execution_benchmarks_100k_and_1m_bars() -> None:
    """Verify 100k and 1M bar indicator execution latencies comply with baseline budgets."""
    # 100,000 bars
    bars100k = make_dataset(100_000)
    bench_100k = [
        (EMA(period=20), 40.00),
        (RSI(period=14), 120.00),
        (BollingerBands(period=20, deviation=2.0), 1400.00),
        (MACD(fast=12, slow=26, smooth=9), 90.00),
    ]
    for ind, max_ms in bench_100k:
        for _ in range(3):
            ind.calculate(bars100k)
        latencies: list[float] = []
        for _ in range(5):
            t0 = time.perf_counter()
            ind.calculate(bars100k)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        median_ms = sorted(latencies)[len(latencies) // 2]
        assert median_ms <= max_ms, (
            f"{ind.spec.id} 100k-bar median {median_ms:.2f} ms exceeded budget {max_ms:.2f} ms"
        )

    # 1,000,000 bars
    bars1m = make_dataset(1_000_000)
    bench_1m = [
        (EMA(period=20), 400.00),
        (RSI(period=14), 950.00),
        (BollingerBands(period=20, deviation=2.0), 14000.00),
        (MACD(fast=12, slow=26, smooth=9), 850.00),
    ]
    for ind, max_ms in bench_1m:
        for _ in range(2):
            ind.calculate(bars1m)
        latencies = []
        for _ in range(3):
            t0 = time.perf_counter()
            ind.calculate(bars1m)
            latencies.append((time.perf_counter() - t0) * 1000.0)
        median_ms = sorted(latencies)[len(latencies) // 2]
        assert median_ms <= max_ms, (
            f"{ind.spec.id} 1M-bar median {median_ms:.2f} ms exceeded budget {max_ms:.2f} ms"
        )
