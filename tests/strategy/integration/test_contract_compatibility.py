"""Producer/consumer compatibility evidence for Strategy-owned contracts."""

from datetime import UTC, datetime

import pytest
from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyMutationResult,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    TradeIntent,
    build_trade_intent,
)
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    WF,
    make_context,
    make_decision,
)


def make_parameter_update() -> StrategyParameterUpdateRequest:
    """Build one governed parameter-update command.

    Returns:
        A complete parameter-update request.
    """
    logger.debug("Building Strategy parameter update compatibility fixture")
    parameters = {"period": 7}
    return StrategyParameterUpdateRequest(
        command_id="command-config-compat",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters=parameters,
        principal_id="builder",
        reason="compatibility fixture",
        ref=StrategyRef(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            environment=StrategyEnvironment.RESEARCH,
            request_id=REQ,
            correlation_id=COR,
        ),
        config=StrategyConfig(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters=parameters,
            request_id=REQ,
        ),
        authorization_ref="approval-config-compat",
        requested_at=NOW,
        request_id=REQ,
        correlation_id=COR,
    )


_REGISTERED_SCHEMA_IDS = {
    StrategyRegistrationRequest: "strategy.registration_request.v1",
    StrategyParameterUpdateRequest: "strategy.parameter_update_request.v1",
    StrategyMutationResult: "strategy.mutation_result.v1",
    TradeIntent: "strategy.trade_intent.v1",
}


@pytest.mark.parametrize("contract", list(_REGISTERED_SCHEMA_IDS))
def test_registered_contract_identity_matches_project_registry(
    contract: type,
) -> None:
    """Verify contract_version and schema_id match docs/PROJECT.md exactly.

    Args:
        contract: One registered Strategy-owned contract class.
    """
    logger.debug("Testing registered Strategy contract identity")
    fields = contract.model_fields
    assert fields["contract_version"].default == "v1"
    assert fields["schema_id"].default == _REGISTERED_SCHEMA_IDS[contract]


@pytest.mark.parametrize("contract", list(_REGISTERED_SCHEMA_IDS))
def test_registered_contract_rejects_unknown_fields(contract: type) -> None:
    """Verify every registered contract forbids undeclared wire fields.

    Args:
        contract: One registered Strategy-owned contract class.
    """
    logger.debug("Testing registered Strategy contract extra-field policy")
    assert contract.model_config.get("extra") == "forbid"
    assert contract.model_config.get("frozen") is True


def test_registration_request_carries_required_consumer_fields() -> None:
    """Verify the registration command exposes every documented field."""
    logger.debug("Testing StrategyRegistrationRequest required fields")
    required = {
        "contract_version",
        "schema_id",
        "command_id",
        "strategy_id",
        "strategy_version",
        "module_path",
        "manifest",
        "config_schema",
        "source_hash",
        "artifact_hash",
        "dependency_hash",
        "provenance_refs",
        "principal_id",
        "reason",
        "lifecycle_status",
        "authorization_ref",
        "requested_at",
        "request_id",
        "correlation_id",
    }
    assert required <= set(StrategyRegistrationRequest.model_fields)


def test_parameter_update_request_carries_required_consumer_fields() -> None:
    """Verify the parameter-update command exposes every documented field."""
    logger.debug("Testing StrategyParameterUpdateRequest required fields")
    required = {
        "contract_version",
        "schema_id",
        "command_id",
        "strategy_id",
        "strategy_version",
        "parameters",
        "optimization_result_ref",
        "expected_config_hash",
        "principal_id",
        "reason",
        "ref",
        "config",
        "authorization_ref",
        "requested_at",
        "request_id",
        "correlation_id",
    }
    assert required <= set(StrategyParameterUpdateRequest.model_fields)


def test_trade_intent_carries_required_risk_consumer_fields() -> None:
    """Verify Risk receives every documented TradeIntent lineage field."""
    logger.debug("Testing TradeIntent required consumer fields")
    required = {
        "contract_version",
        "schema_id",
        "intent_id",
        "decision_id",
        "idempotency_key",
        "strategy_id",
        "strategy_version",
        "strategy_sequence",
        "symbol",
        "side",
        "intent_type",
        "order_type",
        "limit_price",
        "stop_price",
        "time_in_force",
        "requested_sizing_mode",
        "quantity_hint",
        "signal_timestamp",
        "decision_timestamp",
        "parent_intent_id",
        "stop_loss",
        "take_profit",
        "expiration",
        "allow_partial_fills",
        "min_fill_size",
        "rationale_ref",
        "lineage",
    }
    assert required <= set(TradeIntent.model_fields)


def test_trade_intent_round_trips_for_downstream_consumers() -> None:
    """Verify Risk can serialize and rebuild an intent without loss."""
    logger.debug("Testing TradeIntent producer/consumer round trip")
    outcome = build_trade_intent(make_decision(), make_context(), 0)
    assert outcome.data is not None
    wire = outcome.data.model_dump_json()
    rebuilt = TradeIntent.model_validate_json(wire)
    assert rebuilt == outcome.data
    assert rebuilt.contract_version == "v1"


def test_registered_commands_round_trip_for_receiver() -> None:
    """Verify Strategy can rebuild submitted commands from their wire form."""
    logger.debug("Testing Strategy command producer/consumer round trip")
    registration = make_registration()
    rebuilt_registration = StrategyRegistrationRequest.model_validate_json(
        registration.model_dump_json()
    )
    assert rebuilt_registration == registration

    update = make_parameter_update()
    rebuilt_update = StrategyParameterUpdateRequest.model_validate_json(
        update.model_dump_json()
    )
    assert rebuilt_update == update


def test_mutation_result_round_trips_for_ui_risk_and_portfolio() -> None:
    """Verify the published mutation result survives a wire round trip."""
    logger.debug("Testing StrategyMutationResult round trip")
    mutation = StrategyMutationResult(
        mutation_id="mutation-1",
        mutation_type="REGISTER_VERSION",
        status="REJECTED",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        reason_codes=("LIFECYCLE_NOT_APPROVED",),
        request_id=REQ,
        correlation_id=COR,
        workflow_id=WF,
        completed_at=NOW,
    )
    rebuilt = StrategyMutationResult.model_validate_json(mutation.model_dump_json())
    assert rebuilt == mutation


def test_unknown_wire_field_is_rejected_not_ignored() -> None:
    """Verify an added upstream field fails closed instead of being dropped."""
    logger.debug("Testing Strategy contract forward-compatibility policy")
    payload = make_registration().model_dump(mode="json")
    payload["unexpected_future_field"] = "value"
    with pytest.raises(ValidationError):
        StrategyRegistrationRequest.model_validate(payload)


def test_completed_timestamps_are_utc_aware() -> None:
    """Verify published mutation truth carries aware UTC completion time."""
    logger.debug("Testing Strategy mutation timestamp policy")
    mutation = StrategyMutationResult(
        mutation_id="mutation-2",
        mutation_type="UPDATE_PARAMETERS",
        status="REJECTED",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        request_id=REQ,
        correlation_id=COR,
        workflow_id=WF,
        completed_at=datetime.now(UTC),
    )
    assert mutation.completed_at.tzinfo is not None
