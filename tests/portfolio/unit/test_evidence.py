"""Unit tests for Portfolio owner-evidence and eligibility validation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.composition.logging import get_logger
from app.services.analytics import create_analytics_value
from app.services.data import (
    build_account_state_snapshot,
    build_data_quality_report,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_dataset,
    build_ohlcv_record,
    is_account_state_snapshot,
    is_fx_conversion_evidence,
    is_market_dataset,
)
from app.services.portfolio._settings import PortfolioSettings
from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.services.portfolio.contracts.errors import PortfolioError
from app.services.portfolio.evidence import (
    revalidate_activation_evidence,
    validate_construction_evidence,
    validator,
)
from app.services.risk import (
    create_strategy_operational_eligibility_decision,
    get_decision_state,
)
from app.services.strategy import (
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)

logger = get_logger(__name__)

# Private type-only aliases; Risk exposes functions, not contract classes.
StrategyOperationalEligibilityDecision = object
AccountStateSnapshot = object
FXConversionEvidence = object
MarketDataset = object
PortfolioAllocationEvidence = object

_ACCOUNT_REQUEST_ID = "req-11111111-1111-4111-8111-111111111112"
_MARKET_REQUEST_ID = "req-11111111-1111-4111-8111-111111111113"
_FX_REQUEST_ID = "req-11111111-1111-4111-8111-111111111114"


def _analytics_evidence(now: datetime) -> PortfolioAllocationEvidence:
    """Build a minimal type-safe Analytics owner instance for boundary tests.

    Args:
        now: Stable UTC evidence time.

    Returns:
        Analytics evidence instance carrying fields consumed by Portfolio.
    """
    logger.debug("Building minimal Analytics evidence instance")
    return create_analytics_value(
        "PortfolioAllocationEvidence",
        contract_version="v1",
        schema_id="analytics.portfolio_allocation_evidence.v1",
        evidence_id="analytics-evidence-1",
        allocation_reference="allocation-1",
        result_references=("result-1",),
        measurement_start=now - timedelta(minutes=1),
        measurement_end=now,
        base_currency="USD",
        component_metrics=({"component_id": "component-a", "volatility": 0.1},),
        aggregate_metrics=(),
        dependence_evidence={
            "section_key": "dependence",
            "criticality": "optional",
            "metrics": (),
            "status": "skipped",
            "reason": "No dependence metric is required by this boundary test.",
        },
        concentration_evidence={
            "section_key": "concentration",
            "criticality": "optional",
            "metrics": (),
            "status": "skipped",
            "reason": "No concentration metric is required by this boundary test.",
        },
        caveats=(),
        fx_lineage={
            "source_contract": "data.fx_conversion_evidence.v1",
            "source_version": "v1",
            "source_schema_id": "data.fx_conversion_evidence.v1",
            "source_ids": (_FX_REQUEST_ID,),
            "configuration_sources": ("portfolio-tests",),
            "account_currency": "USD",
            "transformations": ("direct EURUSD conversion",),
        },
    )


def _owner_bundle(
    now: datetime,
) -> tuple[
    dict[str, object],
    dict[str, StrategyOperationalEligibilityDecision],
    AccountStateSnapshot,
    MarketDataset,
    PortfolioAllocationEvidence,
    dict[str, FXConversionEvidence],
]:
    """Build exact public owner-contract instances needed by validation.

    Args:
        now: Stable UTC evidence time.

    Returns:
        Strategy, Risk, Data, Analytics, and FX owner-contract bundle.
    """
    logger.debug("Building Portfolio owner evidence test bundle")
    refs: dict[str, object] = {}
    decisions: dict[str, StrategyOperationalEligibilityDecision] = {}
    for suffix in ("a", "b"):
        policy = create_strategy_validation_policy(
            policy_version="strategy-policy-1",
            approved_module_roots=("approved.strategies",),
            max_config_payload_bytes=4096,
            max_config_nesting_depth=8,
            max_config_string_length=256,
            max_config_collection_items=128,
        )
        manifest = create_strategy_manifest(
            strategy_id=f"strategy-{suffix}",
            strategy_version="1.0.0",
            module_path=f"approved.strategies.strategy_{suffix}",
            owner_ref="portfolio-tests",
            interface_version="v1",
            config_schema_version="v1",
            config_schema={"type": "object"},
            required_data=("bars",),
            required_indicators=(),
            timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
            permitted_environments=(get_strategy_environment("SIMULATION"),),
            source_hash=suffix * 64,
            artifact_hash=suffix * 64,
            dependency_hash=suffix * 64,
            provenance_refs=("portfolio-tests",),
            supported_hooks=("on_bar",),
            requires_account_snapshot=False,
            max_batch_records=100,
            max_diagnostic_bytes=8192,
            max_checkpoint_bytes=8192,
            max_local_state_bytes=4096,
            decision_timeout_seconds=5,
        )
        ref = create_validated_strategy_ref(
            manifest=manifest,
            lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
            environment=get_strategy_environment("SIMULATION"),
            policy_version="strategy-policy-1",
            validation_policy=policy,
            registry_record_hash=suffix * 64,
            request_id=f"req-{suffix * 32}",
            correlation_id=f"cor-{suffix * 32}",
        )
        decision = create_strategy_operational_eligibility_decision(
            decision_id=f"eligibility-{suffix}",
            strategy_id=f"strategy-{suffix}",
            strategy_version="1.0.0",
            scope={"environment": "simulation", "tenant": "owner"},
            state=get_decision_state("APPROVE"),
            conditions=(),
            policy_version="risk-policy-1",
            evidence_refs={"strategy": suffix * 64},
            suspended=False,
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=10),
            audit_ref=f"audit-{suffix}",
        )
        refs[f"component-{suffix}"] = ref
        decisions[decision.decision_id] = decision
    account = build_account_state_snapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            {"asset": "USD", "total": Decimal(1000), "available": Decimal(1000)},
        ),
        equity=Decimal(1000),
        margin_used=Decimal(0),
        margin_available=Decimal(1000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="portfolio-tests",
        request_id=_ACCOUNT_REQUEST_ID,
        snapshot_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    bar = build_ohlcv_record(
        timestamp=now,
        source="portfolio-tests",
        source_symbol="EURUSD",
        source_revision="1",
        available_at=now,
        open=Decimal("1.1"),
        high=Decimal("1.2"),
        low=Decimal("1.0"),
        close=Decimal("1.15"),
        volume=Decimal(1),
        price_unit="quote_currency",
        volume_unit="lots",
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=now,
    )
    market = build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=(bar,),
        start=bar.timestamp,
        end=bar.timestamp,
        available_at=bar.available_at,
        record_count=1,
        quality_report=quality,
        source_metadata={"provider": "portfolio-tests"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_MARKET_REQUEST_ID,
    )
    leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.15"),
        source_id="portfolio-tests",
        provider_symbol="EURUSD",
        as_of=now,
        provenance={"source": "portfolio-tests"},
    )
    fx = build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="USD",
        legs=(leg,),
        composite_rate=Decimal("1.15"),
        path_policy_id="direct",
        path_policy_version="1",
        provenance={"source": "portfolio-tests"},
        request_id=_FX_REQUEST_ID,
        as_of=now,
        expires_at=now + timedelta(minutes=10),
    )
    return (
        refs,
        decisions,
        account,
        market,
        _analytics_evidence(now),
        {_FX_REQUEST_ID: fx},
    )


def _request_data_with_fx(data: dict[str, Any]) -> dict[str, Any]:
    """Return request data with exact test owner digests and FX reference.

    Args:
        data: Base complete request data.

    Returns:
        Updated independent request data.
    """
    logger.debug("Adding exact owner hashes to Portfolio request data")
    updated = deepcopy(data)
    updated["evidence"] = {
        **updated["evidence"],
        "account_snapshot_id": _ACCOUNT_REQUEST_ID,
        "account_snapshot_hash": "a" * 64,
        "market_dataset_id": _MARKET_REQUEST_ID,
        "market_dataset_hash": "b" * 64,
        "analytics_evidence_hash": "c" * 64,
        "fx_evidence_ids": (_FX_REQUEST_ID,),
        "fx_evidence_hashes": ("d" * 64,),
    }
    return updated


def _patch_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch canonical hashing with type-distinct deterministic test digests.

    Args:
        monkeypatch: Pytest patch helper.
    """
    logger.debug("Patching owner evidence hashes for validation unit tests")

    def digest(value: object) -> str:
        """Return deterministic digest by exact owner value type.

        Args:
            value: Owner value or aggregate material.

        Returns:
            Stable lowercase digest.
        """
        logger.debug("Resolving deterministic evidence test digest")
        if is_account_state_snapshot(value):
            return "a" * 64
        if is_market_dataset(value):
            return "b" * 64
        if (
            getattr(value, "schema_id", "")
            == "analytics.portfolio_allocation_evidence.v1"
        ):
            return "c" * 64
        if is_fx_conversion_evidence(value):
            return "d" * 64
        if isinstance(value, tuple):
            return "e" * 64
        return "f" * 64

    monkeypatch.setattr(validator, "_digest", digest)


def test_internal_evidence_helpers_cover_nested_material_and_metric_failures(
    construction_request_data: dict[str, Any],
    portfolio_now: datetime,
) -> None:
    """Exercise deterministic helper branches and fail-closed metric checks."""
    request = PortfolioConstructionRequest(**construction_request_data)
    nested = validator._hash_material({"items": ({"value": Decimal("1.5")},)})
    assert nested == {"items": ({"value": Decimal("1.5")},)}
    with pytest.raises(PortfolioError, match="PORT_EVIDENCE_INVALID"):
        validator._require_fresh(
            portfolio_now + timedelta(seconds=1),
            portfolio_now,
            timedelta(minutes=1),
            "FUTURE",
        )
    with pytest.raises(PortfolioError, match="ANALYTICS_METRIC_SET"):
        validator._validate_analytics_metrics(
            request,
            {"component-a": Decimal("0.1")},
            {"component-a": 30},
        )
    with pytest.raises(PortfolioError, match="ANALYTICS_METRICS"):
        validator._validate_analytics_metrics(
            request,
            {"component-a": Decimal(0), "component-b": Decimal("0.2")},
            {"component-a": 30, "component-b": True},
        )


def test_validate_construction_evidence_requires_exact_current_owners(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify exact Strategy, Risk, Data, Analytics, and FX evidence passes.

    Args:
        construction_request_data: Complete base request data.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
        monkeypatch: Pytest patch helper.
    """
    logger.info("Testing complete Portfolio construction evidence validation")
    _patch_digest(monkeypatch)
    request = PortfolioConstructionRequest(
        **_request_data_with_fx(construction_request_data)
    )
    refs, decisions, account, market, analytics, fx = _owner_bundle(portfolio_now)

    evidence = validate_construction_evidence(
        request,
        strategy_refs=refs,
        eligibility_decisions=decisions,
        account_snapshot=account,
        market_dataset=market,
        analytics_evidence=analytics,
        fx_evidence=fx,
        component_volatilities={
            "component-a": Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        component_observations={"component-a": 30, "component-b": 30},
        now=portfolio_now,
        settings=portfolio_settings,
    )

    assert evidence.evidence_hash == "f" * 64
    assert evidence.strategy_lineage_hash == "e" * 64
    revalidate_activation_evidence(
        evidence,
        strategy_refs=refs,
        eligibility_decisions=decisions,
        now=portfolio_now,
    )


def test_evidence_rejects_missing_or_stale_fx_without_synthesis(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing and stale FX references fail closed.

    Args:
        construction_request_data: Complete base request data.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
        monkeypatch: Pytest patch helper.
    """
    logger.info("Testing fail-closed Portfolio FX evidence validation")
    _patch_digest(monkeypatch)
    request = PortfolioConstructionRequest(
        **_request_data_with_fx(construction_request_data)
    )
    refs, decisions, account, market, analytics, _fx = _owner_bundle(portfolio_now)
    arguments = {
        "strategy_refs": refs,
        "eligibility_decisions": decisions,
        "account_snapshot": account,
        "market_dataset": market,
        "analytics_evidence": analytics,
        "component_volatilities": {
            "component-a": Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        "component_observations": {"component-a": 30, "component-b": 30},
        "now": portfolio_now,
        "settings": portfolio_settings,
    }
    with pytest.raises(PortfolioError, match="COVERAGE"):
        validate_construction_evidence(request, fx_evidence={}, **arguments)

    stale_at = portfolio_now - timedelta(hours=1)
    stale_leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.15"),
        source_id="portfolio-tests",
        provider_symbol="EURUSD",
        as_of=stale_at,
        provenance={"source": "portfolio-tests"},
    )
    stale = build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="USD",
        legs=(stale_leg,),
        composite_rate=Decimal("1.15"),
        path_policy_id="direct",
        path_policy_version="1",
        provenance={"source": "portfolio-tests"},
        request_id=_FX_REQUEST_ID,
        as_of=stale_at,
        expires_at=portfolio_now,
    )
    with pytest.raises(PortfolioError, match="CURRENT_REFERENCE"):
        validate_construction_evidence(
            request,
            fx_evidence={_FX_REQUEST_ID: stale},
            **arguments,
        )


def test_evidence_rejects_changed_strategy_and_unsafe_objects(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify owner-reference changes and arbitrary runtime objects are rejected.

    Args:
        construction_request_data: Complete base request data.
        portfolio_settings: Explicit Portfolio settings.
        portfolio_now: Stable UTC time.
        monkeypatch: Pytest patch helper.
    """
    logger.info("Testing Portfolio reference-change and unsafe-object rejection")
    _patch_digest(monkeypatch)
    request = PortfolioConstructionRequest(
        **_request_data_with_fx(construction_request_data)
    )
    refs, decisions, account, market, analytics, fx = _owner_bundle(portfolio_now)
    changed = dict(refs)
    changed_policy = create_strategy_validation_policy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    changed_manifest = create_strategy_manifest(
        strategy_id="strategy-a",
        strategy_version="2.0.0",
        module_path="approved.strategies.strategy_a",
        owner_ref="portfolio-tests",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("SIMULATION"),),
        source_hash="a" * 64,
        artifact_hash="a" * 64,
        dependency_hash="a" * 64,
        provenance_refs=("portfolio-tests",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    changed["component-a"] = create_validated_strategy_ref(
        manifest=changed_manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("SIMULATION"),
        policy_version="strategy-policy-1",
        validation_policy=changed_policy,
        registry_record_hash="a" * 64,
        request_id="req-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        correlation_id="cor-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    common = {
        "eligibility_decisions": decisions,
        "account_snapshot": account,
        "market_dataset": market,
        "analytics_evidence": analytics,
        "fx_evidence": fx,
        "component_volatilities": {
            "component-a": Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        "component_observations": {"component-a": 30, "component-b": 30},
        "now": portfolio_now,
        "settings": portfolio_settings,
    }
    with pytest.raises(PortfolioError, match="PORT_REFERENCE_CHANGED"):
        validate_construction_evidence(request, strategy_refs=changed, **common)
    with pytest.raises(PortfolioError, match="PORT_UNSAFE_OBJECT"):
        validate_construction_evidence(
            request,
            strategy_refs={"component-a": object(), "component-b": object()},  # type: ignore[dict-item]
            **common,
        )
