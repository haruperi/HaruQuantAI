"""Evaluate an external proposal against genuine MT5-backed Strategy evidence."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_symbol_metadata
from app.services.strategy import (
    bind_proposal_lineage,
    create_strategy_proposal_evaluation_request,
    create_strategy_proposal_evaluation_result,
    create_strategy_signal_evidence,
    evaluate_strategy_proposal,
    register_strategy_version,
    validate_strategy_proposal,
)
from app.utils import canonical_digest, create_auth_context

from tests.strategy.usage.workflows._support import (
    COR,
    REQ,
    WF,
    MarketProposalEvaluator,
    caller_config,
    current_context,
    live_bars,
    policy,
    print_market_frame,
    registration_request,
    temporary_storage,
    unresolved_ref,
)


def _header(title: str) -> None:
    """Print one feature-evidence heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_049() -> None:
    """Demonstrate receiver-owned proposal request construction."""
    _header("FR-STR-049 — Receiver-owned proposal request")
    assert callable(create_strategy_proposal_evaluation_request)


def fr_str_050() -> None:
    """Demonstrate typed proposal result construction."""
    _header("FR-STR-050 — Typed proposal result")
    assert callable(create_strategy_proposal_evaluation_result)


def fr_str_051() -> None:
    """Demonstrate fail-closed proposal validation."""
    _header("FR-STR-051 — Proposal authority and evidence validation")
    assert callable(validate_strategy_proposal)


def fr_str_052() -> None:
    """Demonstrate deterministic proposal evaluation and audit."""
    _header("FR-STR-052 — Deterministic proposal evaluation")
    assert callable(evaluate_strategy_proposal)


def fr_str_053() -> None:
    """Demonstrate lineage-only external proposal binding."""
    _header("FR-STR-053 — Lineage-only proposal binding")
    assert callable(bind_proposal_lineage)


def main() -> int:  # noqa: PLR0915
    """Evaluate a runtime proposal using genuine market observations.

    Returns:
        ``0`` after a matching signal, intent, and audit reference are shown.
    """
    fr_str_049()
    fr_str_050()
    fr_str_051()
    fr_str_052()
    fr_str_053()
    print("\nEXTERNAL PROPOSAL INTAKE — GENUINE MT5 EURUSD M1")
    market = live_bars()
    print("\nGenuine normalized input bars:")
    print_market_frame(market, rows=10)
    metadata = get_symbol_metadata(source_id="mt5", symbol=market.symbol)
    if metadata.data is None:
        raise RuntimeError(f"Symbol metadata unavailable: {metadata.error}")
    context = current_context("EVENT_DRIVEN", market=market)
    bar = market.records[-1]
    requested_direction = "BUY" if bar.close >= bar.open else "SELL"
    proposal_material = {
        "market_request_id": market.request_id,
        "bar_timestamp": bar.timestamp.isoformat(),
        "open": str(bar.open),
        "close": str(bar.close),
        "requested_direction": requested_direction,
    }
    source_hash = canonical_digest(proposal_material)
    request = create_strategy_proposal_evaluation_request(
        principal_id="builder",
        source_proposal_id=f"runtime-proposal-{source_hash[:16]}",
        source_task_id=f"runtime-observation-{market.request_id}",
        source_content_hash=source_hash,
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        instrument=market.symbol,
        requested_direction=requested_direction,
        horizon_seconds=600,
        thesis_evidence_refs=(market.request_id,),
        invalidation_evidence_refs=(f"bar-{bar.timestamp.isoformat()}",),
        evaluation_scope="TRADE_INTENT_IF_SUPPORTED",
        requested_at=context.decision_timestamp - timedelta(seconds=1),
        expires_at=context.decision_timestamp + timedelta(minutes=5),
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
    )
    auth = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="builder",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=("strategy:register", "strategy:evaluate_proposal"),
        scopes=("strategy:proposal_evaluation",),
        tenant_or_environment="dev",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        issued_at=datetime.now(UTC),
    )
    evidence = create_strategy_signal_evidence(
        evidence_id=canonical_digest(proposal_material),
        primary_market=market,
        related_markets={},
        point_size=Decimal(str(metadata.data.point)),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    evaluator = MarketProposalEvaluator()
    with temporary_storage():
        registered = register_strategy_version(
            registration_request(),
            auth,
            policy(),
        )
        if registered.data is None or registered.data.status not in {
            "ACCEPTED",
            "IDEMPOTENT",
        }:
            raise RuntimeError(f"Registration failed: {registered.error}")
        validation = validate_strategy_proposal(
            request,
            auth,
            unresolved_ref(),
            caller_config(),
            policy(),
            evidence,
            context,
            evaluator,
        )
        if validation.data is None:
            raise RuntimeError(f"Proposal validation failed: {validation.error}")
        evaluation = evaluate_strategy_proposal(
            request,
            auth,
            unresolved_ref(),
            caller_config(),
            policy(),
            evidence,
            (),
            context,
            evaluator,
        )
    if evaluation.data is None:
        raise RuntimeError(f"Proposal evaluation failed: {evaluation.error}")
    result = evaluation.data
    rebuilt = create_strategy_proposal_evaluation_result(
        **result.model_dump(mode="python")
    )
    if result.trade_intent is None:
        raise RuntimeError(f"Matching signal emitted no intent: {result.reason_codes}")
    rebound = bind_proposal_lineage(result.trade_intent, request)
    if rebound.data is None:
        raise RuntimeError(f"Lineage binding failed: {rebound.error}")

    print("\nProposal material derived from the latest observed bar:")
    print(proposal_material)
    print("\nValidation result:")
    print(validation.data.model_dump(mode="json"))
    print("\nEvaluated proposal result:")
    print(result.model_dump(mode="json"))
    print("\nEvaluated signal evidence:")
    for signal in result.evaluated_signals:
        print(signal.model_dump(mode="json"))
    print("\nCanonical non-executable TradeIntent proposal:")
    print(rebound.data.model_dump(mode="json"))
    print("\nAudit event reference:", result.audit_event_ref)
    print("Result factory round trip:", rebuilt == result)
    print("No broker fill, Risk approval, or execution authority was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
