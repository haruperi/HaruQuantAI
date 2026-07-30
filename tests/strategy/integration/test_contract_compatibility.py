"""Producer/consumer compatibility evidence for Strategy-owned contracts."""

import json
from datetime import UTC, datetime

import pytest
from app.services.strategy import (
    build_trade_intent,
    create_strategy_config,
    create_strategy_mutation_result,
    create_strategy_parameter_update_request,
    create_strategy_proposal_evaluation_request,
    create_strategy_proposal_evaluation_result,
    create_strategy_ref,
    create_strategy_registration_request,
    create_trade_intent_value,
    get_strategy_environment,
)
from app.utils import get_logger
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
from tests.strategy.unit.test_proposal_contracts import make_proposal_request

logger = get_logger(__name__)


def make_parameter_update() -> object:
    """Build one governed parameter-update command.

    Returns:
        A complete parameter-update request.
    """
    logger.debug("Building Strategy parameter update compatibility fixture")
    parameters = {"period": 7}
    return create_strategy_parameter_update_request(
        command_id="command-config-compat",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters=parameters,
        principal_id="builder",
        reason="compatibility fixture",
        ref=create_strategy_ref(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            environment=get_strategy_environment("RESEARCH"),
            request_id=REQ,
            correlation_id=COR,
        ),
        config=create_strategy_config(
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


def test_registered_contract_identity_matches_project_registry() -> None:
    """Verify root constructors return the documented immutable wire contracts."""
    logger.debug("Testing Strategy constructor contract identities")
    registration = make_registration()
    update = make_parameter_update()
    mutation = _mutation_result()
    intent = build_trade_intent(make_decision(), make_context(), 0).data
    assert intent is not None
    assert {
        registration.schema_id,
        update.schema_id,
        mutation.schema_id,
        intent.schema_id,
    } == {
        "strategy.registration_request.v1",
        "strategy.parameter_update_request.v1",
        "strategy.mutation_result.v1",
        "strategy.trade_intent.v1",
    }


def test_registration_request_carries_required_consumer_fields() -> None:
    """Verify the registration command exposes every documented field."""
    logger.debug("Testing create_strategy_registration_request required fields")
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
    assert required <= set(make_registration().model_dump())


def test_parameter_update_request_carries_required_consumer_fields() -> None:
    """Verify the parameter-update command exposes every documented field."""
    logger.debug("Testing create_strategy_parameter_update_request required fields")
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
    assert required <= set(make_parameter_update().model_dump())


def test_proposal_contracts_round_trip_for_external_consumers() -> None:
    """Verify proposal intake request/result wire values survive reconstruction."""
    logger.debug("Testing Strategy proposal contract compatibility")
    request = make_proposal_request()
    rebuilt_request = create_strategy_proposal_evaluation_request(
        **request.model_dump(
            mode="python",
            exclude={"evaluation_request_id", "idempotency_key"},
        )
    )
    assert rebuilt_request == request
    result = create_strategy_proposal_evaluation_result(
        evaluation_id="proposal-result-compatibility",
        evaluation_request_id=request.evaluation_request_id,
        status="rejected",
        reason_codes=("AUTHORIZATION_DENIED",),
        source_proposal_id=request.source_proposal_id,
        source_task_id=request.source_task_id,
        source_content_hash=request.source_content_hash,
        strategy_id=request.strategy_id,
        strategy_version=request.strategy_version,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )
    rebuilt_result = create_strategy_proposal_evaluation_result(
        **json.loads(result.model_dump_json())
    )
    assert rebuilt_result == result


def test_trade_intent_carries_required_risk_consumer_fields() -> None:
    """Verify Risk receives every documented create_trade_intent_value lineage field."""
    logger.debug("Testing create_trade_intent_value required consumer fields")
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
    outcome = build_trade_intent(make_decision(), make_context(), 0)
    assert outcome.data is not None
    assert required <= set(outcome.data.model_dump())


def test_trade_intent_round_trips_for_downstream_consumers() -> None:
    """Verify Risk can serialize and rebuild an intent without loss."""
    logger.debug("Testing create_trade_intent_value producer/consumer round trip")
    outcome = build_trade_intent(make_decision(), make_context(), 0)
    assert outcome.data is not None
    rebuilt = create_trade_intent_value(**json.loads(outcome.data.model_dump_json()))
    assert rebuilt == outcome.data
    assert rebuilt.contract_version == "v1"


def test_registered_commands_round_trip_for_receiver() -> None:
    """Verify Strategy can rebuild submitted commands from their wire form."""
    logger.debug("Testing Strategy command producer/consumer round trip")
    registration = make_registration()
    rebuilt_registration = create_strategy_registration_request(
        **json.loads(registration.model_dump_json())
    )
    assert rebuilt_registration == registration

    update = make_parameter_update()
    rebuilt_update = create_strategy_parameter_update_request(
        **json.loads(update.model_dump_json())
    )
    assert rebuilt_update == update


def test_mutation_result_round_trips_for_ui_risk_and_portfolio() -> None:
    """Verify the published mutation result survives a wire round trip."""
    logger.debug("Testing create_strategy_mutation_result round trip")
    mutation = _mutation_result()
    rebuilt = create_strategy_mutation_result(**json.loads(mutation.model_dump_json()))
    assert rebuilt == mutation


def _mutation_result() -> object:
    """Build one rejected immutable mutation result for wire-boundary checks."""
    return create_strategy_mutation_result(
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


def test_unknown_wire_field_is_rejected_not_ignored() -> None:
    """Verify an added upstream field fails closed instead of being dropped."""
    logger.debug("Testing Strategy contract forward-compatibility policy")
    payload = make_registration().model_dump(mode="json")
    payload["unexpected_future_field"] = "value"
    with pytest.raises(ValidationError):
        create_strategy_registration_request(**payload)


def test_completed_timestamps_are_utc_aware() -> None:
    """Verify published mutation truth carries aware UTC completion time."""
    logger.debug("Testing Strategy mutation timestamp policy")
    mutation = create_strategy_mutation_result(
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
