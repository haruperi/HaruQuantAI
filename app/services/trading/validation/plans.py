"""Side-effect-free deterministic Trading execution-plan construction."""

from hashlib import sha256
from typing import Any, Literal

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json
from app.services.trading.contracts import OrderIntent, TradingError, TradingRequest
from app.services.trading.contracts.models import OrderIntentV2, TradingRequestV2
from app.services.trading.contracts.responses import success_trading_response
from app.services.trading.validation.readiness import (
    ReadinessAssessment,  # noqa: TC001 - runtime annotation and model resolution
)

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)


def _build_execution_plan_value(
    request: TradingRequest,
    readiness: ReadinessAssessment,
) -> OrderIntent:
    """Build one canonical OrderIntent from passed readiness evidence.

    Args:
        request: Validated canonical request.
        readiness: Complete mandatory readiness assessment.

    Returns:
        Deterministic exact-size executable order intent.

    Raises:
        TradingError: If readiness failed or executable order material is absent.
    """
    logger.info("Building deterministic Trading execution plan")
    if not readiness.passed:
        raise TradingError(
            "GATE_BLOCKED",
            "Execution readiness did not pass",
            trace_context={"request_id": request.request_id},
        )
    if request.quantity is None or request.symbol is None or request.side is None:
        raise TradingError(
            "INVALID_REQUEST",
            "Execution plan requires symbol side and Risk-approved size",
            trace_context={"request_id": request.request_id},
        )
    material = {
        "contract_version": "v1",
        "schema_id": "trading.order_intent.v1",
        "request_id": request.request_id,
        "workflow_id": request.workflow_id,
        "correlation_id": request.correlation_id,
        "route": request.route,
        "provider_id": request.provider_id,
        "account_id": request.account_id,
        "simulation_session_id": request.simulation_session_id,
        "strategy_id": request.strategy_id,
        "strategy_version": request.strategy_version,
        "source_intent_id": request.intent_id,
        "symbol": request.symbol,
        "action": request.action,
        "side": request.side,
        "order_type": request.order_type,
        "quantity_unit": request.quantity_unit,
        "approved_volume": request.quantity,
        "price": request.price,
        "stop_price": request.stop_price,
        "stop_loss": request.stop_loss,
        "take_profit": request.take_profit,
        "time_in_force": request.time_in_force,
        "expiration": request.expiration,
        "target_broker_order_id": request.target_broker_order_id,
        "target_broker_position_id": request.target_broker_position_id,
        "canonical_material_version": request.canonical_material_version,
        "risk_decision_id": request.risk_decision_id,
        "action_policy_verdict_id": request.action_policy_verdict_id,
        "approval_token_ref": request.approval_token_ref,
        "created_at": request.system_time,
        "valid_until": request.valid_until,
    }
    digest = sha256(canonical_json(material).encode("utf-8")).hexdigest()
    client_order_digest = sha256(
        canonical_json(
            {
                "request_id": request.request_id,
                "idempotency_key": request.idempotency_key,
                "material_hash": digest,
            }
        ).encode("utf-8")
    ).hexdigest()
    intent_values: dict[str, object] = {
        "client_order_id": f"trd-{client_order_digest}",
        "request_id": request.request_id,
        "workflow_id": request.workflow_id,
        "correlation_id": request.correlation_id,
        "route": request.route,
        "provider_id": request.provider_id,
        "account_id": request.account_id,
        "simulation_session_id": request.simulation_session_id,
        "strategy_id": request.strategy_id,
        "strategy_version": request.strategy_version,
        "source_intent_id": request.intent_id,
        "symbol": request.symbol,
        "action": request.action,
        "side": request.side,
        "order_type": request.order_type,
        "quantity_unit": request.quantity_unit,
        "approved_volume": request.quantity,
        "risk_approved_volume": request.quantity,
        "price": request.price,
        "stop_price": request.stop_price,
        "stop_loss": request.stop_loss,
        "take_profit": request.take_profit,
        "time_in_force": request.time_in_force,
        "expiration": request.expiration,
        "target_broker_order_id": request.target_broker_order_id,
        "target_broker_position_id": request.target_broker_position_id,
        "idempotency_hash": digest,
        "canonical_material_version": request.canonical_material_version,
        "risk_decision_id": request.risk_decision_id,
        "action_policy_verdict_id": request.action_policy_verdict_id,
        "approval_token_ref": request.approval_token_ref,
        "created_at": request.system_time,
        "valid_until": request.valid_until,
    }
    if isinstance(request, TradingRequestV2):
        intent_values.update(
            fill_policy=request.fill_policy,
            time_policy=request.time_policy,
            provider_specification_checksum=request.provider_specification_checksum,
            legacy_compatibility=request.legacy_compatibility,
            canonical_parity_eligible=request.canonical_parity_eligible,
        )
        return OrderIntentV2.model_validate(intent_values)
    return OrderIntent.model_validate(intent_values)


def build_execution_plan(
    request: TradingRequest,
    readiness: ReadinessAssessment,
) -> StandardResponse[OrderIntent]:
    """Build a deterministic execution plan in standard response data.

    Args:
        request: Governed trading request envelope.
        readiness: Validated readiness assessment object.

    Returns:
        Standard response containing the executable intent or an error.
    """
    try:
        value = _build_execution_plan_value(request, readiness)
    except TradingError as error:
        from typing import cast

        from app.services.trading.contracts.errors import map_trading_error

        return cast(
            "StandardResponse[OrderIntent]",
            map_trading_error(
                error,
                {
                    "operation": "trading.build_execution_plan",
                    "request_id": request.request_id,
                    "correlation_id": request.correlation_id,
                },
            ),
        )
    return success_trading_response(
        value,
        operation="trading.build_execution_plan",
        message="Trading execution plan built",
        risk_level="high",
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        read_only=True,
    )


__all__ = ["build_execution_plan"]
