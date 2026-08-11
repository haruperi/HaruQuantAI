"""Generate deterministic seeded geometric-Brownian market-data fixtures.

The generated prices are synthetic and exist only for fixtures and tests. No output
of this feature may be presented as observed market evidence or used in an official
Simulation run.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import (
    DataQualityReport,
    MarketDataset,
)
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.time_sessions.timeframes import (
    TimeframeSpec,
    _get_timeframe_spec_raw,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.synthetic_data.contracts import SyntheticRequest

SYNTHETIC_BAR_MAX_RECORDS = 100_000
SYNTHETIC_TICK_MAX_RECORDS = 250_000
SYNTHETIC_METHODS = ("gbm",)
_ANNUAL_SECONDS = Decimal(31_536_000)
_PRICE_QUANTUM = Decimal("0.00000001")
_VOLUME_QUANTUM = Decimal("0.0001")
_RANDOM_DENOMINATOR = Decimal(1 << 53)


def _uniform(rng: random.Random) -> Decimal:
    """Return one deterministic 53-bit Decimal uniform variate in [0, 1).

    Args:
        rng: The ``rng`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Generating deterministic Decimal uniform variate")
    return Decimal(rng.getrandbits(53)) / _RANDOM_DENOMINATOR


def _normal(rng: random.Random) -> Decimal:
    """Return one deterministic zero-mean unit-variance CLT normal approximation.

    Args:
        rng: The ``rng`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Generating deterministic Decimal normal variate")
    return sum((_uniform(rng) for _ in range(12)), start=Decimal(0)) - Decimal(6)


def _exponential(rng: random.Random, mean: Decimal) -> Decimal:
    """Return one deterministic Decimal exponential variate.

    Args:
        rng: The ``rng`` argument.
        mean: The ``mean`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Generating deterministic Decimal exponential variate")
    uniform = _uniform(rng)
    if uniform == 1:
        uniform = Decimal(1) - Decimal(1) / _RANDOM_DENOMINATOR
    return -(Decimal(1) - uniform).ln() * mean


# Renamed during the `CAP-DATA-026` D7 merge. The two source modules each defined a
# private `_quantize`, and they were NOT equivalent: the synthetic-generation one
# rejects non-finite values with `PRECISION_MISMATCH`, the tick-generation one does
# not. Merging them under one name silently dropped the guard from one half, so both
# are kept with distinct names and their original behaviour.
def _quantize_synthetic(value: Decimal, quantum: Decimal) -> Decimal:
    """Quantize a finite generated value with the approved rounding policy.

    Args:
        value: The ``value`` argument.
        quantum: The ``quantum`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.debug("Quantizing synthetic Decimal value")
    if not value.is_finite():
        raise DataError("PRECISION_MISMATCH")
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


def _gbm_path(
    *,
    start: Decimal,
    mu: Decimal,
    sigma: Decimal,
    step_seconds: Decimal,
    steps: int,
    rng: random.Random,
) -> tuple[Decimal, ...]:
    """Generate a bounded Decimal geometric-Brownian path.

    Args:
        start: The ``start`` argument.
        mu: The ``mu`` argument.
        sigma: The ``sigma`` argument.
        step_seconds: The ``step_seconds`` argument.
        steps: The ``steps`` argument.
        rng: The ``rng`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.info("Generating deterministic Decimal GBM path")
    dt = step_seconds / _ANNUAL_SECONDS
    with localcontext() as context:
        context.prec = 40
        drift = (mu - sigma * sigma / Decimal(2)) * dt
        diffusion = sigma * dt.sqrt()
        values = [start]
        current = start
        for _ in range(steps):
            current *= (drift + diffusion * _normal(rng)).exp()
            if not current.is_finite() or current <= 0:
                raise DataError("DATA_QUALITY_FAILED")
            values.append(current)
    return tuple(values)


def _generate_bars(
    request: SyntheticRequest,
    path: tuple[Decimal, ...],
    spec: TimeframeSpec,
    rng: random.Random,
) -> tuple[OHLCVRecord, ...]:
    """Build deterministic canonical bars from one Decimal path.

    Args:
        request: The ``request`` argument.
        path: The ``path`` argument.
        spec: The ``spec`` argument.
        rng: The ``rng`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Building synthetic bars")
    records: list[OHLCVRecord] = []
    timestamp = request.start
    s_min_val = request.parameters.get("spread_min")
    s_max_val = request.parameters.get("spread_max")
    spread_min = int(s_min_val) if s_min_val is not None else 10
    spread_max = int(s_max_val) if s_max_val is not None else 50
    if spread_min > spread_max:
        spread_min, spread_max = spread_max, spread_min

    for index in range(request.record_count):
        segment = path[4 * index : 4 * index + 5]
        high_val = _quantize_synthetic(max(segment), _PRICE_QUANTUM)
        low_val = _quantize_synthetic(min(segment), _PRICE_QUANTUM)
        spread_val = Decimal(rng.randint(spread_min, spread_max))
        records.append(
            OHLCVRecord(
                timestamp=timestamp,
                source="synthetic",
                source_symbol=request.symbol,
                source_revision="v1",
                available_at=timestamp,
                open=_quantize_synthetic(segment[0], _PRICE_QUANTUM),
                high=high_val,
                low=low_val,
                close=_quantize_synthetic(segment[-1], _PRICE_QUANTUM),
                volume=_quantize_synthetic(
                    _exponential(rng, Decimal(100)),
                    _VOLUME_QUANTUM,
                ),
                price_unit="USD",
                volume_unit="units",
                spread=spread_val,
                spread_unit="points",
            )
        )
        timestamp += spec.duration
    return tuple(records)


def _generate_ticks(
    request: SyntheticRequest,
    path: tuple[Decimal, ...],
    rng: random.Random,
) -> tuple[TickRecord, ...]:
    """Build deterministic canonical ticks from one Decimal path.

    Args:
        request: The ``request`` argument.
        path: The ``path`` argument.
        rng: The ``rng`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Building synthetic ticks")
    records: list[TickRecord] = []
    timestamp = request.start
    for index in range(request.record_count):
        last = path[index]
        records.append(
            TickRecord(
                timestamp=timestamp,
                source="synthetic",
                source_symbol=request.symbol,
                source_revision="v1",
                available_at=timestamp,
                bid=_quantize_synthetic(last * Decimal("0.9999"), _PRICE_QUANTUM),
                ask=_quantize_synthetic(last * Decimal("1.0001"), _PRICE_QUANTUM),
                last=_quantize_synthetic(last, _PRICE_QUANTUM),
                volume=_quantize_synthetic(
                    _exponential(rng, Decimal(10)),
                    _VOLUME_QUANTUM,
                ),
                price_unit="USD",
                volume_unit="units",
            )
        )
        timestamp += timedelta(seconds=1)
    return tuple(records)


def _validate_synthetic_request(
    request: SyntheticRequest,
) -> tuple[Decimal, Decimal, Decimal]:
    """Validate input parameters for synthetic generation.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    logger.debug("Validating synthetic generation request parameters")
    if request.seed is None:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "seed"},
            request_id=request.request_id,
        )
    missing = tuple(
        name for name in ("mu", "sigma", "start_val") if name not in request.parameters
    )
    if missing:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"missing_count": len(missing)},
            request_id=request.request_id,
        )
    mu = request.parameters["mu"]
    sigma = request.parameters["sigma"]
    start = request.parameters["start_val"]
    s_min = request.parameters.get("spread_min")
    s_max = request.parameters.get("spread_max")
    for s_val in (s_min, s_max):
        if s_val is not None and not s_val.is_finite():
            raise DataError("PRECISION_MISMATCH", request_id=request.request_id)
        if s_val is not None and s_val < 0:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"field": "spread"},
                request_id=request.request_id,
            )
    if s_min is not None and s_max is not None and s_min > s_max:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "spread_min"},
            request_id=request.request_id,
        )
    if not all(value.is_finite() for value in (mu, sigma, start)):
        raise DataError("PRECISION_MISMATCH", request_id=request.request_id)
    if sigma <= 0 or start <= 0:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "parameters"},
            request_id=request.request_id,
        )
    return mu, sigma, start


def _generate_synthetic_dataset_raw(request: SyntheticRequest) -> MarketDataset:
    """Generate a byte-reproducible bounded Decimal GBM dataset.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: On any validation, limit, or generation failure.
    """
    logger.info("Generating synthetic dataset for request %s", request.request_id)
    maximum = (
        SYNTHETIC_BAR_MAX_RECORDS
        if request.data_kind == "bars"
        else SYNTHETIC_TICK_MAX_RECORDS
    )
    if request.record_count > maximum:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"record_count": request.record_count, "maximum": maximum},
            request_id=request.request_id,
        )
    mu, sigma, start = _validate_synthetic_request(request)

    rng = random.Random(request.seed)
    if request.data_kind == "bars":
        if request.timeframe is None:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "timeframe"},
                request_id=request.request_id,
            )
        spec = _get_timeframe_spec_raw(request.timeframe)
        path = _gbm_path(
            start=start,
            mu=mu,
            sigma=sigma,
            step_seconds=Decimal(str(spec.duration.total_seconds())) / Decimal(4),
            steps=request.record_count * 4,
            rng=rng,
        )
        records: tuple[OHLCVRecord | TickRecord, ...] = _generate_bars(
            request,
            path,
            spec,
            rng,
        )
    else:
        path = _gbm_path(
            start=start,
            mu=mu,
            sigma=sigma,
            step_seconds=Decimal(1),
            steps=request.record_count,
            rng=rng,
        )
        records = _generate_ticks(request, path, rng)

    generated_at = records[-1].available_at
    quality = DataQualityReport(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=max(1, min(1_000, len(records))),
        schema_version="v1",
        generated_at=generated_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind=request.data_kind,
        symbol=request.symbol,
        timeframe=request.timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=generated_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={
            "generator": "decimal_gbm",
            "seed": str(request.seed),
            "rounding": "ROUND_HALF_EVEN",
        },
        license_metadata={"license": "synthetic-public"},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy=request.precision_policy,
        request_id=request.request_id,
    )


def generate_synthetic_dataset(
    request: SyntheticRequest,
) -> StandardResponse[MarketDataset]:
    """Generate a byte-reproducible bounded Decimal GBM dataset.

    Args:
        request: Canonical synthetic-generation request.

    Returns:
        Standard response carrying the generated ``MarketDataset``.

    Raises:
        (in-band) ``DataError`` codes on validation, limit, or generation failure.
    """
    return run_data_operation(
        operation="data.synthetic_data.generate_synthetic_dataset",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _generate_synthetic_dataset_raw(request),
    )


def _generate_synthetic_ticks_raw(request: SyntheticRequest) -> MarketDataset:
    """Generate GBM-based synthetic tick records; raises if kind is not ticks.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: ``VALIDATION_FAILED`` if ``data_kind`` is not ``ticks``.
    """
    logger.info("Executing public DATA synthetic-tick generation")
    if request.data_kind != "ticks":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"generate_synthetic_ticks requires ticks data_kind, "
                    f"got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    return _generate_synthetic_dataset_raw(request)


def generate_synthetic_ticks(
    request: SyntheticRequest,
) -> StandardResponse[MarketDataset]:
    """Generate GBM-based synthetic tick records.

    Args:
        request: Canonical synthetic-generation request (must be ``ticks``).

    Returns:
        Standard response carrying the generated ``MarketDataset``.

    Raises:
        (in-band) ``DataError`` codes on validation, limit, or generation failure.
    """
    return run_data_operation(
        operation="data.synthetic_data.generate_synthetic_ticks",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _generate_synthetic_ticks_raw(request),
    )


def _generate_synthetic_bars_raw(request: SyntheticRequest) -> MarketDataset:
    """Generate GBM-based synthetic OHLCV bar records; raises if kind is not bars.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: ``VALIDATION_FAILED`` if ``data_kind`` is not ``bars``.
    """
    logger.info("Executing public DATA synthetic-bar generation")
    if request.data_kind != "bars":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"generate_synthetic_bars requires bars data_kind, "
                    f"got '{request.data_kind}'"
                )
            },
            request_id=request.request_id,
        )
    return _generate_synthetic_dataset_raw(request)


def generate_synthetic_bars(
    request: SyntheticRequest,
) -> StandardResponse[MarketDataset]:
    """Generate GBM-based synthetic OHLCV bar records.

    Args:
        request: Canonical synthetic-generation request (must be ``bars``).

    Returns:
        Standard response carrying the generated ``MarketDataset``.

    Raises:
        (in-band) ``DataError`` codes on validation, limit, or generation failure.
    """
    return run_data_operation(
        operation="data.synthetic_data.generate_synthetic_bars",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _generate_synthetic_bars_raw(request),
    )


__all__ = [
    "generate_synthetic_bars",
    "generate_synthetic_dataset",
    "generate_synthetic_ticks",
]
