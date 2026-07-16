"""Deterministic Decimal-only synthetic market-data generation."""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from app.services.data.contracts.errors import DataError
from app.services.data.contracts.market import (
    DataQualityReport,
    MarketDataset,
    SyntheticRequest,
)
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.processing.timeframes import TimeframeSpec, get_timeframe_spec
from app.utils import logger

SYNTHETIC_BAR_MAX_RECORDS = 100_000
SYNTHETIC_TICK_MAX_RECORDS = 250_000
SYNTHETIC_METHODS = ("gbm",)
_ANNUAL_SECONDS = Decimal(31_536_000)
_PRICE_QUANTUM = Decimal("0.00000001")
_VOLUME_QUANTUM = Decimal("0.0001")
_RANDOM_DENOMINATOR = Decimal(1 << 53)


def _uniform(rng: random.Random) -> Decimal:
    """Return one deterministic 53-bit Decimal uniform variate in [0, 1)."""
    logger.debug("Generating deterministic Decimal uniform variate")
    return Decimal(rng.getrandbits(53)) / _RANDOM_DENOMINATOR


def _normal(rng: random.Random) -> Decimal:
    """Return one deterministic zero-mean unit-variance CLT normal approximation."""
    logger.debug("Generating deterministic Decimal normal variate")
    return sum((_uniform(rng) for _ in range(12)), start=Decimal(0)) - Decimal(6)


def _exponential(rng: random.Random, mean: Decimal) -> Decimal:
    """Return one deterministic Decimal exponential variate."""
    logger.debug("Generating deterministic Decimal exponential variate")
    uniform = _uniform(rng)
    if uniform == 1:
        uniform = Decimal(1) - Decimal(1) / _RANDOM_DENOMINATOR
    return -(Decimal(1) - uniform).ln() * mean


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    """Quantize a finite generated value with the approved rounding policy."""
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
    """Generate a bounded Decimal geometric-Brownian path."""
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
    """Build deterministic canonical bars from one Decimal path."""
    logger.info("Building synthetic bars")
    records: list[OHLCVRecord] = []
    timestamp = request.start
    for index in range(request.record_count):
        segment = path[4 * index : 4 * index + 5]
        records.append(
            OHLCVRecord(
                timestamp=timestamp,
                source="synthetic",
                source_symbol=request.symbol,
                source_revision="v1",
                available_at=timestamp,
                open=_quantize(segment[0], _PRICE_QUANTUM),
                high=_quantize(max(segment), _PRICE_QUANTUM),
                low=_quantize(min(segment), _PRICE_QUANTUM),
                close=_quantize(segment[-1], _PRICE_QUANTUM),
                volume=_quantize(
                    _exponential(rng, Decimal(100)),
                    _VOLUME_QUANTUM,
                ),
                price_unit="USD",
                volume_unit="units",
            )
        )
        timestamp += spec.duration
    return tuple(records)


def _generate_ticks(
    request: SyntheticRequest,
    path: tuple[Decimal, ...],
    rng: random.Random,
) -> tuple[TickRecord, ...]:
    """Build deterministic canonical ticks from one Decimal path."""
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
                bid=_quantize(last * Decimal("0.9999"), _PRICE_QUANTUM),
                ask=_quantize(last * Decimal("1.0001"), _PRICE_QUANTUM),
                last=_quantize(last, _PRICE_QUANTUM),
                volume=_quantize(
                    _exponential(rng, Decimal(10)),
                    _VOLUME_QUANTUM,
                ),
                price_unit="USD",
                volume_unit="units",
            )
        )
        timestamp += timedelta(seconds=1)
    return tuple(records)


def generate_synthetic_dataset(request: SyntheticRequest) -> MarketDataset:
    """Generate a byte-reproducible bounded Decimal GBM dataset."""
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
    if not all(value.is_finite() for value in (mu, sigma, start)):
        raise DataError("PRECISION_MISMATCH", request_id=request.request_id)
    if sigma <= 0 or start <= 0:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "parameters"},
            request_id=request.request_id,
        )

    rng = random.Random(request.seed)
    if request.data_kind == "bars":
        if request.timeframe is None:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "timeframe"},
                request_id=request.request_id,
            )
        spec = get_timeframe_spec(request.timeframe)
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
        quality_status="passed",
        quality_score=Decimal(1),
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


__all__ = ["generate_synthetic_dataset"]
