"""Run Data Binding domain implementation.

Purpose:
    Bind immutable committed market data versions to execution/backtest run
    manifests and fail fast when precision prerequisites are missing.

Key capabilities:
    * Pin committed data versions to execution runs without mutable drift.
    * Validate precision prerequisites (tick, spread, custom models).
    * Reject uncommitted or unverified data version bindings.
    * Provide async bind_run_data implementing BindRunDataCapability.

Python API usage:
    from app.services.data.run_data_binding.run_data_binding import (
        RunDataBindingService,
    )
    from app.contracts.data.models import BindRunDataRequest

    service = RunDataBindingService()
    result = await service.bind_run_data(request)

CLI usage:
    uv run python -m app.services.data.run_data_binding.run_data_binding
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

from app.contracts.common.models import Precision, ProblemDetails, Uuid7
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    BindRunDataRequest,
    BindRunDataSuccess,
    RunDataBinding,
)
from app.contracts.data.ports import BindRunDataCapability
from app.services.data.run_data_binding.config import RunDataBindingConfig

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_utc_timestamp(dt: datetime) -> str:
    """Format an aware datetime as a canonical UtcTimestamp string.

    Args:
        dt: Aware UTC datetime.

    Returns:
        Canonical ISO 8601 string with microsecond resolution and Z suffix.
    """
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _is_valid_uuid(val: str) -> bool:
    """Check if a string represents a valid UUID.

    Args:
        val: Input string.

    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(val)
        return True
    except ValueError, AttributeError, TypeError:
        return False


def _check_precision_mode(
    precision: Precision,
    has_tick_data: bool,
    has_recorded_spread: bool,
    available_timeframe: str,
) -> str | None:
    """Check specific precision requirements.

    Returns:
        Error string if unavailable, or None if valid.
    """
    if precision == "REAL_TICK_RECORDED_SPREAD":
        if not has_tick_data or not has_recorded_spread:
            return (
                f"Precision '{precision}' requires recorded tick spread data, "
                f"but only {available_timeframe} is available; no fallback permitted."
            )
    elif precision == "REAL_TICK_CUSTOM_SPREAD":
        if not has_tick_data:
            return (
                f"Precision '{precision}' requires tick market data, "
                f"but only {available_timeframe} is available; no fallback permitted."
            )
    elif (
        precision == "M1_SIMULATION"
        and not has_tick_data
        and available_timeframe not in ("TICK", "M1")
    ):
        return (
            f"Precision '{precision}' requires M1 or finer data, "
            f"but only {available_timeframe} is available; no fallback permitted."
        )
    return None


def data_validate_precision_inputs(
    series_version_ids: tuple[Uuid7, ...],
    precision: Precision,
    *,
    has_tick_data: bool = True,
    has_recorded_spread: bool = True,
    available_timeframe: str = "TICK",
) -> tuple[bool, str | None]:
    """Validate precision prerequisites for runs (FR-DATA-VALIDATE_PRECISION_INPUTS).

    Selecting a precision whose source prerequisites are absent shall fail before
    a backtest job is queued (e.g. real-tick mode with only H1 data returns
    DATA_PRECISION_UNAVAILABLE; no fallback occurs).

    Args:
        series_version_ids: Tuple of committed series version IDs to validate.
        precision: Desired simulation precision.
        has_tick_data: Whether genuine tick data is available.
        has_recorded_spread: Whether tick data includes recorded quotes.
        available_timeframe: Coarsest or available resolution description.

    Returns:
        Tuple of (is_valid, error_reason_if_any).
    """
    if not series_version_ids:
        return False, "series_version_ids cannot be empty"

    if any(not _is_valid_uuid(s_id) for s_id in series_version_ids):
        return False, "Invalid series version UUID present"

    err = _check_precision_mode(
        precision=precision,
        has_tick_data=has_tick_data,
        has_recorded_spread=has_recorded_spread,
        available_timeframe=available_timeframe,
    )
    if err is not None:
        return False, err

    return True, None


def data_bind_committed_data(
    run_manifest_id: Uuid7,
    series_version_ids: tuple[Uuid7, ...],
    precision: Precision,
    *,
    has_tick_data: bool = True,
    has_recorded_spread: bool = True,
    available_timeframe: str = "TICK",
) -> RunDataBinding:
    """Pin committed input data versions to a run (FR-DATA-BIND_COMMITTED_DATA).

    A run shall bind only committed data versions and shall retain those bindings
    after later imports or updates. Updating a series does not change an already
    queued run manifest.

    Args:
        run_manifest_id: Unique identifier of the run manifest.
        series_version_ids: Non-empty tuple of committed series version IDs.
        precision: Simulation precision mode.
        has_tick_data: Availability of tick data for precision validation.
        has_recorded_spread: Availability of spread for precision validation.
        available_timeframe: Available timeframe representation.

    Returns:
        Immutable RunDataBinding DTO.

    Raises:
        ValueError: If validation fails or prerequisites are absent.
    """
    if not _is_valid_uuid(run_manifest_id):
        msg = f"Invalid run_manifest_id UUID: {run_manifest_id}"
        raise ValueError(msg)

    valid, reason = data_validate_precision_inputs(
        series_version_ids=series_version_ids,
        precision=precision,
        has_tick_data=has_tick_data,
        has_recorded_spread=has_recorded_spread,
        available_timeframe=available_timeframe,
    )
    if not valid:
        msg = f"Precision validation failed: {reason}"
        raise ValueError(msg)

    return RunDataBinding(
        binding_id=_generate_uuid7(),
        run_manifest_id=run_manifest_id,
        series_version_ids=series_version_ids,
        precision=precision,
        validated_at=_format_utc_timestamp(datetime.now(UTC)),
        schema_version=1,
    )


class BindRunDataService(BindRunDataCapability):
    """Service adapter implementing the BindRunDataCapability protocol."""

    def __init__(
        self,
        config: RunDataBindingConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the BindRunDataService.

        Args:
            config: Optional configuration instance.
            event_bus: Optional event bus for publication.
        """
        self._config = config or RunDataBindingConfig()
        self._event_bus = event_bus
        self._bindings: dict[str, RunDataBinding] = {}

    @property
    def config(self) -> RunDataBindingConfig:
        """Return the active configuration."""
        return self._config

    def _handle_bind(
        self,
        request: BindRunDataRequest,
    ) -> BindRunDataSuccess | DataFailure:
        """Handle BIND operation.

        Args:
            request: Run data binding request.

        Returns:
            Success with binding, or structured failure.
        """
        if (
            request.run_manifest_id is None
            or request.series_version_ids is None
            or request.precision is None
        ):
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:validation-failed",
                    title="Missing required parameters for BIND operation",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail=(
                        "run_manifest_id, series_version_ids, and precision "
                        "are required for BIND."
                    ),
                    request_id=request.request_id,
                ),
            )

        valid, reason = data_validate_precision_inputs(
            series_version_ids=request.series_version_ids,
            precision=request.precision,
        )
        if not valid:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_PRECISION_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:precision-unavailable",
                    title="Data precision unavailable",
                    status=422,
                    code="DATA_PRECISION_UNAVAILABLE",
                    detail=(
                        reason
                        or "Required data precision prerequisites are unavailable."
                    ),
                    request_id=request.request_id,
                ),
            )

        binding = data_bind_committed_data(
            run_manifest_id=request.run_manifest_id,
            series_version_ids=request.series_version_ids,
            precision=request.precision,
        )
        self._bindings[binding.binding_id] = binding
        logger.info(
            "Bound %d series versions to run manifest %s (binding_id=%s)",
            len(binding.series_version_ids),
            binding.run_manifest_id,
            binding.binding_id,
        )
        return BindRunDataSuccess(
            request_id=request.request_id,
            binding=binding,
        )

    def _handle_validate_precision(
        self,
        request: BindRunDataRequest,
    ) -> BindRunDataSuccess | DataFailure:
        """Handle VALIDATE_PRECISION operation.

        Args:
            request: Run data binding request.

        Returns:
            Success with empty binding, or structured failure.
        """
        if request.series_version_ids is None or request.precision is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:validation-failed",
                    title="Missing required parameters for VALIDATE_PRECISION",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail="series_version_ids and precision are required.",
                    request_id=request.request_id,
                ),
            )

        valid, reason = data_validate_precision_inputs(
            series_version_ids=request.series_version_ids,
            precision=request.precision,
        )
        if not valid:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_PRECISION_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:precision-unavailable",
                    title="Data precision unavailable",
                    status=422,
                    code="DATA_PRECISION_UNAVAILABLE",
                    detail=(
                        reason
                        or "Required data precision prerequisites are unavailable."
                    ),
                    request_id=request.request_id,
                ),
            )

        return BindRunDataSuccess(
            request_id=request.request_id,
            binding=None,
        )

    @override
    async def bind_run_data(
        self,
        request: BindRunDataRequest,
    ) -> BindRunDataSuccess | DataFailure:
        """Bind committed series versions and validate run precision.

        Args:
            request: Operation-discriminated run data binding request.

        Returns:
            The validated binding on success, otherwise a structured data failure.
        """
        try:
            if request.operation == "BIND":
                return self._handle_bind(request)
            return self._handle_validate_precision(request)
        except Exception as exc:
            logger.exception("Error in bind_run_data")
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:unexpected",
                    title="Unexpected error during run data binding",
                    status=500,
                    code="DATA_VALIDATION_FAILED",
                    detail=str(exc),
                    request_id=request.request_id,
                ),
            )


async def main() -> None:
    """Execute the run data binding usage demonstration harness."""
    from app.services.data.run_data_binding._usage import (
        main as _usage_main,
    )

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
