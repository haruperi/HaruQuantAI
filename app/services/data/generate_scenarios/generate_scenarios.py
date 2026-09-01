"""Deterministic synthetic/scenario generation for ``FEAT-DATA-GENERATE_SCENARIOS``.

Generated output is always stored as scenario-shaped evidence and returned under a
new immutable UUIDv7. The implementation supports the proven seeded GBM baseline
plus bounded, explicitly pinned transforms; it never labels generated values as
observed provider history.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import random
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    Bar,
    GenerateScenariosRequest,
    GenerateScenariosSuccess,
    ScenarioTransform,
    SyntheticModelSpec,
)
from app.kernel.identity import generate_uuid7
from app.kernel.time import format_utc_timestamp, parse_utc_timestamp
from app.services.data.generate_scenarios.config import GenerateScenariosConfig

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability


def _failure(request_id: str, *, code: str, detail: str) -> DataFailure:
    return DataFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=404 if code == "DATA_NOT_FOUND" else 422,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


def _number(value: object, *, name: str, default: float | None = None) -> float:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _decimal_text(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("generated value must be finite")
    decimal = Decimal(str(value)).normalize()
    text = format(decimal, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _timeframe_delta(spec: SyntheticModelSpec) -> timedelta:
    multiple = spec.timeframe.multiple
    if spec.timeframe.unit == "MINUTE":
        return timedelta(minutes=multiple)
    if spec.timeframe.unit == "DAY":
        return timedelta(days=multiple)
    if spec.timeframe.unit == "WEEK":
        return timedelta(weeks=multiple)
    raise ValueError("MONTH synthetic timeframe requires calendar-aware generation")


def _seed(spec: SyntheticModelSpec) -> int:
    material = "|".join((spec.content_hash, *spec.seed_streams)).encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def generate_gbm_bars(
    spec: SyntheticModelSpec,
    *,
    max_points: int,
) -> tuple[Bar, ...]:
    """Generate bounded seeded GBM bars from one immutable model specification.

    Args:
        spec: Versioned synthetic-model specification.
        max_points: Hard generation bound.

    Returns:
        Deterministic synthetic bar tuple.

    Raises:
        ValueError: If model parameters/timeframe/window are unsupported.
    """
    if spec.model_type.upper() != "GBM":
        raise ValueError("only the proven GBM synthetic model is supported")
    initial_price = _number(spec.parameters.get("initial_price"), name="initial_price")
    drift = _number(spec.parameters.get("drift"), name="drift", default=0.0)
    volatility = _number(
        spec.parameters.get("volatility"), name="volatility", default=0.01
    )
    volume = _number(spec.parameters.get("volume"), name="volume", default=0.0)
    if initial_price <= 0 or volatility < 0 or volume < 0:
        raise ValueError("GBM price must be positive and volatility/volume non-negative")
    delta = _timeframe_delta(spec)
    start = parse_utc_timestamp(spec.from_at)
    end = parse_utc_timestamp(spec.to_at)
    points = int((end - start) / delta)
    if points <= 0 or points > max_points:
        raise ValueError("synthetic generation window exceeds configured bound")
    rng = random.Random(_seed(spec))
    annual_fraction = delta.total_seconds() / (365.25 * 86_400)
    price = initial_price
    bars: list[Bar] = []
    for index in range(points):
        shock = rng.gauss(0.0, 1.0)
        next_price = price * math.exp(
            (drift - 0.5 * volatility * volatility) * annual_fraction
            + volatility * math.sqrt(annual_fraction) * shock
        )
        high = max(price, next_price)
        low = min(price, next_price)
        bars.append(
            Bar(
                timestamp=format_utc_timestamp(start + delta * index),
                open=_decimal_text(price),
                high=_decimal_text(high),
                low=_decimal_text(low),
                close=_decimal_text(next_price),
                volume=_decimal_text(volume),
                source_sequence=index,
                flags=0,
            )
        )
        price = next_price
    return tuple(bars)


def _transform_bars(
    bars: tuple[Bar, ...],
    transforms: tuple[ScenarioTransform, ...],
) -> tuple[Bar, ...]:
    current = list(bars)
    for transform in transforms:
        parameters = transform.parameters
        if transform.kind in {"OUTAGE", "MISSINGNESS", "GAP"}:
            drop_every = int(_number(parameters.get("drop_every"), name="drop_every", default=10.0))
            if drop_every <= 1:
                raise ValueError("drop_every must be greater than 1")
            current = [bar for index, bar in enumerate(current, start=1) if index % drop_every]
            continue
        if transform.kind == "SHOCK":
            factor = _number(parameters.get("factor"), name="factor", default=1.0)
            if factor <= 0:
                raise ValueError("shock factor must be positive")
            current = [
                bar.model_copy(
                    update={
                        "open": _decimal_text(float(bar.open) * factor),
                        "high": _decimal_text(float(bar.high) * factor),
                        "low": _decimal_text(float(bar.low) * factor),
                        "close": _decimal_text(float(bar.close) * factor),
                    }
                )
                for bar in current
            ]
            continue
        if transform.kind == "LIQUIDITY":
            factor = _number(
                parameters.get("volume_factor"), name="volume_factor", default=1.0
            )
            if factor < 0:
                raise ValueError("volume_factor must be non-negative")
            current = [
                bar.model_copy(update={"volume": _decimal_text(float(bar.volume) * factor)})
                for bar in current
            ]
            continue
        if transform.kind == "VOLATILITY":
            factor = _number(parameters.get("factor"), name="factor", default=1.0)
            if factor < 0:
                raise ValueError("volatility factor must be non-negative")
            transformed: list[Bar] = []
            for bar in current:
                close = float(bar.close)
                high = close + (float(bar.high) - close) * factor
                low = close - (close - float(bar.low)) * factor
                transformed.append(
                    bar.model_copy(
                        update={"high": _decimal_text(high), "low": _decimal_text(low)}
                    )
                )
            current = transformed
    return tuple(current)


def _content_hash(
    bars: tuple[Bar, ...],
    *,
    classification: str,
    transforms: tuple[ScenarioTransform, ...],
) -> str:
    payload = {
        "classification": classification,
        "transforms": [item.model_dump(mode="json") for item in transforms],
        "bars": [bar.model_dump(mode="json") for bar in bars],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class GenerateScenariosService:
    """Capability implementation for explicit synthetic/scenario versions."""

    def __init__(
        self,
        store: DataSeriesStoreCapability,
        config: GenerateScenariosConfig,
    ) -> None:
        """Initialize with immutable storage and generation bounds."""
        self._store = store
        self._config = config

    async def generate_scenarios(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Configure, generate, or transform an explicit scenario series."""
        if request.operation == "CONFIGURE_MODEL":
            assert request.spec is not None
            if request.spec.model_type.upper() != "GBM":
                return _failure(
                    request.request_id,
                    code="DATA_VALIDATION_FAILED",
                    detail="Only the proven GBM synthetic model is available",
                )
            return GenerateScenariosSuccess(request_id=request.request_id, spec=request.spec)

        if request.operation == "GENERATE":
            assert request.spec is not None
            try:
                bars = generate_gbm_bars(
                    request.spec,
                    max_points=self._config.max_points,
                )
            except ValueError as error:
                return _failure(
                    request.request_id,
                    code="DATA_TIMEFRAME_UNSUPPORTED"
                    if "MONTH" in str(error)
                    else "DATA_VALIDATION_FAILED",
                    detail=str(error),
                )
            version_id = generate_uuid7()
            content_hash = _content_hash(
                bars,
                classification="SYNTHETIC",
                transforms=(),
            )
            await self._store.put_bars(
                version_id,
                bars,
                content_hash=content_hash,
                kind="SCENARIO",
            )
            return GenerateScenariosSuccess(
                request_id=request.request_id,
                spec=request.spec,
                scenario_version_id=version_id,
            )

        assert request.source_version_id is not None
        assert request.source_hash is not None
        assert request.classification is not None
        snapshot = await self._store.get_snapshot(request.source_version_id)
        if snapshot is None:
            return _failure(
                request.request_id,
                code="DATA_NOT_FOUND",
                detail="Scenario source version is unavailable",
            )
        if snapshot.content_hash != request.source_hash:
            return _failure(
                request.request_id,
                code="DATA_VERSION_CONFLICT",
                detail="Scenario source hash does not match committed evidence",
            )
        bars = await self._store.read_bars(request.source_version_id)
        if bars is None:
            return _failure(
                request.request_id,
                code="DATA_ALIGNMENT_INCOMPATIBLE",
                detail="Scenario transforms currently require bar-shaped source evidence",
            )
        try:
            transformed = _transform_bars(bars, request.transforms)
        except ValueError as error:
            return _failure(
                request.request_id,
                code="DATA_VALIDATION_FAILED",
                detail=str(error),
            )
        version_id = generate_uuid7()
        content_hash = _content_hash(
            transformed,
            classification=request.classification,
            transforms=request.transforms,
        )
        await self._store.put_bars(
            version_id,
            transformed,
            content_hash=content_hash,
            kind="SCENARIO",
        )
        return GenerateScenariosSuccess(
            request_id=request.request_id,
            scenario_version_id=version_id,
        )


async def _demo() -> None:
    """Demonstrate deterministic seeded GBM generation without persistence."""
    from app.contracts.catalogue.models import InstrumentRef
    from app.contracts.common.models import Timeframe

    spec = SyntheticModelSpec(
        spec_id=generate_uuid7(),
        model_type="GBM",
        model_version="1",
        parameters={"initial_price": 100, "drift": 0, "volatility": 0.1},
        timeframe=Timeframe(unit="MINUTE", multiple=1),
        from_at="2026-01-01T00:00:00.000000Z",
        to_at="2026-01-01T00:03:00.000000Z",
        instrument=InstrumentRef(instrument_id=generate_uuid7()),
        seed_streams=("demo",),
        content_hash="0" * 64,
    )
    print([bar.model_dump(mode="json") for bar in generate_gbm_bars(spec, max_points=10)])


if __name__ == "__main__":
    asyncio.run(_demo())
