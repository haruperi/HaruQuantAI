"""Focused fail-closed branch tests for Strategy public boundaries."""

from datetime import timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.services.strategy import (
    build_trade_intent,
    create_strategy_checkpoint,
    create_strategy_checkpoint_value,
    create_strategy_config,
    create_strategy_decision,
    create_strategy_diagnostics,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_execution_result,
    create_strategy_manifest,
    create_strategy_mutation_result,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_replay_manifest_value,
    create_strategy_signal,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_trade_intent_value,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    export_strategy_diagnostics,
    list_strategy_versions,
    validate_strategy_checkpoint,
)
from app.services.strategy.contracts._base import (
    _contains_executable_marker,
    _finite_decimal,
    _freeze_json,
    _hash,
    _text,
    _utc,
)
from app.services.strategy.registry.configuration import (
    _apply_schema,
    _matches_rule,
    _within_limits,
)
from app.utils import get_logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import (
    NOW,
    make_auth,
    make_config,
    make_context,
    make_ref,
)

logger = get_logger(__name__)


@pytest.mark.parametrize(
    "factory",
    [
        create_strategy_checkpoint_value,
        create_strategy_config,
        create_strategy_decision,
        create_strategy_diagnostics,
        create_strategy_event,
        create_strategy_execution_context,
        create_strategy_execution_result,
        create_strategy_manifest,
        create_strategy_mutation_result,
        create_strategy_parameter_update_request,
        create_strategy_ref,
        create_strategy_registration_request,
        create_strategy_replay_manifest_value,
        create_strategy_signal,
        create_strategy_signal_evidence,
        create_strategy_validation_policy,
        create_trade_intent_value,
        create_validated_strategy_config,
        create_validated_strategy_ref,
    ],
)
def test_public_value_factories_validate_inputs(factory) -> None:
    """Verify every function-only value constructor invokes model validation."""
    logger.debug("Testing Strategy value factory %s", factory.__name__)
    with pytest.raises(ValidationError):
        factory()


def test_trade_intent_builder_rejects_each_invalid_boundary() -> None:
    """Verify proposal construction fails closed for invalid decision evidence."""
    context = make_context()
    neutral = build_trade_intent(
        create_strategy_decision(
            decision_id="neutral-1",
            sequence=0,
            action="NEUTRAL",
            valid_from=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(minutes=1),
            allow_partial_fills=False,
            rationale_refs=("reason-1",),
            diagnostic_facts={},
            lineage={},
        ),
        context,
        0,
    )
    assert neutral.error is not None
    assert neutral.error.code == "STRATEGY_INVALID_CONFIG"

    proposal = create_strategy_decision(
        decision_id="proposal-1",
        sequence=0,
        action="PROPOSE",
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        requested_sizing_mode="quantity",
        quantity_hint="1",
        valid_from=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        rationale_refs=("reason-1",),
        diagnostic_facts={},
        lineage={"strategy_id": "mean-reversion", "strategy_version": "1.0.0"},
    )
    missing_shape = proposal.model_copy(update={"side": None})
    assert build_trade_intent(missing_shape, context, 0).error is not None
    assert build_trade_intent(proposal, context, 1).error is not None
    future = proposal.model_copy(
        update={"valid_from": context.decision_timestamp + timedelta(seconds=1)}
    )
    assert build_trade_intent(future, context, 0).error is not None
    missing_lineage = proposal.model_copy(update={"lineage": {}})
    assert build_trade_intent(missing_lineage, context, 0).error is not None


def test_diagnostics_export_covers_bounded_failure_paths() -> None:
    """Verify malformed, oversized, and unserializable diagnostics fail closed."""
    context = make_context()
    tiny = context.model_copy(update={"max_diagnostic_bytes": 1})
    oversized = export_strategy_diagnostics(tiny, {"status": "READY", "fact": "value"})
    assert oversized.error is not None
    assert oversized.error.code == "STRATEGY_RESOURCE_LIMIT_EXCEEDED"

    invalid_redaction = SimpleNamespace(
        value=(),
        redacted_paths=(),
        truncated_paths=(),
    )
    with patch(
        "app.services.strategy.diagnostics.export.redact_mapping_value",
        return_value=invalid_redaction,
    ):
        malformed = export_strategy_diagnostics(context, {})
    assert malformed.error is not None
    assert malformed.error.code == "STRATEGY_INTERNAL_ERROR"

    with patch(
        "app.services.strategy.diagnostics.export.canonical_json",
        side_effect=ValueError("invalid"),
    ):
        unserializable = export_strategy_diagnostics(context, {})
    assert unserializable.error is not None
    assert unserializable.error.code == "STRATEGY_INTERNAL_ERROR"


def test_configuration_helpers_cover_structural_and_schema_rejections() -> None:
    """Verify all declarative schema subset branches fail deterministically."""
    policy = make_ref().validation_policy
    assert not _within_limits(
        "x",
        policy.model_copy(update={"max_config_nesting_depth": 0}),
        depth=1,
    )
    assert not _within_limits(
        "x" * 10,
        policy.model_copy(update={"max_config_string_length": 1}),
        depth=1,
    )
    assert not _within_limits(
        {"a": 1, "b": 2},
        policy.model_copy(update={"max_config_collection_items": 1}),
        depth=1,
    )
    assert not _within_limits(
        (1, 2),
        policy.model_copy(update={"max_config_collection_items": 1}),
        depth=1,
    )

    assert _apply_schema({}, {"properties": "invalid"}) is None
    assert _apply_schema({}, {"properties": {}, "required": []}) is None
    assert (
        _apply_schema(
            {},
            {"properties": {"period": {"type": "integer"}}, "required": ("period",)},
        )
        is None
    )
    assert (
        _apply_schema(
            {"unexpected": 1},
            {"properties": {}, "required": (), "additionalProperties": False},
        )
        is None
    )
    assert (
        _apply_schema(
            {"period": 1},
            {"properties": {"period": "invalid"}, "required": ("period",)},
        )
        is None
    )
    assert (
        _apply_schema(
            {"period": "bad"},
            {
                "properties": {"period": {"type": "integer"}},
                "required": ("period",),
            },
        )
        is None
    )
    assert _matches_rule("bad", {"type": "integer"}) is False
    assert _matches_rule("a", {"type": "string", "enum": ("b",)}) is False
    assert _matches_rule(0, {"type": "integer", "minimum": 1}) is False
    assert _matches_rule(2, {"type": "integer", "maximum": 1}) is False


def test_contract_base_helpers_reject_invalid_scalar_material() -> None:
    """Verify private contract primitives enforce every documented scalar bound."""
    with pytest.raises(ValueError, match="UTC"):
        _utc(NOW.astimezone(timezone(timedelta(hours=1))))
    with pytest.raises(ValueError, match=r"1\.\.512"):
        _text(" ")
    with pytest.raises(ValueError, match="SHA-256"):
        _hash("invalid")
    with pytest.raises(ValueError, match="finite"):
        _finite_decimal(Decimal("NaN"))
    assert _freeze_json(1.5) == 1.5
    with pytest.raises(ValueError, match="finite"):
        _freeze_json(float("inf"))
    with pytest.raises(ValueError, match="JSON-compatible"):
        _freeze_json(object())
    assert _contains_executable_marker(("safe", "eval(payload)"))


def test_checkpoint_and_listing_fail_closed_branches() -> None:
    """Verify checkpoint and registry reads expose bounded public errors."""
    ref = make_ref()
    config = make_config()
    unauthorized = make_auth()
    denied = create_strategy_checkpoint(
        ref,
        config,
        {"counter": 1},
        "checkpoint-auth",
        unauthorized,
    )
    assert denied.error is not None
    assert denied.error.code == "STRATEGY_CHECKPOINT_INVALID"

    auth = make_auth(checkpoint=True)
    official = create_strategy_checkpoint(
        ref,
        config,
        {"nested": {"position": "forbidden"}},
        "checkpoint-auth",
        auth,
    )
    assert official.error is not None
    assert official.error.code == "STRATEGY_CHECKPOINT_INVALID"

    tiny_ref = ref.model_copy(
        update={"manifest": ref.manifest.model_copy(update={"max_checkpoint_bytes": 1})}
    )
    oversized = create_strategy_checkpoint(
        tiny_ref,
        config,
        {"counter": 1},
        "checkpoint-auth",
        auth,
    )
    assert oversized.error is not None
    assert oversized.error.code == "STRATEGY_RESOURCE_LIMIT_EXCEEDED"

    checkpoint = create_strategy_checkpoint_value(
        checkpoint_id="checkpoint-test",
        strategy_id=ref.manifest.strategy_id,
        strategy_version=ref.manifest.strategy_version,
        config_hash=config.config_hash,
        state={"counter": 1},
        state_checksum="a" * 64,
        authorization_ref="checkpoint-auth",
        created_at=NOW,
        request_id=auth.request_id,
        payload_bytes=13,
        redacted_paths=(),
    )
    denied_restore = validate_strategy_checkpoint(
        checkpoint,
        ref,
        config,
        unauthorized,
    )
    assert denied_restore.error is not None
    assert denied_restore.error.code == "STRATEGY_CHECKPOINT_INVALID"

    with patch(
        "app.services.strategy.checkpoints.store.read_strategy_checkpoint_record",
        return_value=(),
    ):
        unknown = validate_strategy_checkpoint(
            checkpoint,
            ref,
            config,
            auth,
        )
    assert unknown.error is not None
    assert unknown.error.code == "STRATEGY_CHECKPOINT_INVALID"

    with (
        patch(
            "app.services.strategy.registry.listing.read_strategy_version_records",
            side_effect=RuntimeError("database"),
        ),
        patch(
            "app.services.strategy.registry.listing.is_data_error",
            return_value=True,
        ),
    ):
        failed_listing = list_strategy_versions("missing")
    assert failed_listing.error is not None
    assert failed_listing.error.code == "STRATEGY_INTERNAL_ERROR"

    with patch(
        "app.services.strategy.registry.listing.read_strategy_version_records",
        return_value=(),
    ):
        missing = list_strategy_versions("missing")
    assert missing.error is not None
    assert missing.error.code == "STRATEGY_NOT_FOUND"
