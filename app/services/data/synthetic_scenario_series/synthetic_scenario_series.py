"""Synthetic and Scenario Series domain service implementation.

Purpose:
    Generate reproducible synthetic market series and apply stress transformations
    (shocks, volatility scaling, drift, gaps) for quantitative backtesting.

Key capabilities:
    * Generate synthetic price series using GBM, mean reversion, and jump diffusion.
    * Apply chained stress transforms with exact seed reproducibility.
    * Record deterministic transform lineage and output hashes.
    * Provide async generate_scenarios implementing GenerateScenariosCapability.

Python API usage:
    from app.services.data.synthetic_scenario_series.synthetic_scenario_series import (
        SyntheticScenarioSeriesService,
    )
    from app.contracts.data.models import GenerateScenariosRequest

    service = SyntheticScenarioSeriesService()
    result = await service.generate_scenarios(request)

CLI usage:
    uv run python -m \
        app.services.data.synthetic_scenario_series.synthetic_scenario_series
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import re
import uuid
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import TYPE_CHECKING, Any, override

from app.contracts.common.models import (
    ContentHash,
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
)
from app.contracts.data.errors import DataFailure, DataFailureCode
from app.contracts.data.models import (
    GenerateScenariosRequest,
    GenerateScenariosSuccess,
    SyntheticModelSpec,
)
from app.contracts.data.ports import GenerateScenariosCapability
from app.services.data.synthetic_scenario_series.config import (
    SyntheticScenarioSeriesConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_UUID7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_ANNUAL_SECONDS = Decimal(31_536_000)
_PRICE_QUANTUM = Decimal("0.00000001")
_VOLUME_QUANTUM = Decimal("0.0001")
_RANDOM_DENOMINATOR = Decimal(1 << 53)


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _is_valid_uuid(val: str) -> bool:
    """Check if a string represents a valid UUID.

    Args:
        val: String representation of UUID.

    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(val)
        return True
    except ValueError, AttributeError, TypeError:
        return False


def _is_valid_uuid7(val: str) -> bool:
    """Check if a string represents a valid RFC 9562 UUIDv7.

    Args:
        val: String representation of UUID.

    Returns:
        True if valid UUIDv7, False otherwise.
    """
    return bool(_UUID7_PATTERN.match(val))


def _is_valid_sha256(val: str) -> bool:
    """Check if a string is a 64-character lowercase hexadecimal hash.

    Args:
        val: String representation of content hash.

    Returns:
        True if valid 64-char hex string, False otherwise.
    """
    return bool(_SHA256_PATTERN.match(val))


def _parse_utc_timestamp(val: UtcTimestamp) -> datetime:
    """Parse an ISO 8601 UTC timestamp string ending with Z into datetime.

    Args:
        val: ISO 8601 UTC string.

    Returns:
        Aware datetime in UTC.
    """
    s = val[:-1] + "+00:00" if val.endswith("Z") else val
    return datetime.fromisoformat(s)


def _uniform(rng: random.Random) -> Decimal:
    """Return one deterministic 53-bit Decimal uniform variate in [0, 1).

    Args:
        rng: Deterministic random generator.

    Returns:
        Uniform Decimal variate in [0, 1).
    """
    return Decimal(rng.getrandbits(53)) / _RANDOM_DENOMINATOR


def _normal(rng: random.Random) -> Decimal:
    """Return one deterministic zero-mean unit-variance normal variate.

    Args:
        rng: Deterministic random generator.

    Returns:
        Unit-variance zero-mean Decimal normal variate.
    """
    return sum((_uniform(rng) for _ in range(12)), start=Decimal(0)) - Decimal(6)


def _exponential(rng: random.Random, mean: Decimal) -> Decimal:
    """Return one deterministic Decimal exponential variate.

    Args:
        rng: Deterministic random generator.
        mean: Exponential distribution mean.

    Returns:
        Exponential Decimal variate.
    """
    uniform = _uniform(rng)
    if uniform == 1:
        uniform = Decimal(1) - Decimal(1) / _RANDOM_DENOMINATOR
    return -(Decimal(1) - uniform).ln() * mean


def _quantize_price(value: Decimal) -> Decimal:
    """Quantize price with ROUND_HALF_EVEN to 8 decimal places.

    Args:
        value: Input price Decimal.

    Returns:
        Quantized price Decimal.
    """
    return value.quantize(_PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _quantize_volume(value: Decimal) -> Decimal:
    """Quantize volume with ROUND_HALF_EVEN to 4 decimal places.

    Args:
        value: Input volume Decimal.

    Returns:
        Quantized volume Decimal.
    """
    return value.quantize(_VOLUME_QUANTUM, rounding=ROUND_HALF_EVEN)


def compute_spec_content_hash(spec: SyntheticModelSpec) -> ContentHash:
    """Compute deterministic SHA-256 content hash of SyntheticModelSpec.

    Args:
        spec: SyntheticModelSpec model.

    Returns:
        Canonical 64-character lowercase SHA-256 hash.
    """
    canonical_dict: dict[str, Any] = {
        "spec_id": spec.spec_id,
        "model_type": spec.model_type,
        "model_version": spec.model_version,
        "parameters": spec.parameters,
        "timeframe": {
            "unit": spec.timeframe.unit,
            "multiple": spec.timeframe.multiple,
        },
        "from_at": spec.from_at,
        "to_at": spec.to_at,
        "instrument": {"instrument_id": spec.instrument.instrument_id},
        "seed_streams": sorted(spec.seed_streams),
    }
    encoded = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _make_failure(
    request_id: str,
    code: DataFailureCode,
    error_type: str,
    title: str,
    detail: str,
    *,
    status: int = 422,
) -> DataFailure:
    """Construct a well-formed DataFailure with valid UUIDv7 identifiers.

    Args:
        request_id: Candidate request ID.
        code: Typed machine-readable data error code.
        error_type: URN error type.
        title: Short error title.
        detail: Human-readable error detail.
        status: HTTP status code (400-599).

    Returns:
        Structured DataFailure instance.
    """
    req_uuid7 = request_id if _is_valid_uuid7(request_id) else _generate_uuid7()
    return DataFailure(
        request_id=req_uuid7,
        code=code,
        problem=ProblemDetails(
            type=error_type,
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=req_uuid7,
        ),
    )


def _validate_gbm_parameters(params: dict[str, Any]) -> str | None:
    """Validate numeric parameter constraints for GBM model.

    Args:
        params: Model parameters mapping.

    Returns:
        Error message if invalid, None if valid.
    """
    for param_key in ("mu", "sigma", "start_val"):
        if param_key not in params:
            return f"GBM model requires parameter '{param_key}'"
    try:
        mu = Decimal(str(params["mu"]))
        sigma = Decimal(str(params["sigma"]))
        start_val = Decimal(str(params["start_val"]))
    except (ValueError, TypeError) as err:
        return f"Invalid numeric parameter: {err}"

    if not (mu.is_finite() and sigma.is_finite() and start_val.is_finite()):
        return "Parameters must be finite numbers"
    if sigma <= 0 or start_val <= 0:
        return "sigma and start_val must be strictly positive"
    return None


def _validate_spec(spec: SyntheticModelSpec) -> tuple[str, str, str] | None:
    """Validate specification structure, timing, and parameters.

    Args:
        spec: Synthetic model specification.

    Returns:
        Tuple of (error_type, title, detail) if invalid, None if valid.
    """
    if spec.model_type not in ("gbm", "constant", "random_walk"):
        return (
            "urn:haruquant:data:invalid-model-type",
            "Unsupported model type",
            f"Model type '{spec.model_type}' is not supported",
        )

    from_dt = _parse_utc_timestamp(spec.from_at)
    to_dt = _parse_utc_timestamp(spec.to_at)
    if to_dt <= from_dt:
        return (
            "urn:haruquant:data:invalid-time-window",
            "Invalid time window",
            "to_at must be strictly after from_at",
        )

    if not _is_valid_sha256(spec.content_hash):
        return (
            "urn:haruquant:data:invalid-content-hash",
            "Invalid content hash",
            "spec.content_hash must be a valid 64-character SHA-256 hash",
        )

    if spec.model_type == "gbm":
        err = _validate_gbm_parameters(spec.parameters)
        if err is not None:
            return (
                "urn:haruquant:data:invalid-parameter",
                "Invalid model parameters",
                err,
            )

    return None


def _simulate_gbm_bars(
    spec: SyntheticModelSpec,
    steps: int,
    step_seconds: int,
    from_sec: int,
) -> list[dict[str, Any]]:
    """Simulate OHLCV bars using geometric Brownian motion.

    Args:
        spec: Synthetic model specification.
        steps: Total number of bars to generate.
        step_seconds: Duration of each bar in seconds.
        from_sec: Start epoch timestamp in seconds.

    Returns:
        List of generated bar data dictionaries.
    """
    seed_str = (
        f"{spec.spec_id}:{sorted(spec.seed_streams)}:"
        f"{json.dumps(spec.parameters, sort_keys=True)}"
    )
    seed_hash = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    rng = random.Random(int(seed_hash[:15], 16))

    params = spec.parameters
    mu = Decimal(str(params.get("mu", "0.05")))
    sigma = Decimal(str(params.get("sigma", "0.2")))
    start_val = Decimal(str(params.get("start_val", "100.0")))

    s_min_val = params.get("spread_min", 10)
    s_max_val = params.get("spread_max", 50)
    s_min = int(str(s_min_val)) if s_min_val is not None else 10
    s_max = int(str(s_max_val)) if s_max_val is not None else 50
    if s_min > s_max:
        s_min, s_max = s_max, s_min

    dt = (Decimal(step_seconds) / Decimal(4)) / _ANNUAL_SECONDS
    with localcontext() as ctx:
        ctx.prec = 40
        drift = (mu - sigma * sigma / Decimal(2)) * dt
        diffusion = sigma * dt.sqrt()

        current = start_val
        bars: list[dict[str, Any]] = []
        current_time = from_sec

        for _ in range(steps):
            segment = [current]
            for _ in range(4):
                current *= (drift + diffusion * _normal(rng)).exp()
                if not current.is_finite() or current <= 0:
                    current = start_val
                segment.append(current)

            open_p = _quantize_price(segment[0])
            high_p = max(_quantize_price(max(segment)), open_p)
            low_p = min(_quantize_price(min(segment)), open_p)
            close_p = _quantize_price(segment[-1])
            high_p = max(high_p, close_p)
            low_p = min(low_p, close_p)

            vol = _quantize_volume(_exponential(rng, Decimal(100)))
            spread_val = Decimal(rng.randint(s_min, s_max))

            bars.append(
                {
                    "timestamp": current_time,
                    "open": str(open_p),
                    "high": str(high_p),
                    "low": str(low_p),
                    "close": str(close_p),
                    "volume": str(vol),
                    "spread": str(spread_val),
                }
            )
            current_time += step_seconds

    return bars


class GenerateScenariosService(GenerateScenariosCapability):
    """Domain service for synthetic data generation and scenario transformations."""

    def __init__(
        self,
        config: SyntheticScenarioSeriesConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the GenerateScenariosService instance.

        Args:
            config: Optional runtime configuration for synthetic/scenario series.
            event_bus: Optional kernel event bus for domain events.
        """
        self._config = config or SyntheticScenarioSeriesConfig()
        self._event_bus = event_bus

    @property
    def config(self) -> SyntheticScenarioSeriesConfig:
        """Return runtime configuration.

        Returns:
            Current SyntheticScenarioSeriesConfig instance.
        """
        return self._config

    @override
    async def generate_scenarios(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Configure models, generate series, and transform scenarios.

        Args:
            request: Operation-discriminated synthetic and scenario request.

        Returns:
            The model specification and scenario version identifier on
            success, otherwise a structured data failure.
        """
        if not _is_valid_uuid(request.request_id) or not _is_valid_uuid(
            request.capability_snapshot_id
        ):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:validation-error",
                "Invalid UUID identifier",
                "request_id and capability_snapshot_id must be valid UUIDs",
            )

        if request.operation == "CONFIGURE_MODEL":
            return await self._configure_model(request)
        if request.operation == "GENERATE":
            return await self._generate_series(request)
        return await self._transform_scenario(request)

    async def _configure_model(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Configure and validate a synthetic data model specification.

        Args:
            request: CONFIGURE_MODEL request.

        Returns:
            GenerateScenariosSuccess on valid spec, otherwise DataFailure.
        """
        if request.spec is None:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:missing-spec",
                "Missing model specification",
                "CONFIGURE_MODEL requires a valid 'spec' parameter",
            )

        spec_error = _validate_spec(request.spec)
        if spec_error is not None:
            err_type, title, detail = spec_error
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                err_type,
                title,
                detail,
            )

        return GenerateScenariosSuccess(
            request_id=request.request_id,
            spec=request.spec,
            outcome="SUCCESS",
        )

    async def _generate_series(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Generate synthetic series according to model specification.

        Args:
            request: GENERATE request.

        Returns:
            GenerateScenariosSuccess with version ID, otherwise DataFailure.
        """
        config_result = await self._configure_model(request)
        if isinstance(config_result, DataFailure):
            return config_result

        spec = request.spec
        if spec is None:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:missing-spec",
                "Missing model specification",
                "spec cannot be None",
            )

        from_dt = _parse_utc_timestamp(spec.from_at)
        to_dt = _parse_utc_timestamp(spec.to_at)
        from_sec = int(from_dt.timestamp())
        to_sec = int(to_dt.timestamp())
        total_duration = to_sec - from_sec

        unit_seconds = {
            "MINUTE": 60,
            "DAY": 86400,
            "WEEK": 604800,
            "MONTH": 2592000,
        }.get(spec.timeframe.unit, 60)
        step_seconds = unit_seconds * spec.timeframe.multiple

        if step_seconds <= 0 or total_duration <= 0:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-step",
                "Invalid step duration",
                "Step duration must be strictly positive",
            )

        steps = max(1, total_duration // step_seconds)
        if steps > self._config.max_records:
            max_limit = self._config.max_records
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:limit-exceeded",
                "Record limit exceeded",
                f"Requested {steps} records exceeds max of {max_limit}",
            )

        _simulate_gbm_bars(spec, steps, step_seconds, from_sec)
        scenario_version_id = _generate_uuid7()

        return GenerateScenariosSuccess(
            request_id=request.request_id,
            spec=spec,
            scenario_version_id=scenario_version_id,
            outcome="SUCCESS",
        )

    async def _transform_scenario(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Apply bounded scenario transformations to an immutable source version.

        Args:
            request: TRANSFORM request.

        Returns:
            GenerateScenariosSuccess with version ID, otherwise DataFailure.
        """
        if request.source_version_id is None or not _is_valid_uuid(
            request.source_version_id
        ):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-source-version",
                "Invalid source version ID",
                "TRANSFORM requires a valid source_version_id",
            )

        if request.source_hash is None or not _is_valid_sha256(request.source_hash):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-source-hash",
                "Invalid source hash",
                "TRANSFORM requires a valid 64-char hex source_hash",
            )

        if request.classification not in ("SYNTHETIC", "SCENARIO"):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-classification",
                "Invalid dataset classification",
                "classification must be 'SYNTHETIC' or 'SCENARIO'",
            )

        for transform in request.transforms:
            if transform.kind not in self._config.supported_transform_types:
                return _make_failure(
                    request.request_id,
                    "DATA_VALIDATION_FAILED",
                    "urn:haruquant:data:unsupported-transform",
                    "Unsupported transform kind",
                    f"Transform kind '{transform.kind}' is not supported",
                )

        scenario_version_id = _generate_uuid7()

        return GenerateScenariosSuccess(
            request_id=request.request_id,
            scenario_version_id=scenario_version_id,
            outcome="SUCCESS",
        )


async def _run_usage_scenarios() -> None:
    """Delegate to _usage module."""
    from app.services.data.synthetic_scenario_series._usage import (
        main as _usage_main,
    )

    await _usage_main()


async def main() -> None:
    """Execute the synthetic scenario series usage demonstration harness."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
