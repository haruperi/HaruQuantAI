"""Shared Strategy contract fixtures and focused model tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

import pandas as pd
import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.results import IndicatorResult, build_indicator_result
from app.services.strategy import (
    StrategyConfig,
    StrategyDecision,
    StrategyEnvironment,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.utils import AuthContext, logger
from pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from app.services.strategy.contracts._base import JsonValue

HASH = "a" * 64
HASH_B = "b" * 64
NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)
REQ = "req-11111111-1111-4111-8111-111111111111"
WF = "wf-22222222-2222-4222-8222-222222222222"
COR = "cor-33333333-3333-4333-8333-333333333333"


def make_market(
    prices: Sequence[tuple[str, str, str, str]],
    *,
    timeframe: str = "M5",
    symbol: str = "EURUSD",
) -> MarketDataset:
    """Build canonical bar evidence from explicit OHLC strings.

    Args:
        prices: Ordered open, high, low, and close string tuples.
        timeframe: Exact dataset timeframe.
        symbol: Canonical dataset symbol.

    Returns:
        A complete immutable Data-owned market dataset.
    """
    logger.debug("Building concrete Strategy market test evidence")
    records = tuple(
        OHLCVRecord(
            timestamp=NOW - timedelta(hours=1) + timedelta(minutes=5 * index),
            source="test",
            source_symbol=symbol,
            available_at=NOW - timedelta(hours=1) + timedelta(minutes=5 * index),
            open=Decimal(open_price),
            high=Decimal(high),
            low=Decimal(low),
            close=Decimal(close),
            volume=Decimal(100),
            price_unit="USD",
            volume_unit="units",
        )
        for index, (open_price, high, low, close) in enumerate(prices)
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=symbol,
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=REQ,
    )


def make_indicator(
    market: MarketDataset,
    *,
    indicator_id: str,
    output_column: str,
    values: Sequence[float],
) -> IndicatorResult:
    """Build one official indicator result over exact market evidence.

    Args:
        market: Exact source market dataset.
        indicator_id: Official indicator identity.
        output_column: Exact output column name.
        values: Ordered ready indicator values.

    Returns:
        A checksum-bound official indicator result.
    """
    logger.debug("Building concrete Strategy indicator test evidence")
    index = pd.DatetimeIndex(
        [record.timestamp for record in market.records], name="timestamp", tz="UTC"
    )
    output_values = pd.DataFrame({output_column: values}, index=index)
    available_at = pd.Series(
        [record.available_at for record in market.records], index=index
    )
    computed_from = pd.Series(
        [record.timestamp for record in market.records], index=index
    )
    unavailable_reason = pd.Series([pd.NA] * len(index), index=index)
    config = IndicatorConfig(
        indicator_id=indicator_id,
        parameters=(),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    return build_indicator_result(
        data=market,
        config=config,
        indicator_version="1.0.0",
        output_columns=(output_column,),
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from,
        computed_from_end=computed_from,
        unavailable_reason=unavailable_reason,
    )


def make_signal_config(
    parameters: Mapping[str, JsonValue],
) -> ValidatedStrategyConfig:
    """Build validated configuration for a concrete signal evaluator.

    Args:
        parameters: Exact normalized evaluator parameters.

    Returns:
        An immutable validated configuration.
    """
    logger.debug("Building concrete Strategy validated test configuration")
    return ValidatedStrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters=MappingProxyType(dict(parameters)),
        config_hash=HASH_B,
        policy_version="policy-v1",
        request_id=REQ,
    )


def make_signal_evidence(
    market: MarketDataset,
    *,
    related_markets: Mapping[str, MarketDataset] | None = None,
    feature_values: Mapping[str, tuple[Decimal, ...]] | None = None,
    feature_available_at: Mapping[str, datetime] | None = None,
    feature_refs: Mapping[str, str] | None = None,
    active_position_tags: tuple[str, ...] = (),
) -> StrategySignalEvidence:
    """Build provenance-complete concrete signal evidence.

    Args:
        market: Primary canonical market dataset.
        related_markets: Optional named point-in-time market datasets.
        feature_values: Optional named immutable feature values.
        feature_available_at: Optional named feature availability times.
        feature_refs: Optional named feature provenance references.
        active_position_tags: Runtime-owned open-position tags.

    Returns:
        Immutable concrete signal evidence.
    """
    logger.debug("Building concrete Strategy signal test evidence")
    return StrategySignalEvidence(
        evidence_id=HASH,
        primary_market=market,
        related_markets=related_markets or {},
        point_size=Decimal("0.00001"),
        feature_values=feature_values or {},
        feature_available_at=feature_available_at or {},
        feature_refs=feature_refs or {},
        active_position_tags=active_position_tags,
    )


def make_policy() -> StrategyValidationPolicy:
    """Build an explicit validation policy fixture.

    Returns:
        A complete validation policy.
    """
    logger.debug("Building Strategy test validation policy")
    return StrategyValidationPolicy(
        policy_version="policy-v1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )


def make_manifest(
    *, timing: StrategyTimingPolicy = StrategyTimingPolicy.EVENT_DRIVEN
) -> StrategyManifest:
    """Build a complete Strategy manifest fixture.

    Args:
        timing: Desired timing policy.

    Returns:
        A complete immutable manifest.
    """
    logger.debug("Building Strategy test manifest")
    return StrategyManifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {
                "period": {"type": "integer", "minimum": 1},
                "mode": {"type": "string", "default": "strict"},
            },
            "required": ("period",),
            "additionalProperties": False,
        },
        required_data=("bars",),
        required_indicators=(),
        timing_policy=timing,
        permitted_environments=(StrategyEnvironment.RESEARCH,),
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=4_096,
        decision_timeout_seconds=5,
    )


def make_ref(
    *, timing: StrategyTimingPolicy = StrategyTimingPolicy.EVENT_DRIVEN
) -> ValidatedStrategyRef:
    """Build an exact validated Strategy reference fixture.

    Args:
        timing: Desired timing policy.

    Returns:
        A validated exact reference.
    """
    logger.debug("Building Strategy test validated reference")
    policy = make_policy()
    return ValidatedStrategyRef(
        manifest=make_manifest(timing=timing),
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.RESEARCH,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=HASH_B,
        request_id=REQ,
        correlation_id=COR,
    )


def make_config() -> ValidatedStrategyConfig:
    """Build a validated Strategy configuration fixture.

    Returns:
        A validated configuration.
    """
    logger.debug("Building Strategy test validated configuration")
    return ValidatedStrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"period": 5, "mode": "strict"},
        config_hash=HASH_B,
        policy_version="policy-v1",
        request_id=REQ,
    )


def make_context(
    *, timing: StrategyTimingPolicy = StrategyTimingPolicy.EVENT_DRIVEN
) -> StrategyExecutionContext:
    """Build a fixed-clock Strategy execution context fixture.

    Args:
        timing: Desired timing policy.

    Returns:
        A deterministic context.
    """
    logger.debug("Building Strategy test execution context")
    return StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=NOW,
        timing_policy=timing,
        seed=7,
        interface_version="v1",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        dependency_status={},
        snapshot_refs=("snapshot-1",),
        max_diagnostic_bytes=8_192,
    )


def make_decision(*, action: str = "PROPOSE") -> StrategyDecision:
    """Build a neutral or proposal Strategy decision fixture.

    Args:
        action: ``PROPOSE`` or ``NEUTRAL``.

    Returns:
        A complete decision.
    """
    logger.debug("Building Strategy test decision")
    proposal = action == "PROPOSE"
    return StrategyDecision(
        decision_id="decision-1",
        sequence=0,
        action=action,
        symbol="EURUSD" if proposal else None,
        side="BUY" if proposal else None,
        intent_type="OPEN" if proposal else None,
        order_type="MARKET" if proposal else None,
        requested_sizing_mode="quantity" if proposal else None,
        quantity_hint=Decimal(1) if proposal else None,
        valid_from=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        rationale_refs=("reason-1",),
        diagnostic_facts={},
        lineage={
            "strategy_id": "mean-reversion",
            "strategy_version": "1.0.0",
            "config_hash": HASH_B,
        },
    )


def make_event() -> StrategyEvent:
    """Build receiver-owned external event evidence.

    Returns:
        A complete event contract.
    """
    logger.debug("Building Strategy test event")
    return StrategyEvent(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=NOW - timedelta(minutes=1),
        sequence=1,
        source_owner="data",
        source_contract_version="v1",
        source_schema_id="data.market_dataset.v1",
        source_snapshot_ref="dataset-1",
        source_checksum=HASH,
        source_as_of=NOW - timedelta(minutes=1),
        facts={"symbol": "EURUSD"},
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
    )


def make_auth(*, checkpoint: bool = False) -> AuthContext:
    """Build an authenticated Strategy test principal.

    Args:
        checkpoint: Whether to include checkpoint authorization scope.

    Returns:
        A complete AuthContext.
    """
    logger.debug("Building Strategy test authentication context")
    permissions = ("strategy:register", "strategy:update")
    scopes: tuple[str, ...] = ()
    if checkpoint:
        permissions += ("strategy:checkpoint",)
        scopes = ("checkpoint-auth",)
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="builder",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=permissions,
        scopes=scopes,
        tenant_or_environment="test",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        issued_at=NOW,
    )


def test_contracts_are_immutable_and_validate_selectors() -> None:
    """Verify frozen models and exact version-selector cardinality."""
    logger.debug("Testing Strategy contract immutability")
    config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    with pytest.raises(TypeError):
        config.parameters["period"] = 6  # type: ignore[index]
    with pytest.raises(ValidationError):
        StrategyRef(
            strategy_id="mean-reversion",
            environment=StrategyEnvironment.RESEARCH,
            request_id=REQ,
            correlation_id=COR,
        )


def test_validation_policy_requires_explicit_positive_bounds() -> None:
    """Verify validation policy has no hidden numeric defaults."""
    logger.debug("Testing Strategy validation policy bounds")
    with pytest.raises(ValidationError):
        StrategyValidationPolicy(
            policy_version="p1",
            approved_module_roots=("approved",),
            max_config_payload_bytes=0,
            max_config_nesting_depth=1,
            max_config_string_length=1,
            max_config_collection_items=1,
        )


def test_strategy_event_payload_is_immutable() -> None:
    """Verify receiver-owned event facts cannot be mutated."""
    logger.debug("Testing Strategy event fact immutability")
    event = make_event()
    with pytest.raises(TypeError):
        event.facts["symbol"] = "GBPUSD"  # type: ignore[index]


def test_neutral_decision_contains_no_intent() -> None:
    """Verify neutral decisions contain no proposal fields."""
    logger.debug("Testing neutral Strategy decision")
    assert make_decision(action="NEUTRAL").symbol is None


def test_strategy_environment_rejects_shadow_initially() -> None:
    """Verify the unsupported shadow profile is excluded."""
    logger.debug("Testing Strategy environment enumeration")
    with pytest.raises(ValueError, match="SHADOW"):
        StrategyEnvironment("SHADOW")


def test_timing_policy_serializes_stably() -> None:
    """Verify timing policy values are stable strings."""
    logger.debug("Testing Strategy timing policy serialization")
    assert StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE.value == (
        "BAR_OPEN_PREVIOUS_CLOSE"
    )


def test_revoked_status_is_never_executable() -> None:
    """Verify revoked is distinct from approved lifecycle state."""
    logger.debug("Testing Strategy revoked lifecycle state")
    assert StrategyLifecycleStatus.REVOKED is not StrategyLifecycleStatus.APPROVED


def test_strategy_ref_requires_exactly_one_version_selector() -> None:
    """Verify exact and constraint selectors are mutually exclusive."""
    logger.debug("Testing Strategy reference selector cardinality")
    with pytest.raises(ValidationError):
        StrategyRef(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            version_constraint="*",
            environment=StrategyEnvironment.RESEARCH,
            request_id=REQ,
            correlation_id=COR,
        )


def test_validated_ref_is_immutable() -> None:
    """Verify exact resolved references are frozen."""
    logger.debug("Testing validated Strategy reference immutability")
    with pytest.raises(ValidationError):
        make_ref().environment = StrategyEnvironment.LIVE


def test_strategy_config_rejects_executable_values() -> None:
    """Verify executable-looking parameter strings fail at the contract."""
    logger.debug("Testing Strategy config executable rejection")
    with pytest.raises(ValidationError):
        StrategyConfig(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters={"payload": "exec(value)"},
            request_id=REQ,
        )


def test_validated_config_hash_is_canonical() -> None:
    """Verify validated configuration carries an exact digest."""
    logger.debug("Testing canonical Strategy config hash")
    assert len(make_config().config_hash) == 64


def test_manifest_requires_only_applicable_declarations() -> None:
    """Verify a stateless manifest can declare no account dependency."""
    logger.debug("Testing Strategy manifest applicability")
    assert make_manifest().requires_account_snapshot is False


def test_registration_request_rejects_user_file_path() -> None:
    """Verify user filesystem paths cannot be module identifiers."""
    logger.debug("Testing Strategy registration path rejection")
    values = make_manifest().model_dump(mode="json")
    values["module_path"] = "C:/user/strategy.py"
    with pytest.raises(ValidationError):
        StrategyManifest(
            **values,
        )


def test_parameter_update_requires_exact_version() -> None:
    """Verify parameter updates cannot use a version constraint."""
    logger.debug("Testing exact Strategy parameter update selector")
    config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    with pytest.raises(ValidationError):
        StrategyParameterUpdateRequest(
            command_id="command",
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            parameters={"period": 5},
            principal_id="builder",
            reason="test",
            ref=StrategyRef(
                strategy_id="mean-reversion",
                version_constraint="*",
                environment=StrategyEnvironment.RESEARCH,
                request_id=REQ,
                correlation_id=COR,
            ),
            config=config,
            authorization_ref="approval",
            requested_at=NOW,
            request_id=REQ,
            correlation_id=COR,
        )


def test_execution_context_rejects_naive_time() -> None:
    """Verify fixed decision clocks must be aware UTC."""
    logger.debug("Testing Strategy context UTC enforcement")
    values = make_context().model_dump(mode="json")
    values["decision_timestamp"] = NOW.replace(tzinfo=None)
    with pytest.raises(ValidationError):
        StrategyExecutionContext(
            **values,
        )


def test_execution_result_rejects_partial_failed_batch() -> None:
    """Verify proposal decisions cannot omit their corresponding intent."""
    logger.debug("Testing Strategy execution-result atomicity")
    with pytest.raises(ValidationError):
        StrategyExecutionResult(
            decisions=(make_decision(),),
            intents=(),
            diagnostics=object(),
            replay_manifest=object(),
            result_hash=HASH,
        )
