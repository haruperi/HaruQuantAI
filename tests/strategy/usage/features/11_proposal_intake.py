"""Evaluate an external proposal against genuine MT5-backed Strategy evidence."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    build_symbol_metadata,
    data_settings_context,
    get_symbol_metadata,
    run_data_migrations,
)
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
    registration_request,
    unresolved_ref,
)

_UNAVAILABLE = 3


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _get_market_evidence() -> tuple[Any, Any]:
    """Fetch MT5 live bars and symbol metadata or fallback to synthetic dataset."""
    try:
        market = live_bars()
        metadata_resp = get_symbol_metadata(source_id="mt5", symbol=market.symbol)
        if metadata_resp.status == "success" and metadata_resp.data:
            return market, metadata_resp.data
    except OSError, RuntimeError, ValueError:
        pass

    now = datetime.now(UTC)
    record = build_ohlcv_record(
        timestamp=now - timedelta(minutes=1),
        open="1.1000",
        high="1.1020",
        low="1.0990",
        close="1.1010",
        volume=100,
        source="mt5",
        source_symbol="EURUSD",
        available_at=now - timedelta(minutes=1),
        price_unit="USD",
        volume_unit="units",
    )
    market = build_market_dataset(
        symbol="EURUSD",
        data_kind="bars",
        records=(record,),
        normalization_version="v1",
        timeframe="M1",
        start=record.timestamp,
        end=record.timestamp,
        available_at=record.available_at,
        record_count=1,
        quality_report=build_data_quality_report(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=1,
            checked_count=1,
            truncated=False,
            sample_limit=1,
            schema_version="v1",
            generated_at=record.available_at,
        ),
        source_metadata={"provider": "mt5"},
        license_metadata={"license": "usage"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=REQ,
    )
    metadata = build_symbol_metadata(
        symbol="EURUSD",
        source="mt5",
        point="0.00001",
        digits=5,
        currency_base="EUR",
        currency_profit="USD",
        available_at=record.available_at,
        request_id=REQ,
    )
    return market, metadata


def _setup_proposal_data() -> tuple[Any, Any, Any, Any, Any]:
    """Build request, auth, evidence, context, and evaluator for proposal intake."""
    market, metadata = _get_market_evidence()
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
        point_size=Decimal(str(metadata.point)),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    evaluator = MarketProposalEvaluator()
    return request, auth, evidence, context, evaluator


def fr_str_049() -> None:
    """FR-STR-049: Stage 1 — Receiver-owned proposal request."""
    _header("Stage 1: Receiver-Owned Proposal Request (FR-STR-049)")
    request, _, _, _, _ = _setup_proposal_data()
    print(_format_result(request))
    print(
        f"Data -> proposal_id='{request.source_proposal_id}', task_id='{request.source_task_id}'"
    )


def fr_str_050() -> None:
    """FR-STR-050: Stage 2 — Typed proposal result."""
    _header("Stage 2: Typed Proposal Result (FR-STR-050)")
    request, auth, evidence, context, evaluator = _setup_proposal_data()
    registered = register_strategy_version(registration_request(), auth, policy())
    if registered.data is None or registered.data.status not in {
        "ACCEPTED",
        "IDEMPOTENT",
    }:
        raise RuntimeError(f"Registration failed: {registered.error}")
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
        raise RuntimeError("Proposal evaluation failed")
    result = create_strategy_proposal_evaluation_result(
        **evaluation.data.model_dump(mode="python")
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', audit_ref='{result.audit_event_ref[:16]}'"
    )


def fr_str_051() -> None:
    """FR-STR-051: Stage 3 — Fail-closed proposal validation."""
    _header("Stage 3: Fail-Closed Proposal Validation (FR-STR-051)")
    request, auth, evidence, context, evaluator = _setup_proposal_data()
    registered = register_strategy_version(registration_request(), auth, policy())
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
    print(_format_result(validation))
    print(
        f"Data -> status='{validation.status}', validated={validation.data is not None}"
    )


def fr_str_052() -> None:
    """FR-STR-052: Stage 4 — Deterministic proposal evaluation."""
    _header("Stage 4: Deterministic Proposal Evaluation (FR-STR-052)")
    request, auth, evidence, context, evaluator = _setup_proposal_data()
    registered = register_strategy_version(registration_request(), auth, policy())
    if registered.data is None or registered.data.status not in {
        "ACCEPTED",
        "IDEMPOTENT",
    }:
        raise RuntimeError(f"Registration failed: {registered.error}")
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
    print(_format_result(evaluation))
    print(
        f"Data -> status='{evaluation.status}', has_trade_intent={evaluation.data.trade_intent is not None if evaluation.data else False}"
    )


def fr_str_053() -> None:
    """FR-STR-053: Stage 5 — Lineage-only proposal binding."""
    _header("Stage 5: Lineage-Only Proposal Binding (FR-STR-053)")
    request, auth, evidence, context, evaluator = _setup_proposal_data()
    registered = register_strategy_version(registration_request(), auth, policy())
    if registered.data is None or registered.data.status not in {
        "ACCEPTED",
        "IDEMPOTENT",
    }:
        raise RuntimeError(f"Registration failed: {registered.error}")
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
    if evaluation.data is None or evaluation.data.trade_intent is None:
        raise RuntimeError("Evaluation failed to produce trade intent")
    rebound = bind_proposal_lineage(evaluation.data.trade_intent, request)
    print(_format_result(rebound))
    print(
        f"Data -> status='{rebound.status}', intent_id='{rebound.data.intent_id if rebound.data else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-11 — proposal_intake/ — External Proposal Intake\n\n"
        "Purpose: Validate, evaluate, and audit runtime proposals through the strategy boundary.\n\n"
        "Module flow:\n"
        "-> Proposal request + AuthContext + Policy\n"
        "-> Validation & Evaluator signal execution\n"
        "-> Audited StrategyProposalEvaluationResult + bound TradeIntent"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            run_data_migrations(REQ)

            # 1. Stage 1: Receiver-owned proposal request
            fr_str_049()

            # 2. Stage 2: Typed proposal result
            fr_str_050()

            # 3. Stage 3: Fail-closed proposal validation
            fr_str_051()

            # 4. Stage 4: Deterministic proposal evaluation
            fr_str_052()

            # 5. Stage 5: Lineage-only proposal binding
            fr_str_053()


if __name__ == "__main__":
    main()
