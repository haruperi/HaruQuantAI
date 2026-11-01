"""Phase 1 unit tests for shared contracts, independent registry, and vertical slice."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, override

import numpy as np
import pytest
from app.include.blocks.actions.log_to_file import LogToFileAction
from app.include.blocks.base import BaseBlock
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.functions.plus import plus
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.trend.sma import SMA
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.money_management.base import BasePositionSizer
from app.include.blocks.price import BarPrice
from app.include.blocks.registry import (
    BlockRegistry,
    BlockRegistryError,
    block_registry,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.metrics.base import BaseMetric
from pydantic import Field, ValidationError


def hash_array(arr: np.ndarray[Any, Any]) -> str:
    """Compute deterministic nan-safe SHA256 prefix matching Phase 0 protocol."""
    clean = np.nan_to_num(arr, nan=-999999.99, posinf=1e9, neginf=-1e9)
    return hashlib.sha256(clean.tobytes()).hexdigest()[:16]


def make_dataset(n_bars: int) -> BarData:
    """Generate synthetic dataset matching Phase 0 seed and parameters."""
    rng = np.random.default_rng(42)
    returns = rng.normal(loc=0.0001, scale=0.01, size=n_bars)
    close = 100.0 * np.exp(np.cumsum(returns))
    high = close * (1.0 + rng.uniform(0.0, 0.005, size=n_bars))
    low = close * (1.0 - rng.uniform(0.0, 0.005, size=n_bars))
    open_p = (high + low) / 2.0
    volume = rng.uniform(100, 10000, size=n_bars)
    timestamps = np.arange(
        1700000000000, 1700000000000 + n_bars * 3600000, 3600000, dtype=np.int64
    )

    prices = BarPrice(
        open_data=open_p,
        high_data=high,
        low_data=low,
        close_data=close,
        volume_data=volume,
    )
    return BarData(
        prices=prices,
        timestamps=timestamps,
        symbol="EURUSD",
        timeframe="H1",
        dataset_revision="test-v1",
    )


@pytest.fixture
def sample_bars_150() -> BarData:
    return make_dataset(150)


# ---------------------------------------------------------------------------
# 1. Contract & Schema Tests
# ---------------------------------------------------------------------------


def test_block_spec_initialization() -> None:
    spec = BlockSpec(
        id="test.sample",
        version="1.0.0",
        name="Sample",
        description="Sample spec",
        category="testing",
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("in", PortType.SERIES),),
        outputs=(OutputPort("out", PortType.SERIES),),
    )
    assert spec.id == "test.sample"
    assert spec.execution_kind == ExecutionKind.EXPRESSION
    assert spec.is_generation_eligible is True
    assert spec.is_deterministic is True


def test_base_block_pydantic_schema_excludes_metadata_and_private_state() -> None:
    schema = SMA.get_parameter_schema()
    assert "properties" in schema
    assert "period" in schema["properties"]
    assert "spec" not in schema["properties"]
    assert not any(k.startswith("_") for k in schema["properties"])
    assert schema["properties"]["period"]["default"] == 20
    assert schema["properties"]["period"]["minimum"] == 1


def test_base_block_forbids_extra_parameters_and_freezes_config() -> None:
    sma = SMA(period=25)
    assert sma.period == 25

    with pytest.raises(ValidationError):
        sma.period = 30

    with pytest.raises(ValidationError) as exc_info:
        SMA(period=20, unknown_param=123)  # type: ignore[call-arg]
    assert "extra_forbidden" in str(exc_info.value)


def test_base_block_validates_default_values() -> None:
    """Verify validate_default=True prevents defining models with invalid defaults."""
    with pytest.raises(ValidationError):

        class InvalidDefaultBlock(BaseBlock):
            spec = BlockSpec(id="test.invalid", name="Invalid")
            bad_param: int = Field(default=-10, ge=0)

        InvalidDefaultBlock()


def test_sma_parameter_validation_rejects_non_positive_period() -> None:
    with pytest.raises(ValidationError) as exc_0:
        SMA(period=0)
    assert "greater_than_equal" in str(exc_0.value)

    with pytest.raises(ValidationError) as exc_neg:
        SMA(period=-5)
    assert "greater_than_equal" in str(exc_neg.value)


def test_sma_metadata_supports_incremental_is_false() -> None:
    """Verify incremental capability is set to False until streaming is implemented."""
    assert SMA.spec.supports_incremental is False
    sma = SMA(period=20)
    assert sma.supports_incremental() is False


# ---------------------------------------------------------------------------
# 2. BarData Zero-Copy and Strict Alignment
# ---------------------------------------------------------------------------


def test_bardata_zero_copy_and_immutability(sample_bars_150: BarData) -> None:
    # 1. Zero-copy: memory buffer is directly shared with BarPrice
    assert np.shares_memory(sample_bars_150.close, sample_bars_150.prices._close)
    assert np.shares_memory(sample_bars_150.open, sample_bars_150.prices._open)
    assert np.shares_memory(sample_bars_150.high, sample_bars_150.prices._high)
    assert np.shares_memory(sample_bars_150.low, sample_bars_150.prices._low)
    assert np.shares_memory(sample_bars_150.volume, sample_bars_150.prices._volume)

    # 2. Immutability: writeable flag is False
    with pytest.raises(ValueError):
        sample_bars_150.close[0] = 999.0

    with pytest.raises(ValueError):
        sample_bars_150.timestamps[0] = 999


def test_bardata_rejects_misaligned_timestamps(sample_bars_150: BarData) -> None:
    # Mismatched timestamp length must be rejected
    mismatched_ts = np.array([1, 2, 3], dtype=np.int64)
    with pytest.raises(ValueError) as exc_info:
        BarData(
            prices=sample_bars_150.prices,
            timestamps=mismatched_ts,
        )
    assert "does not match bar count" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. Independent Registry & Transactional Staging
# ---------------------------------------------------------------------------


def test_registry_registration_and_callable_schema_separation() -> None:
    registry = BlockRegistry()
    desc_sma = registry.register_block(SMA, source_file="sma.py")
    assert desc_sma.spec.id == "indicator.trend.sma"
    assert "period" in desc_sma.parameter_schema["properties"]

    # Callable block registration: verify runtime input ports are excluded from configuration
    desc_plus = registry.register_block(plus, source_file="plus.py")
    assert desc_plus.spec.id == "function.plus"
    assert desc_plus.is_class is False
    # 'shift' is configurable parameter with declared integer type
    assert "shift" in desc_plus.parameter_schema["properties"]
    assert desc_plus.parameter_schema["properties"]["shift"]["type"] == "integer"
    assert desc_plus.parameter_schema["properties"]["shift"]["default"] == 0
    # 'left' and 'right' are input ports, NOT configuration parameters
    assert "left" not in desc_plus.parameter_schema["properties"]
    assert "right" not in desc_plus.parameter_schema["properties"]


def test_callable_descriptor_instantiate_validates_parameters() -> None:
    from app.include.blocks.base import block

    registry = BlockRegistry()
    desc = registry.register_block(plus)

    # Unknown parameter must be rejected
    with pytest.raises(BlockRegistryError) as exc_info:
        desc.instantiate(unknown_kwarg=42)
    assert "Unknown configuration parameter" in str(exc_info.value)

    # Type mismatch must be rejected (shift="invalid" or string "1")
    with pytest.raises(BlockRegistryError) as exc_str:
        desc.instantiate(shift="invalid")
    assert "Invalid configuration parameter" in str(exc_str.value)

    with pytest.raises(BlockRegistryError) as exc_num_str:
        desc.instantiate(shift="1")
    assert "Invalid configuration parameter" in str(exc_num_str.value)

    # Valid parameter binds cleanly
    configured_plus = desc.instantiate(shift=1)
    s1 = IndicatorSeries([10.0, 20.0])
    s2 = IndicatorSeries([5.0, 15.0])
    # shift=1: 10.0 + 5.0 = 15.0
    assert configured_plus(s1, s2) == 15.0

    # Callable with required configuration parameter (no default)
    req_spec = BlockSpec(
        id="function.test_req",
        name="Test Req",
        inputs=(InputPort("x", PortType.NUMBER),),
        outputs=(OutputPort("out", PortType.NUMBER),),
    )

    @block(req_spec)
    def dummy_func(x: float, threshold: float) -> float:
        return x + threshold

    desc_req = registry.register_block(dummy_func)
    # Missing required parameter fails validation
    with pytest.raises(BlockRegistryError):
        desc_req.instantiate()

    # Invalid type for required parameter fails validation
    with pytest.raises(BlockRegistryError):
        desc_req.instantiate(threshold="bad")

    # Providing required parameter succeeds
    configured_dummy = desc_req.instantiate(threshold=5.0)
    assert configured_dummy(10.0) == 15.0


def test_catalog_snapshot_is_deeply_immutable() -> None:
    registry = BlockRegistry()
    registry.register_block(SMA)
    snapshot = registry.snapshot()

    # 1. snapshot.blocks dictionary cannot be mutated
    with pytest.raises(TypeError):
        snapshot.blocks["new_entry"] = registry.get("indicator.trend.sma")  # type: ignore[index]

    with pytest.raises(AttributeError):
        snapshot.blocks.clear()  # type: ignore[attr-defined]

    # 2. Nested parameter schema cannot be mutated
    desc = snapshot.require("indicator.trend.sma")
    with pytest.raises(TypeError):
        desc.parameter_schema["properties"]["period"] = {}

    # 3. BlockSpec metadata and nested parameter_search_space cannot be mutated
    assert isinstance(desc.spec.parameter_search_space, Mapping)
    with pytest.raises(TypeError):
        desc.spec.parameter_search_space["period"] = [1, 2]  # type: ignore[index]

    with pytest.raises(TypeError):
        desc.spec.parameter_search_space["new_key"] = "forbidden"  # type: ignore[index]

    with pytest.raises(AttributeError):
        desc.spec.parameter_search_space["period"].append(999)

    with pytest.raises(AttributeError):
        desc.spec.parameter_search_space.clear()  # type: ignore[attr-defined]

    # 4. Class descriptor instantiate validates parameters
    with pytest.raises(BlockRegistryError):
        desc.instantiate(period="invalid")

    with pytest.raises(BlockRegistryError):
        desc.instantiate(period=-5)

    with pytest.raises(BlockRegistryError):
        desc.instantiate(unknown_param=100)

    valid_sma = desc.instantiate(period=30)
    assert isinstance(valid_sma, SMA)
    assert valid_sma.period == 30


def test_registry_staging_is_fully_atomic() -> None:
    registry = BlockRegistry()
    registry.register_block(SMA, source_file="sma.py")
    initial_rev = registry.revision

    # Begin staging
    registry.begin_staging()

    # During staging: unregister live source 'sma.py' and add 'plus.py'
    registry.unregister_source("sma.py")
    registry.register_block(plus, source_file="plus.py")

    # Staging view reflects changes
    assert registry.get("indicator.trend.sma") is None
    assert registry.get("function.plus") is not None

    # ROLLBACK: live catalog must be completely restored!
    registry.rollback_staging()

    assert registry.get("indicator.trend.sma") is not None
    assert registry.get("function.plus") is None
    assert registry.revision == initial_rev
    # Source ownership restored
    assert registry._by_source.get("sma.py") == ["indicator.trend.sma"]
    assert "plus.py" not in registry._by_source

    # COMMIT: changes become permanent
    registry.begin_staging()
    registry.unregister_source("sma.py")
    registry.register_block(plus, source_file="plus.py")
    registry.commit_staging()

    assert registry.get("indicator.trend.sma") is None
    assert registry.get("function.plus") is not None
    assert registry.revision != initial_rev
    assert "sma.py" not in registry._by_source
    assert registry._by_source.get("plus.py") == ["function.plus"]


def test_registry_rejects_duplicate_block_id_with_different_target() -> None:
    registry = BlockRegistry()
    registry.register_block(SMA)

    class DuplicateSMA(BaseIndicator):
        spec = BlockSpec(id="indicator.trend.sma", name="Duplicate")

        @override
        def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
            return {}

    with pytest.raises(BlockRegistryError) as exc_info:
        registry.register_block(DuplicateSMA)
    assert "Duplicate block ID" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Vertical Slice: SMA Exact Bit-Parity & Agreed Benchmark Budgets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n_bars", "expected_hash", "max_median_ms"),
    [
        (150, "c92738bf6b3b3222", 0.07),
        (100_000, "86191cfe5da2832f", 1.90),
        (1_000_000, "f482e78146e14577", 20.00),
    ],
)
def test_sma_full_output_bit_parity_and_benchmark(
    n_bars: int, expected_hash: str, max_median_ms: float
) -> None:
    """Verify SMA full-output hash bit-parity and execution budget across all 3 datasets."""
    bars = make_dataset(n_bars)
    sma = SMA(period=20)

    # 1. Bit-parity test
    res = sma.calculate(bars)
    assert "value" in res
    series = res["value"]
    assert len(series) == n_bars

    actual_hash = hash_array(series.values)
    assert actual_hash == expected_hash, (
        f"Bit-parity hash mismatch for {n_bars:,} bars: {actual_hash} != {expected_hash}"
    )

    # 2. Performance benchmark with warmup and timing protocol
    for _ in range(3):
        sma.calculate(bars)

    latencies: list[float] = []
    iterations = 20 if n_bars <= 100_000 else 5
    for _ in range(iterations):
        t0 = time.perf_counter()
        sma.calculate(bars)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    median_ms = sorted(latencies)[len(latencies) // 2]
    assert median_ms <= max_median_ms, (
        f"SMA on {n_bars:,} bars ({median_ms:.3f} ms) exceeded agreed budget ({max_median_ms} ms)"
    )


# ---------------------------------------------------------------------------
# 5. Vertical Slice: Functions (plus) & Comparisons (is_greater)
# ---------------------------------------------------------------------------


def test_plus_function_block() -> None:
    # Scalar addition
    assert plus(10.0, 20.5) == 30.5

    # Series addition
    s1 = IndicatorSeries([10.0, 20.0, 30.0])
    s2 = IndicatorSeries([1.0, 2.0, 3.0])
    assert plus(s1, s2, shift=0) == 33.0
    assert plus(s1, s2, shift=1) == 22.0
    assert plus(s1, s2, shift=2) == 11.0

    # NaN handling
    assert np.isnan(plus(float("nan"), 10.0))
    assert np.isnan(plus(s1, s2, shift=10))


def test_is_greater_condition_block() -> None:
    # Scalar comparison
    assert is_greater(20.0, 10.0) is True
    assert is_greater(10.0, 20.0) is False
    assert is_greater(10.0, 10.0) is False

    # Series comparison
    s1 = IndicatorSeries([10.0, 25.0])
    s2 = IndicatorSeries([15.0, 20.0])
    assert is_greater(s1, s2, shift=0) is True  # 25 > 20
    assert is_greater(s1, s2, shift=1) is False  # 10 not > 15

    # NaN handling: missing data must never evaluate as valid true
    assert is_greater(float("nan"), 10.0) is False
    assert is_greater(10.0, float("nan")) is False


# ---------------------------------------------------------------------------
# 6. Vertical Slice: Action (log_to_file) & Discovery Invariant
# ---------------------------------------------------------------------------


def test_log_to_file_discovery_and_registration_never_touches_disk(
    tmp_path: Path,
) -> None:
    """CRITICAL: Block declaration, instantiation, and registration must NEVER perform file I/O."""
    target_file = tmp_path / "sandbox_audit.log"
    assert not target_file.exists()

    # 1. Instantiation does not create file
    action = LogToFileAction(
        filename="sandbox_audit.log",
        message="Test message",
        base_dir=str(tmp_path),
    )
    assert not target_file.exists(), "Instantiation must not touch the filesystem"

    # 2. Schema extraction does not create file
    schema = LogToFileAction.get_parameter_schema()
    assert "filename" in schema["properties"]
    assert not target_file.exists(), "Schema inspection must not touch the filesystem"

    # 3. Registration in BlockRegistry does not create file
    reg = BlockRegistry()
    reg.register_block(LogToFileAction)
    assert not target_file.exists(), "Registration must not touch the filesystem"

    # 4. Only calling .execute() performs file writing
    record = action.execute()
    assert target_file.exists()
    assert record.action_type == "log_to_file"
    assert "Test message\n" in target_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 7. Canonical Contracts (No Compatibility Aliases)
# ---------------------------------------------------------------------------


def test_canonical_metric_and_sizer_contracts() -> None:
    # Direct import from canonical packages
    assert issubclass(BaseMetric, object)
    assert issubclass(BasePositionSizer, object)

    # Verify no legacy aliases exist on code_editor.registry
    import app.workspace.code_editor.registry as editor_reg

    assert not hasattr(editor_reg, "BaseMetric")
    assert not hasattr(editor_reg, "BasePositionSizer")


def test_global_block_registry_registers_vertical_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    isolated_registry = BlockRegistry()
    current_module = sys.modules[__name__]
    monkeypatch.setattr(
        current_module,
        "block_registry",
        isolated_registry,
    )
    monkeypatch.setattr(
        "app.core.trading.blocks.registry.block_registry",
        isolated_registry,
    )
    monkeypatch.setattr(
        "app.include.blocks.registry.block_registry",
        isolated_registry,
    )
    block_registry.register_block(SMA)
    block_registry.register_block(plus)
    block_registry.register_block(is_greater)
    block_registry.register_block(LogToFileAction)

    snapshot = block_registry.snapshot()
    assert "indicator.trend.sma" in snapshot
    assert "function.plus" in snapshot
    assert "condition.is_greater" in snapshot
    assert "action.log_to_file" in snapshot
