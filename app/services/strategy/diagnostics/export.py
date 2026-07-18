"""Safe bounded Strategy diagnostics export."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from app.services.strategy.contracts.models import (  # noqa: TC001
    JsonValue,
    StrategyExecutionContext,
)
from app.services.strategy.contracts.outcomes import StrategyOutcome, failure, success
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.diagnostics.models import StrategyDiagnostics
from app.utils import RedactionPolicy, canonical_json, logger, redact_mapping_value


def export_strategy_diagnostics(
    context: StrategyExecutionContext,
    facts: Mapping[str, JsonValue],
) -> StrategyOutcome[StrategyDiagnostics]:
    """Redact, bound, and export diagnostic facts.

    Args:
        context: Exact deterministic evaluation context.
        facts: JSON-compatible diagnostic facts. Reserved identity/status keys
            are consumed into the typed diagnostic fields.

    Returns:
        A schema-valid diagnostic outcome or a bounded deterministic error.
    """
    logger.info("Exporting bounded Strategy diagnostics")
    try:
        redacted = redact_mapping_value(
            facts,
            RedactionPolicy(
                max_text_length=context.max_diagnostic_bytes,
                max_depth=16,
                max_items=1_000,
            ),
        )
        if not isinstance(redacted.value, dict):
            logger.error("Strategy redaction returned an invalid mapping")
            return failure(
                StrategyErrorCode.INTERNAL_ERROR,
                "diagnostic export failed",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )
        safe = redacted.value
        diagnostics = StrategyDiagnostics(
            status=cast(
                "Literal['READY', 'NEUTRAL', 'PROPOSED', 'FAILED']",
                str(safe.pop("status", "READY")),
            ),
            strategy_id=str(safe.pop("strategy_id", "unknown")),
            strategy_version=str(safe.pop("strategy_version", "unknown")),
            config_hash=_optional_text(safe.pop("config_hash", None)),
            data_checksum=_optional_text(safe.pop("data_checksum", None)),
            request_id=context.request_id,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
            decision_timestamp=context.decision_timestamp,
            error_code=_optional_text(safe.pop("error_code", None)),
            safe_details=safe,
            dependency_health=context.dependency_status,
            metrics={},
            redacted_paths=redacted.redacted_paths,
            truncated_paths=redacted.truncated_paths,
            payload_bytes=0,
        )
        encoded = canonical_json(diagnostics.model_dump(mode="json"))
        payload_size = len(encoded.encode("utf-8"))
        if payload_size > context.max_diagnostic_bytes:
            return failure(
                StrategyErrorCode.RESOURCE_LIMIT_EXCEEDED,
                "diagnostic payload exceeds the approved resource budget",
                request_id=context.request_id,
                correlation_id=context.correlation_id,
            )
        return success(diagnostics.model_copy(update={"payload_bytes": payload_size}))
    except (TypeError, ValueError) as error:
        logger.warning("Strategy diagnostic export failed: %s", type(error).__name__)
        return failure(
            StrategyErrorCode.INTERNAL_ERROR,
            "diagnostic export failed",
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )


def _optional_text(value: object) -> str | None:
    """Normalize an optional diagnostic scalar to text.

    Args:
        value: Candidate scalar.

    Returns:
        ``None`` or bounded string form.
    """
    logger.debug("Normalizing optional Strategy diagnostic text")
    return None if value is None else str(value)


__all__ = ["export_strategy_diagnostics"]
