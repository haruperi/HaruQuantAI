"""Function-only construction and inspection for Trading-owned contracts."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

from app.services.trading.contracts.errors import TradingError
from app.services.trading.contracts.models import (
    TRADING_CONTRACT_VERSION,
    ClosedPositionRecord,
    ExecutionEvidenceReport,
    ExecutionReceipt,
    JsonValue,
    OrderIntent,
    OrderIntentV2,
    PortfolioRebalanceExecutionRequest,
    TradeRecord,
    TradingRequest,
    TradingRequestV2,
    TradingRoute,
)
from app.utils import canonical_json, to_json_safe


def get_trading_contract_version() -> str:
    """Return the canonical Trading contract version.

    Returns:
        Current Trading contract version.
    """
    return TRADING_CONTRACT_VERSION


def get_trading_route(value: str) -> TradingRoute:
    """Resolve one canonical Trading route.

    Args:
        value: Registered Trading route value.

    Returns:
        Internal canonical Trading route.
    """
    return TradingRoute(value.lower())


def create_trading_request(**values: object) -> TradingRequest:
    """Construct one validated Trading request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal Trading request.
    """
    return TradingRequest.model_validate(values)


def create_order_intent(**values: object) -> OrderIntent:
    """Construct one validated order intent.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal order intent.
    """
    return OrderIntent.model_validate(values)


def _validate_provider_policies(
    provider_specification: object,
    fill_policy: object,
    time_policy: object,
) -> str:
    """Validate explicit policies against one exact opaque provider revision.

    Returns:
        Exact provider-specification checksum.

    Raises:
        TypeError: If provider revision evidence has an invalid type.
        ValueError: If either policy is unsupported.
    """
    from app.services.brokers import get_provider_specification_snapshot_field

    filling_modes = get_provider_specification_snapshot_field(
        provider_specification, "filling_modes"
    )
    expiration_modes = get_provider_specification_snapshot_field(
        provider_specification, "expiration_modes"
    )
    checksum = get_provider_specification_snapshot_field(
        provider_specification, "checksum"
    )
    if not isinstance(filling_modes, (tuple, list)) or fill_policy not in filling_modes:
        raise ValueError("fill_policy is unsupported by provider specification")
    if (
        not isinstance(expiration_modes, (tuple, list))
        or time_policy not in expiration_modes
    ):
        raise ValueError("time_policy is unsupported by provider specification")
    if not isinstance(checksum, str):
        raise TypeError("provider specification checksum is invalid")
    return checksum


def create_trading_request_v2(
    *, provider_specification: object, **values: object
) -> TradingRequestV2:
    """Construct a provider-bound Trading request v2.

    Args:
        provider_specification: Exact opaque Brokers snapshot revision.
        **values: Complete v2 request fields including both policy dimensions.

    Returns:
        Immutable validated Trading request v2.
    """
    checksum = _validate_provider_policies(
        provider_specification, values.get("fill_policy"), values.get("time_policy")
    )
    return TradingRequestV2.model_validate(
        {**values, "provider_specification_checksum": checksum}
    )


def create_order_intent_v2(
    *, provider_specification: object, **values: object
) -> OrderIntentV2:
    """Construct a provider-bound executable order intent v2.

    Returns:
        Immutable validated order intent v2.
    """
    checksum = _validate_provider_policies(
        provider_specification, values.get("fill_policy"), values.get("time_policy")
    )
    return OrderIntentV2.model_validate(
        {**values, "provider_specification_checksum": checksum}
    )


_LEGACY_POLICY_PROFILES = {
    "trading-order-policy-legacy-v1": ("FOK", "GTC"),
}


def create_legacy_compatible_trading_request(
    *,
    legacy_profile_version: str,
    provider_specification: object,
    **values: object,
) -> TradingRequestV2:
    """Decode v1 material only through an explicit parity-ineligible profile.

    Returns:
        Labelled parity-ineligible v2 request.

    Raises:
        ValueError: If the named legacy profile is unknown.
    """
    try:
        fill_policy, time_policy = _LEGACY_POLICY_PROFILES[legacy_profile_version]
    except KeyError as error:
        raise ValueError("unknown legacy order-policy profile") from error
    material = dict(values)
    material.pop("contract_version", None)
    material.pop("schema_id", None)
    material.pop("time_in_force", None)
    return create_trading_request_v2(
        provider_specification=provider_specification,
        **material,
        fill_policy=fill_policy,
        time_policy=time_policy,
        legacy_compatibility=True,
        canonical_parity_eligible=False,
    )


def build_order_intent(**values: object) -> dict[str, JsonValue]:
    """Build one validated JSON-safe ``OrderIntent v1`` mapping.

    Args:
        **values: Complete order-intent fields.

    Returns:
        Validated JSON-safe contract mapping.

    Raises:
        ValueError: If required operational lineage is absent.
        TypeError: If serialization does not produce a mapping.
    """
    intent = OrderIntent.model_validate(values)
    lineage = (
        intent.trade_plan_id,
        intent.trade_plan_version,
        intent.risk_decision_version,
        intent.policy_version,
        intent.profile_version,
    )
    if any(value is None for value in lineage):
        raise ValueError("operational OrderIntent requires complete versioned lineage")
    safe = to_json_safe(intent.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("OrderIntent transport must be a mapping")
    return safe


def parse_order_intent(value: Mapping[str, object]) -> OrderIntent:
    """Parse one validated JSON-safe ``OrderIntent v1`` mapping.

    Args:
        value: Candidate contract mapping.

    Returns:
        Validated internal order intent.
    """
    return OrderIntent.model_validate(build_order_intent(**dict(value)))


def create_execution_receipt(**values: object) -> ExecutionReceipt:
    """Construct one validated execution receipt.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal execution receipt.
    """
    return ExecutionReceipt.model_validate(values)


def create_trade_record(**values: object) -> TradeRecord:
    """Construct one validated trade record.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal trade record.
    """
    return TradeRecord.model_validate(values)


def create_closed_position_record(**values: object) -> ClosedPositionRecord:
    """Construct one validated immutable closed-position record.

    Args:
        **values: Exact broker and strategy evidence. ``evidence_hash`` is derived.

    Returns:
        Validated internal closed-position record.

    Raises:
        ValueError: If a caller attempts to supply a digest or evidence is invalid.
    """
    if "evidence_hash" in values:
        raise ValueError("evidence_hash is derived from closed-position evidence")
    material = dict(values)
    digest = sha256(canonical_json(material).encode("utf-8")).hexdigest()
    return ClosedPositionRecord.model_validate({**material, "evidence_hash": digest})


def create_portfolio_rebalance_execution_request(
    **values: object,
) -> PortfolioRebalanceExecutionRequest:
    """Construct one validated portfolio-rebalance execution request.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal portfolio-rebalance execution request.
    """
    return PortfolioRebalanceExecutionRequest.model_validate(values)


def create_execution_evidence_report(**values: object) -> ExecutionEvidenceReport:
    """Construct one validated execution-evidence report.

    Args:
        **values: Contract field values.

    Returns:
        Validated internal execution-evidence report.
    """
    return ExecutionEvidenceReport.model_validate(values)


def create_trading_error(
    code: str,
    details: str,
    *,
    trace_context: Mapping[str, JsonValue] | None = None,
) -> TradingError:
    """Construct one redacted Trading exception.

    Args:
        code: Registered Trading error code.
        details: Secret-safe diagnostic detail.
        trace_context: Optional secret-safe trace context.

    Returns:
        Internal Trading exception.
    """
    return TradingError(code, details, trace_context=trace_context)


def is_trading_error(value: object) -> bool:
    """Return whether a value is the internal Trading exception.

    Args:
        value: Value to inspect.

    Returns:
        True only for Trading exceptions.
    """
    return isinstance(value, TradingError)


def is_execution_receipt(value: object) -> bool:
    """Return whether a value is an internal execution receipt.

    Args:
        value: Value to inspect.

    Returns:
        True only for execution receipts.
    """
    return isinstance(value, ExecutionReceipt)


__all__ = [
    "build_order_intent",
    "create_closed_position_record",
    "create_execution_evidence_report",
    "create_execution_receipt",
    "create_order_intent",
    "create_portfolio_rebalance_execution_request",
    "create_trade_record",
    "create_trading_error",
    "create_trading_request",
    "get_trading_contract_version",
    "get_trading_route",
    "is_execution_receipt",
    "is_trading_error",
    "parse_order_intent",
]
