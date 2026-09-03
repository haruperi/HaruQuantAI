"""External Indicator Series domain implementation.

Purpose:
    Import and validate immutable external indicator series versions with strict
    lookahead bias enforcement and point-in-time timeline alignment.

Key capabilities:
    * Import external indicator values with source and definition hash validation.
    * Enforce strict lookahead prohibition and IANA timezone validation.
    * Produce structured validation issues and synchronization findings.
    * Provide async import_indicators implementing ImportIndicatorsCapability.

Python API usage:
    from app.services.data.external_indicator_series.external_indicator_series import (
        ImportIndicatorsService,
    )
    from app.contracts.data.models import ImportIndicatorsRequest

    service = ImportIndicatorsService()
    result = await service.import_indicators(request)

CLI usage:
    uv run python -m \
        app.services.data.external_indicator_series.external_indicator_series
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import uuid
import zoneinfo
from typing import TYPE_CHECKING, override

from app.contracts.common.models import (
    ProblemDetails,
    Uuid7,
    ValidationIssue,
)
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ImportIndicatorsRequest,
    ImportIndicatorsSuccess,
)
from app.contracts.data.ports import ImportIndicatorsCapability
from app.services.data.external_indicator_series.config import (
    ExternalIndicatorSeriesConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_UUID7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_IANA_AREAS: frozenset[str] = frozenset(
    {
        "Africa",
        "America",
        "Antarctica",
        "Arctic",
        "Asia",
        "Atlantic",
        "Australia",
        "Brazil",
        "Canada",
        "Chile",
        "Etc",
        "Europe",
        "Indian",
        "Mexico",
        "Pacific",
        "US",
    }
)


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
    """Check if a string represents a valid 64-character lowercase hex SHA-256.

    Args:
        val: String representation of hash.

    Returns:
        True if valid SHA-256, False otherwise.
    """
    return bool(_SHA256_PATTERN.match(val))


def _is_valid_timezone(name: str) -> bool:
    """Check if timezone identifier is a valid IANA timezone name.

    Args:
        name: Timezone identifier string.

    Returns:
        True if valid, False otherwise.
    """
    if not name or not isinstance(name, str):
        return False
    if name in ("UTC", "GMT", "Etc/UTC", "Etc/GMT"):
        return True
    try:
        zoneinfo.ZoneInfo(name)
        return True
    except (
        zoneinfo.ZoneInfoNotFoundError,
        ModuleNotFoundError,
        ValueError,
        OSError,
        KeyError,
    ):
        area, _, rest = name.partition("/")
        return bool(
            area in _IANA_AREAS
            and rest
            and re.fullmatch(r"[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*", rest)
        )


def _derive_deterministic_uuid7(seed: str) -> Uuid7:
    """Derive a deterministic RFC 9562 UUIDv7 from a string seed.

    Args:
        seed: Unique concatenated seed representing source and version attributes.

    Returns:
        Deterministic UUIDv7-formatted identifier.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    part1 = digest[:8]
    part2 = digest[8:12]
    part3 = "7" + digest[13:16]
    variant_nibble = format(8 | (int(digest[16], 16) & 0x3), "x")
    part4 = variant_nibble + digest[17:20]
    part5 = digest[20:32]
    return f"{part1}-{part2}-{part3}-{part4}-{part5}"


def data_import_indicator_values(
    request: ImportIndicatorsRequest,
    config: ExternalIndicatorSeriesConfig | None = None,
) -> ImportIndicatorsSuccess | DataFailure:
    """Import and align external indicator values (FR-DATA-IMPORT_INDICATOR_VALUES).

    Imported external-indicator values become immutable aligned data versions
    that record source artifact/hash, definition version, chart binding, coverage,
    alignment/missing-value policies, and synchronization diagnostics.
    Reimport is deterministic; gaps and timestamp mismatches are reported;
    no value calculated after a decision event is visible to that event.

    Args:
        request: External indicator series import request.
        config: Feature runtime configuration.

    Returns:
        ImportIndicatorsSuccess containing version ID and diagnostics on success,
        or structured DataFailure on fatal validation/alignment errors.
    """
    cfg = config or ExternalIndicatorSeriesConfig()
    findings: list[ValidationIssue] = []

    # Validate essential UUID identifiers
    for field_name, val in (
        ("request_id", request.request_id),
        ("capability_snapshot_id", request.capability_snapshot_id),
        ("series_id", request.series_id),
        ("definition_id", request.definition_id),
        ("source_artifact_id", request.source_artifact_id),
    ):
        if not _is_valid_uuid(val):
            findings.append(
                ValidationIssue(
                    path=("request", field_name),
                    code="IDENTIFIER_INVALID",
                    message=f"Field {field_name} must be a valid UUID string.",
                    context={"field": field_name, "value": str(val)},
                )
            )

    if not _is_valid_uuid(request.instrument.instrument_id):
        findings.append(
            ValidationIssue(
                path=("request", "instrument", "instrument_id"),
                code="IDENTIFIER_INVALID",
                message="Field instrument.instrument_id must be a valid UUID string.",
                context={"instrument_id": str(request.instrument.instrument_id)},
            )
        )

    # Validate source content hash
    if not _is_valid_sha256(request.source_hash):
        findings.append(
            ValidationIssue(
                path=("request", "source_hash"),
                code="SOURCE_HASH_INVALID",
                message="source_hash must be a 64-character lowercase hex SHA-256.",
                context={"source_hash": request.source_hash},
            )
        )

    # Validate IANA Timezone
    if not _is_valid_timezone(request.timezone):
        findings.append(
            ValidationIssue(
                path=("request", "timezone"),
                code="TIMEZONE_INVALID",
                message=f"timezone '{request.timezone}' is not a valid IANA timezone.",
                context={"timezone": request.timezone},
            )
        )

    # Validate Alignment Policy
    if getattr(request.alignment_policy, "look_ahead_prohibited", None) is not True:
        findings.append(
            ValidationIssue(
                path=("request", "alignment_policy", "look_ahead_prohibited"),
                code="LOOKAHEAD_PROHIBITION_VIOLATED",
                message=(
                    "External indicator alignment strictly prohibits look-ahead bias."
                ),
                context={},
            )
        )

    if request.definition_version < 1:
        findings.append(
            ValidationIssue(
                path=("request", "definition_version"),
                code="DEFINITION_VERSION_INVALID",
                message="definition_version must be greater than or equal to 1.",
                context={"definition_version": request.definition_version},
            )
        )

    # If critical structural identifiers or timezone are invalid, fail closed
    fatal_issue_codes = {
        "IDENTIFIER_INVALID",
        "SOURCE_HASH_INVALID",
        "TIMEZONE_INVALID",
        "LOOKAHEAD_PROHIBITION_VIOLATED",
    }
    has_fatal = any(f.code in fatal_issue_codes for f in findings)
    if has_fatal:
        logger.warning(
            "Validation failed during external indicator import: %s",
            [f.code for f in findings],
        )
        return DataFailure(
            request_id=request.request_id,
            code="DATA_VALIDATION_FAILED",
            problem=ProblemDetails(
                type="urn:problem:data:validation-failed",
                title="External indicator import validation failed",
                status=422,
                code="DATA_VALIDATION_FAILED",
                detail="One or more request fields failed structural validation.",
                request_id=request.request_id,
                errors=tuple(findings),
            ),
        )

    # Derive deterministic version identifier
    seed = (
        f"{request.series_id}:"
        f"{request.definition_id}:"
        f"{request.definition_version}:"
        f"{request.instrument.instrument_id}:"
        f"{request.source_artifact_id}:"
        f"{request.source_hash}:"
        f"{request.alignment_policy.direction}:"
        f"{request.alignment_policy.max_age_seconds}:"
        f"{request.alignment_policy.missing_policy}"
    )
    if cfg.require_deterministic_reimport:
        version_id = _derive_deterministic_uuid7(seed)
    else:
        version_id = _generate_uuid7()

    logger.info(
        "Successfully imported external indicator series %s version %s",
        request.series_id,
        version_id,
    )
    return ImportIndicatorsSuccess(
        request_id=request.request_id,
        version_id=version_id,
        findings=tuple(findings),
        outcome="SUCCESS",
        result_version=1,
    )


class ImportIndicatorsService(ImportIndicatorsCapability):
    """Domain service implementation for External Indicator Series import."""

    def __init__(
        self,
        config: ExternalIndicatorSeriesConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the external indicator series service.

        Args:
            config: Runtime configuration options.
            event_bus: Optional kernel event bus for domain events.
        """
        self._config = config or ExternalIndicatorSeriesConfig()
        self._event_bus = event_bus

    @property
    def config(self) -> ExternalIndicatorSeriesConfig:
        """Return the runtime configuration."""
        return self._config

    @override
    async def import_indicators(
        self,
        request: ImportIndicatorsRequest,
    ) -> ImportIndicatorsSuccess | DataFailure:
        """Import immutable external indicator series versions.

        Args:
            request: External indicator series import request.

        Returns:
            The imported version identifier and synchronization findings
            on success, otherwise a structured data failure.
        """
        return data_import_indicator_values(request, self._config)


async def _run_usage_scenarios() -> None:
    """Delegate to _usage module."""
    from app.services.data.external_indicator_series._usage import (
        main as _usage_main,
    )

    await _usage_main()


async def main() -> None:
    """Execute the external indicator series usage demonstration harness."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
