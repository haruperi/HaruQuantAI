"""Unit tests for Portfolio owner-evidence and eligibility validation."""

# ruff: noqa: INP001

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from app.services.analytics import PortfolioAllocationEvidence
from app.services.data.contracts import (
    AccountStateSnapshot,
    FXConversionEvidence,
    MarketDataset,
)
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.services.portfolio.evidence import (
    revalidate_activation_evidence,
    validate_construction_evidence,
    validator,
)
from app.services.portfolio.exceptions import PortfolioError
from app.services.risk import DecisionState, StrategyOperationalEligibilityDecision
from app.services.strategy import StrategyLifecycleStatus, ValidatedStrategyRef
from app.utils import logger


def _analytics_evidence(now: datetime) -> PortfolioAllocationEvidence:
    """Build a minimal type-safe Analytics owner instance for boundary tests.

    Args:
        now: Stable UTC evidence time.

    Returns:
        Analytics evidence instance carrying fields consumed by Portfolio.
    """
    logger.debug("Building minimal Analytics evidence instance")
    evidence = object.__new__(PortfolioAllocationEvidence)
    object.__setattr__(evidence, "evidence_id", "analytics-evidence-1")
    object.__setattr__(evidence, "measurement_end", now)
    object.__setattr__(evidence, "base_currency", "USD")
    return evidence


def _owner_bundle(
    now: datetime,
) -> tuple[
    dict[str, ValidatedStrategyRef],
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
    refs: dict[str, ValidatedStrategyRef] = {}
    decisions: dict[str, StrategyOperationalEligibilityDecision] = {}
    for suffix in ("a", "b"):
        ref = ValidatedStrategyRef.model_construct(
            manifest=SimpleNamespace(
                strategy_id=f"strategy-{suffix}",
                strategy_version="1.0.0",
            ),
            lifecycle_status=StrategyLifecycleStatus.APPROVED,
            registry_record_hash=suffix * 64,
        )
        decision = StrategyOperationalEligibilityDecision.model_construct(
            decision_id=f"eligibility-{suffix}",
            strategy_id=f"strategy-{suffix}",
            strategy_version="1.0.0",
            scope={"environment": "simulation", "tenant": "owner"},
            state=DecisionState.APPROVE,
            suspended=False,
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=10),
        )
        refs[f"component-{suffix}"] = ref
        decisions[decision.decision_id] = decision
    account = AccountStateSnapshot.model_construct(
        request_id="account-snapshot-1",
        snapshot_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    market = MarketDataset.model_construct(
        request_id="market-dataset-1",
        end=now,
    )
    fx = FXConversionEvidence.model_construct(
        request_id="fx-1",
        as_of=now,
        expires_at=now + timedelta(minutes=10),
    )
    return refs, decisions, account, market, _analytics_evidence(now), {"fx-1": fx}


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
        "account_snapshot_hash": "a" * 64,
        "market_dataset_hash": "b" * 64,
        "analytics_evidence_hash": "c" * 64,
        "fx_evidence_ids": ("fx-1",),
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
        if isinstance(value, AccountStateSnapshot):
            return "a" * 64
        if isinstance(value, MarketDataset):
            return "b" * 64
        if isinstance(value, PortfolioAllocationEvidence):
            return "c" * 64
        if isinstance(value, FXConversionEvidence):
            return "d" * 64
        if isinstance(value, tuple):
            return "e" * 64
        return "f" * 64

    monkeypatch.setattr(validator, "_digest", digest)


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

    stale = FXConversionEvidence.model_construct(
        request_id="fx-1",
        as_of=portfolio_now - timedelta(hours=1),
        expires_at=portfolio_now,
    )
    with pytest.raises(PortfolioError, match="CURRENT_REFERENCE"):
        validate_construction_evidence(
            request,
            fx_evidence={"fx-1": stale},
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
    changed["component-a"] = ValidatedStrategyRef.model_construct(
        manifest=SimpleNamespace(
            strategy_id="strategy-a",
            strategy_version="2.0.0",
        ),
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        registry_record_hash="a" * 64,
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
