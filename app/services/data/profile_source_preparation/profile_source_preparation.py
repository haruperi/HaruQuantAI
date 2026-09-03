"""Volume Profile Source Preparation domain implementation.

Purpose:
    Prepare and validate session and price-bin source declarations for Volume
    Profile and TPO (Time Price Opportunity) analysis.

Key capabilities:
    * Validate tick or bar input market series against declared profiles.
    * Enforce trading session boundary alignment without lookahead bias.
    * Verify price-step rules, bin-count thresholds, and source sufficiency.
    * Provide async prepare_profiles implementing PrepareProfilesCapability.

Python API usage:
    from app.services.data.profile_source_preparation import (
        profile_source_preparation as psp,
    )
    from app.contracts.data.models import PrepareProfilesRequest

    service = psp.PrepareProfilesService()
    result = await service.prepare_profiles(request)

CLI usage:
    uv run python -m \
        app.services.data.profile_source_preparation.profile_source_preparation
"""

from __future__ import annotations

import decimal
import logging
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, override

from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    PrepareProfilesRequest,
    PrepareProfilesSuccess,
    ProfileSourceKind,
    VolumeProfileSource,
)
from app.contracts.data.ports import PrepareProfilesCapability
from app.services.data.profile_source_preparation.config import (
    ProfileSourcePreparationConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_MIN_COVERAGE_RATIO = 0.95
_DEFAULT_FALLBACK_STEP = Decimal("0.01")


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _format_decimal(val: str | float | Decimal) -> str:
    """Format a decimal value to match the canonical DecimalValue grammar.

    Args:
        val: Input number or decimal string.

    Returns:
        Canonical decimal string without trailing zeros.
    """
    dec = Decimal(str(val))
    if dec == 0:
        return "0"
    s = f"{dec:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


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


def _validate_identifiers(
    data_version_id: str,
    session_version_id: str,
    require_session_alignment: bool,
) -> tuple[list[ValidationIssue], bool]:
    """Validate UUID identifiers for series and session boundaries.

    Args:
        data_version_id: Data series version UUID.
        session_version_id: Session boundary version UUID.
        require_session_alignment: Whether session alignment is required.

    Returns:
        Tuple of validation issues list and boolean sufficiency flag.
    """
    issues: list[ValidationIssue] = []
    sufficient = True

    if not _is_valid_uuid(str(data_version_id)):
        issues.append(
            ValidationIssue(
                path=("data_version_id",),
                code="DATA_VERSION_INVALID",
                message=f"data_version_id '{data_version_id}' is not a valid UUID.",
            )
        )
        sufficient = False

    if not _is_valid_uuid(str(session_version_id)):
        if require_session_alignment:
            issues.append(
                ValidationIssue(
                    path=("session_version_id",),
                    code="SESSION_BOUNDARY_MISSING",
                    message="Session boundary version ID is invalid or missing.",
                )
            )
            sufficient = False
        else:
            issues.append(
                ValidationIssue(
                    path=("session_version_id",),
                    code="SESSION_BOUNDARY_UNALIGNED",
                    message=(
                        "Session boundary is unaligned; using unsegmented window."
                    ),
                )
            )

    return issues, sufficient


def _validate_source_kind(source_kind: str) -> tuple[list[ValidationIssue], bool]:
    """Validate source granularity kind.

    Args:
        source_kind: Declared granularity string.

    Returns:
        Tuple of validation issues list and boolean sufficiency flag.
    """
    if source_kind in ("TICK", "LOWER_GRANULARITY"):
        return [], True

    issue = ValidationIssue(
        path=("source_kind",),
        code="INVALID_SOURCE_KIND",
        message=(f"source_kind '{source_kind}' must be 'TICK' or 'LOWER_GRANULARITY'."),
    )
    return [issue], False


def _validate_price_step(
    price_step: str | Decimal,
    min_price_step: Decimal,
) -> tuple[list[ValidationIssue], bool, Decimal]:
    """Validate price step magnitude and precision.

    Args:
        price_step: Proposed price step increment.
        min_price_step: Minimum allowable precision.

    Returns:
        Tuple of issues list, boolean sufficiency flag, and parsed Decimal step.
    """
    issues: list[ValidationIssue] = []
    try:
        step_dec = Decimal(str(price_step))
        if step_dec <= Decimal(0):
            issues.append(
                ValidationIssue(
                    path=("price_step",),
                    code="PRICE_STEP_NON_POSITIVE",
                    message="Price step must be strictly greater than zero.",
                )
            )
            return issues, False, _DEFAULT_FALLBACK_STEP
        if step_dec < min_price_step:
            issues.append(
                ValidationIssue(
                    path=("price_step",),
                    code="PRICE_STEP_TOO_SMALL",
                    message=(
                        f"Price step {step_dec} is below minimum supported "
                        f"precision {min_price_step}."
                    ),
                )
            )
            return issues, False, step_dec
        return issues, True, step_dec
    except (ValueError, decimal.InvalidOperation) as exc:
        issues.append(
            ValidationIssue(
                path=("price_step",),
                code="PRICE_STEP_MALFORMED",
                message=f"Price step could not be parsed as decimal: {exc}",
            )
        )
        return issues, False, _DEFAULT_FALLBACK_STEP


def _validate_bin_count(
    bin_count: int | None,
    max_bin_count: int,
) -> tuple[list[ValidationIssue], bool]:
    """Validate optional explicit bin count bounds.

    Args:
        bin_count: Optional bin count integer.
        max_bin_count: Upper bound limit.

    Returns:
        Tuple of validation issues list and boolean sufficiency flag.
    """
    if bin_count is None:
        return [], True

    if bin_count < 1:
        issue = ValidationIssue(
            path=("bin_count",),
            code="BIN_COUNT_INVALID",
            message="bin_count must be >= 1.",
        )
        return [issue], False

    if bin_count > max_bin_count:
        issue = ValidationIssue(
            path=("bin_count",),
            code="BIN_COUNT_EXCEEDED",
            message=(
                f"bin_count {bin_count} exceeds maximum allowed limit "
                f"of {max_bin_count}."
            ),
        )
        return [issue], False

    return [], True


def _validate_coverage_ratio(
    sample_coverage_ratio: float | None,
) -> tuple[list[ValidationIssue], bool]:
    """Validate measured session coverage ratio against sufficiency threshold.

    Args:
        sample_coverage_ratio: Optional measured sample coverage ratio.

    Returns:
        Tuple of validation issues list and boolean sufficiency flag.
    """
    if sample_coverage_ratio is None:
        return [], True

    if sample_coverage_ratio < 0.0 or sample_coverage_ratio > 1.0:
        issue = ValidationIssue(
            path=("sample_coverage_ratio",),
            code="COVERAGE_RATIO_OUT_OF_BOUNDS",
            message="sample_coverage_ratio must be between 0.0 and 1.0.",
        )
        return [issue], False

    if sample_coverage_ratio < _MIN_COVERAGE_RATIO:
        issue = ValidationIssue(
            path=("sample_coverage_ratio",),
            code="COVERAGE_INCOMPLETE",
            message=(
                f"Sample coverage ratio ({sample_coverage_ratio:.2%}) is "
                f"below sufficiency threshold ({_MIN_COVERAGE_RATIO:.0%})."
            ),
        )
        return [issue], False

    return [], True


def data_validate_profile_source(
    data_version_id: str,
    source_kind: str,
    session_version_id: str,
    price_step: str | Decimal,
    bin_count: int | None = None,
    *,
    min_price_step: Decimal = Decimal("0.00000001"),
    max_bin_count: int = 10_000,
    require_session_alignment: bool = True,
    sample_coverage_ratio: float | None = None,
) -> VolumeProfileSource:
    """Validate Volume Profile / TPO source preparation requirements.

    Args:
        data_version_id: Identifier of underlying market data series version.
        source_kind: Data granularity kind (TICK or LOWER_GRANULARITY).
        session_version_id: Identifier of trading session boundaries.
        price_step: Price bin step increment.
        bin_count: Optional explicit number of price bins.
        min_price_step: Minimum allowable price step precision.
        max_bin_count: Maximum allowable price bin count.
        require_session_alignment: Whether session boundaries are mandatory.
        sample_coverage_ratio: Optional measured sample coverage ratio.

    Returns:
        Validated VolumeProfileSource instance.
    """
    issues: list[ValidationIssue] = []
    is_sufficient = True

    id_issues, id_ok = _validate_identifiers(
        data_version_id, session_version_id, require_session_alignment
    )
    issues.extend(id_issues)
    is_sufficient = is_sufficient and id_ok

    kind_issues, kind_ok = _validate_source_kind(source_kind)
    issues.extend(kind_issues)
    is_sufficient = is_sufficient and kind_ok

    step_issues, step_ok, step_dec = _validate_price_step(price_step, min_price_step)
    issues.extend(step_issues)
    is_sufficient = is_sufficient and step_ok

    bin_issues, bin_ok = _validate_bin_count(bin_count, max_bin_count)
    issues.extend(bin_issues)
    is_sufficient = is_sufficient and bin_ok

    cov_issues, cov_ok = _validate_coverage_ratio(sample_coverage_ratio)
    issues.extend(cov_issues)
    is_sufficient = is_sufficient and cov_ok

    canonical_step = _format_decimal(step_dec) if step_dec > 0 else "0.01"
    valid_source_kind: ProfileSourceKind = (
        "LOWER_GRANULARITY" if source_kind == "LOWER_GRANULARITY" else "TICK"
    )
    resolved_data_id = (
        data_version_id if _is_valid_uuid(str(data_version_id)) else _generate_uuid7()
    )
    resolved_session_id = (
        session_version_id
        if _is_valid_uuid(str(session_version_id))
        else _generate_uuid7()
    )

    return VolumeProfileSource(
        source_id=_generate_uuid7(),
        data_version_id=resolved_data_id,
        source_kind=valid_source_kind,
        session_version_id=resolved_session_id,
        price_step=canonical_step,
        bin_count=bin_count,
        coverage_diagnostics=tuple(issues),
        is_sufficient=is_sufficient,
        schema_version=1,
    )


class PrepareProfilesService(PrepareProfilesCapability):
    """Domain service implementation for Volume Profile Source Preparation."""

    def __init__(
        self,
        config: ProfileSourcePreparationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the profile source preparation service.

        Args:
            config: Runtime configuration for source preparation.
            event_bus: Optional kernel event bus for domain event dispatching.
        """
        self.config = config or ProfileSourcePreparationConfig()
        self.event_bus = event_bus

    @override
    async def prepare_profiles(
        self,
        request: PrepareProfilesRequest,
    ) -> PrepareProfilesSuccess | DataFailure:
        """Validate volume-profile source declarations.

        Args:
            request: Volume-profile source validation request.

        Returns:
            The validated source with sufficiency evidence on success,
            otherwise a structured data failure.
        """
        if getattr(request, "operation", None) != "VALIDATE_SOURCE":
            return DataFailure(
                request_id=request.request_id,
                code="DATA_VALIDATION_FAILED",
                problem=ProblemDetails(
                    type="urn:error:haruquant:data:operation-unsupported",
                    title="Unsupported Operation",
                    status=400,
                    code="DATA_VALIDATION_FAILED",
                    detail=(
                        f"Operation '{request.operation}' is not supported by "
                        "PrepareProfilesCapability."
                    ),
                    request_id=request.request_id,
                ),
            )

        source = data_validate_profile_source(
            data_version_id=request.data_version_id,
            source_kind=request.source_kind,
            session_version_id=request.session_version_id,
            price_step=request.price_step,
            bin_count=request.bin_count,
            min_price_step=self.config.min_price_step,
            max_bin_count=self.config.max_bin_count,
            require_session_alignment=self.config.require_session_alignment,
        )

        return PrepareProfilesSuccess(
            request_id=request.request_id,
            source=source,
            outcome="SUCCESS",
            result_version=1,
            schema_version=1,
        )


async def main() -> None:
    """Execute the profile source preparation usage demonstration harness."""
    from app.services.data.profile_source_preparation._usage import (
        main as _usage_main,
    )

    await _usage_main()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
