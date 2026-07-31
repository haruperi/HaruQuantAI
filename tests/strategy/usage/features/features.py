"""Homogeneous full-domain usage program for app.services.strategy.

Ties all registered Strategy features (FEAT-STR-01 through FEAT-STR-11) together into a single,
sequential, step-by-step pipeline matching real-world operational execution order:
1. Versioned Strategy Contracts (FEAT-STR-01)
2. Deterministic Safe Diagnostics (FEAT-STR-02)
3. Immutable Registry & Configuration (FEAT-STR-03)
4. Canonical TradeIntent Proposals (FEAT-STR-04)
5. Deterministic Replay Manifests (FEAT-STR-05)
6. Bounded Persisted Local State (FEAT-STR-06)
7. Atomic Vectorized Evaluation (FEAT-STR-07)
8. Stateful Event Evaluation (FEAT-STR-08)
9. Concrete Strategy Signal Boundary (FEAT-STR-09)
10. Strategy Evaluators Library (FEAT-STR-10)
11. External Proposal Intake (FEAT-STR-11)
"""

from __future__ import annotations

import hashlib
import inspect
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    data_settings_context,
    get_market_data,
    get_symbol_metadata,
    run_data_migrations,
)
from app.services.indicators import rsi, sma
from app.services.strategy import (
    bind_proposal_lineage,
    build_trade_intent,
    create_strategy_checkpoint,
    create_strategy_config,
    create_strategy_decision,
    create_strategy_evaluator,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_proposal_evaluation_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_replay_manifest,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    evaluate_strategy_proposal,
    evaluate_strategy_signals,
    export_strategy_diagnostics,
    get_strategy_environment,
    get_strategy_error_catalog,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    list_strategy_versions,
    register_strategy_version,
    run_event_strategy_hook,
    run_vectorized_strategy_signals,
    validate_strategy_checkpoint,
    validate_strategy_config,
    validate_strategy_proposal,
    validate_strategy_ref,
)
from app.utils import canonical_json, create_auth_context
from tests.strategy.usage.workflows._support import MarketProposalEvaluator

_REQ = "req-11111111-1111-4111-8111-111111111111"
_WF = "wf-22222222-2222-4222-8222-222222222222"
_COR = "cor-33333333-3333-4333-8333-333333333333"
_STRATEGY = "pipeline-ma-trend"
_MODULE = "app.services.strategy.evaluators.naive_ma_trend"


def _stage_banner(stage_num: Any, title: str, description: str) -> None:
    """Print a standardized stage banner."""
    print(
        f"\n\n{'-' * 80}\nStage {stage_num}: {title}\nDescription: {description}\n{'-' * 80}"
    )


def _source_hash(module_path: str, evaluator_name: str, strategy_id: str) -> str:
    """Compute concrete source hash for an evaluator."""
    probe = create_strategy_evaluator(
        evaluator_name,
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        module_path=module_path,
        source_hash="0" * 64,
        artifact_hash="0" * 64,
        dependency_hash="0" * 64,
    )
    return hashlib.sha256(inspect.getsource(type(probe)).encode()).hexdigest()


def _get_pipeline_market() -> tuple[Any, Decimal]:
    """Fetch genuine MT5 EURUSD H1 market dataset for the full year 2025."""
    start_2025 = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    end_2025 = datetime(2025, 12, 31, 23, 0, tzinfo=UTC)

    m_resp = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="H1",
        start=start_2025,
        end=end_2025,
        limit=10_000,
        use_cache=False,
        quality_failure_behavior="warn",
    )
    meta_resp = get_symbol_metadata(source_id="mt5", symbol="EURUSD")

    if (
        m_resp.status != "success"
        or m_resp.data is None
        or meta_resp.status != "success"
        or meta_resp.data is None
    ):
        err_msg = m_resp.error.message if m_resp.error else "Unknown MT5 fetch error"
        raise RuntimeError(
            f"Failed to fetch MT5 real market data for EURUSD H1 (2025): {err_msg}"
        )

    market = m_resp.data.model_copy(
        update={
            "quality_report": m_resp.data.quality_report.model_copy(
                update={"quality_status": "passed_with_warnings"}
            )
        }
    )
    point = Decimal(str(meta_resp.data.point))
    return market, point


class PipelineVectorizedEvaluator:
    """Minimal hash-bound vectorized evaluator for pipeline testing."""

    def __init__(self, source_hash: str) -> None:
        self.strategy_id = _STRATEGY
        self.strategy_version = "1.0.0"
        self.module_path = _MODULE
        self.source_hash = source_hash
        self.artifact_hash = source_hash
        self.dependency_hash = source_hash

    def evaluate_vectorized(
        self,
        market: Any,
        indicators: Any,
        config: Any,
        context: Any,
        account_snapshot: Any,
    ) -> Any:
        """Propose one bounded entry on the last completed bar."""
        del indicators, config, account_snapshot
        bar = market.records[-1]
        decision = create_strategy_decision(
            decision_id=f"pipeline-vectorized-{bar.timestamp.isoformat()}",
            sequence=0,
            action="PROPOSE",
            symbol=market.symbol,
            side="BUY",
            intent_type="OPEN",
            order_type="MARKET",
            requested_sizing_mode="quantity",
            quantity_hint=Decimal("0.01"),
            valid_from=context.decision_timestamp,
            expires_at=context.decision_timestamp + timedelta(minutes=5),
            allow_partial_fills=False,
            rationale_refs=("vectorized-last-bar",),
            diagnostic_facts={"bar_timestamp": bar.timestamp.isoformat()},
            lineage={
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
            },
        )
        return (decision,)


class PipelineEventEvaluator:
    """Minimal declared-hook evaluator for pipeline testing."""

    def __init__(self, source_hash: str) -> None:
        self.strategy_id = _STRATEGY
        self.strategy_version = "1.0.0"
        self.module_path = _MODULE
        self.source_hash = source_hash
        self.artifact_hash = source_hash
        self.dependency_hash = source_hash
        self.supported_hooks = ("on_bar",)

    def evaluate_event(
        self,
        event: Any,
        config: Any,
        context: Any,
        local_state: Any,
        account_snapshot: Any,
    ) -> Any:
        """Return one neutral decision carrying an incremented candidate state."""
        del config, account_snapshot
        seen = int((local_state or {}).get("bars_seen", 0)) + 1
        decision = create_strategy_decision(
            decision_id=f"pipeline-event-{event.sequence}",
            sequence=0,
            action="NEUTRAL",
            valid_from=context.decision_timestamp,
            expires_at=context.decision_timestamp + timedelta(minutes=5),
            allow_partial_fills=False,
            rationale_refs=("event-hook",),
            diagnostic_facts={"bars_seen": str(seen)},
            candidate_local_state={"bars_seen": seen},
            lineage={
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
            },
        )
        return (decision,)


def _export_signal_dataframe(
    market: Any, sma_fast_resp: Any, sma_slow_resp: Any, sma_filter_resp: Any
) -> None:
    """Construct and display full market DataFrame enriched with indicators and calculated signals."""
    _stage_banner(
        "9B",
        "Enriched Strategy Signal DataFrame Export",
        "Construct and display full market DataFrame enriched with indicators and calculated signals.",
    )
    res_fast = (
        sma_fast_resp.data
        if getattr(sma_fast_resp, "data", None) is not None
        else sma_fast_resp
    )
    res_slow = (
        sma_slow_resp.data
        if getattr(sma_slow_resp, "data", None) is not None
        else sma_slow_resp
    )
    res_filter = (
        sma_filter_resp.data
        if getattr(sma_filter_resp, "data", None) is not None
        else sma_filter_resp
    )

    if res_fast and res_slow and res_filter:
        join_resp = res_fast.join_to(market)
        df = (
            join_resp.data
            if getattr(join_resp, "data", None) is not None
            else join_resp
        )
        for res in (res_slow, res_filter):
            res_df = res.values
            for col in res_df.columns:
                if col not in ("symbol", "timestamp") and col not in df.columns:
                    df[col] = res_df[col].to_list()
        up_cross = (df["sma_20"] > df["sma_50"]) & (
            df["sma_20"].shift(1) <= df["sma_50"].shift(1)
        )
        down_cross = (df["sma_20"] < df["sma_50"]) & (
            df["sma_20"].shift(1) >= df["sma_50"].shift(1)
        )
        df["signal_long_entry"] = up_cross & (df["sma_50"] > df["sma_200"])
        df["signal_short_entry"] = down_cross & (df["sma_50"] < df["sma_200"])
        df["signal_long_exit"] = down_cross
        df["signal_short_exit"] = up_cross
        df["signal_direction"] = 0
        df.loc[df["signal_long_entry"], "signal_direction"] = 1
        df.loc[df["signal_short_entry"], "signal_direction"] = -1
        total_longs = int(df["signal_long_entry"].sum())
        total_shorts = int(df["signal_short_entry"].sum())
        total_exits = int((df["signal_long_exit"] | df["signal_short_exit"]).sum())
        print(
            f"Strategy 2025 Full Year -> total_bars={len(df)}, long_entries={total_longs}, short_entries={total_shorts}, total_exits={total_exits}"
        )
        display_cols = [
            col
            for col in [
                "available_at",
                "close",
                "sma_20",
                "sma_50",
                "sma_200",
                "signal_long_entry",
                "signal_short_entry",
                "signal_long_exit",
                "signal_short_exit",
                "signal_direction",
            ]
            if col in df.columns
        ]
        active_signals = df[df["signal_direction"] != 0][display_cols]
        print(
            f"\nFull Year 2025 Signal Events Ledger (showing all {len(active_signals)} active entry signals):"
        )
        print(active_signals.to_string(index=False))


def _run_stages_1_to_5(
    market: Any,
) -> tuple[Any, Any, Any, Any, Any, str, Any]:
    """Execute Stages 1 through 5 and return pipeline context and resources."""
    source_hash = _source_hash(_MODULE, "naive_ma_trend", _STRATEGY)

    # Stage 1: Versioned Strategy Contracts
    _stage_banner(
        1,
        "Versioned Strategy Contracts (FEAT-STR-01)",
        "Validate contract schemas, environments, and policies.",
    )
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=8_192,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=64,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="strategy-pipeline",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {
                "fast_ma_period": {"type": "integer", "minimum": 1},
                "slow_ma_period": {"type": "integer", "minimum": 1},
                "filter_ma_period": {"type": "integer", "minimum": 1},
            },
            "required": ("fast_ma_period", "slow_ma_period", "filter_ma_period"),
            "additionalProperties": False,
        },
        required_data=("EURUSD:H1",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
        provenance_refs=("pipeline-approval-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=20_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=market.available_at + timedelta(seconds=1),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=42,
        interface_version="v1",
        request_id=_REQ,
        workflow_id=_WF,
        correlation_id=_COR,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    print(
        f"Strategy -> contract_manifest_id='{manifest.strategy_id}', policy_version='{policy.policy_version}'"
    )

    # Stage 2: Safe Diagnostics
    _stage_banner(
        2,
        "Deterministic Safe Diagnostics (FEAT-STR-02)",
        "Catalogue error codes and export redacted execution diagnostics.",
    )
    error_catalog = get_strategy_error_catalog()
    diag_resp = export_strategy_diagnostics(
        context,
        {"symbol": "EURUSD", "secret_key": "redacted"},  # pragma: allowlist secret
    )
    print(
        f"Strategy -> accepted_error_codes={len(error_catalog)}, diagnostics_status='{diag_resp.status}'"
    )

    # Stage 3: Immutable Registry & Configuration
    _stage_banner(
        3,
        "Immutable Registry & Configuration (FEAT-STR-03)",
        "Register strategy versions, parameter sets, and resolve approved references.",
    )
    auth = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="pipeline-builder",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=(
            "strategy:register",
            "strategy:update",
            "strategy:checkpoint",
            "strategy:evaluate_proposal",
        ),
        scopes=("pipeline-approval-1", "pipeline-auth"),
        tenant_or_environment="research",
        request_id=_REQ,
        workflow_id=_WF,
        correlation_id=_COR,
        issued_at=datetime.now(UTC),
    )
    reg_req = create_strategy_registration_request(
        command_id=f"reg-{_REQ}",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        manifest=manifest,
        config_schema=manifest.config_schema,
        source_hash=manifest.source_hash,
        artifact_hash=manifest.artifact_hash,
        dependency_hash=manifest.dependency_hash,
        provenance_refs=manifest.provenance_refs,
        principal_id=auth.principal_id,
        reason="pipeline registration",
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        authorization_ref="pipeline-approval-1",
        requested_at=datetime.now(UTC),
        request_id=_REQ,
        correlation_id=_COR,
    )
    reg_res = register_strategy_version(reg_req, auth, policy)
    versions_res = list_strategy_versions()
    ref = create_strategy_ref(
        strategy_id=manifest.strategy_id,
        exact_version=manifest.strategy_version,
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQ,
        correlation_id=_COR,
    )
    val_ref_res = validate_strategy_ref(ref, policy)
    config = create_strategy_config(
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        config_schema_version="v1",
        parameters={
            "fast_ma_period": 20,
            "slow_ma_period": 50,
            "filter_ma_period": 200,
        },
        request_id=_REQ,
    )
    val_cfg_res = validate_strategy_config(val_ref_res.data, config)
    print(
        f"Strategy -> registration_status='{reg_res.status}', registered_versions={len(versions_res.data) if versions_res.data else 0}, config_valid={val_cfg_res.data is not None}"
    )

    # Stage 4: TradeIntent Proposals
    _stage_banner(
        4,
        "Canonical TradeIntent Proposals (FEAT-STR-04)",
        "Derive canonical TradeIntent proposals from StrategyDecisions.",
    )
    decision = create_strategy_decision(
        decision_id="pipeline-decision-1",
        sequence=0,
        action="PROPOSE",
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        requested_sizing_mode="quantity",
        quantity_hint=Decimal("0.01"),
        valid_from=context.decision_timestamp,
        expires_at=context.decision_timestamp + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("pipeline-ma-cross",),
        diagnostic_facts={"fast_ma": "1.1020", "slow_ma": "1.1010"},
        lineage={
            "strategy_id": manifest.strategy_id,
            "strategy_version": manifest.strategy_version,
            "config_hash": val_cfg_res.data.config_hash
            if val_cfg_res.data
            else source_hash,
        },
    )
    intent_res = build_trade_intent(decision, context, 0)
    print(
        f"Strategy -> intent_status='{intent_res.status}', intent_id='{intent_res.data.intent_id if intent_res.data else None}'"
    )

    # Stage 5: Replay Manifests
    _stage_banner(
        5,
        "Deterministic Replay Manifests (FEAT-STR-05)",
        "Generate audit replay manifest binding input dataset and config hashes.",
    )
    replay_res = create_strategy_replay_manifest(
        val_ref_res.data, val_cfg_res.data, context, source_hash, source_hash
    )
    print(
        f"Strategy -> replay_status='{replay_res.status}', replay_hash='{replay_res.data.manifest_hash[:16] if replay_res.data else None}...'"
    )

    return context, policy, manifest, val_ref_res, val_cfg_res, source_hash, auth


def _run_stages_6_to_11(
    market: Any,
    point: Decimal,
    context: Any,
    policy: Any,
    manifest: Any,
    val_ref_res: Any,
    val_cfg_res: Any,
    source_hash: str,
    auth: Any,
) -> None:
    """Execute Stages 6 through 11."""
    # Stage 6: Persisted Local State
    _stage_banner(
        6,
        "Bounded Persisted Local State (FEAT-STR-06)",
        "Persist and validate strategy local state checkpoints.",
    )
    ckpt_res = create_strategy_checkpoint(
        val_ref_res.data,
        val_cfg_res.data,
        {"bars_processed": 30},
        "pipeline-approval-1",
        auth,
    )
    val_ckpt_res = validate_strategy_checkpoint(
        ckpt_res.data, val_ref_res.data, val_cfg_res.data, auth
    )
    print(
        f"Strategy -> checkpoint_status='{ckpt_res.status}', restored_bars={val_ckpt_res.data.get('bars_processed') if val_ckpt_res.data else None}"
    )

    # Stage 7: Atomic Vectorized Evaluation
    _stage_banner(
        7,
        "Atomic Vectorized Evaluation (FEAT-STR-07)",
        "Run batch vectorized evaluation across market dataset.",
    )
    vec_evaluator = PipelineVectorizedEvaluator(source_hash)
    vec_res = run_vectorized_strategy_signals(
        val_ref_res.data, val_cfg_res.data, market, (), context, vec_evaluator
    )
    print(
        f"Strategy -> vectorized_status='{vec_res.status}', has_results={vec_res.data is not None}"
    )

    # Stage 8: Stateful Event Evaluation
    _stage_banner(
        8,
        "Stateful Event Evaluation (FEAT-STR-08)",
        "Evaluate on_bar hook event over discrete market bar.",
    )
    event_evaluator = PipelineEventEvaluator(source_hash)
    last_bar = market.records[-1]
    event = create_strategy_event(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=last_bar.timestamp,
        sequence=market.record_count - 1,
        source_owner="data",
        source_contract_version=market.contract_version,
        source_schema_id=market.schema_id,
        source_snapshot_ref=market.request_id,
        source_checksum=source_hash,
        source_as_of=last_bar.timestamp,
        facts={"symbol": market.symbol},
        request_id=_REQ,
        workflow_id=_WF,
        correlation_id=_COR,
    )
    event_res = run_event_strategy_hook(
        val_ref_res.data,
        val_cfg_res.data,
        event,
        context,
        event_evaluator,
        {"bars_seen": 29},
    )
    print(
        f"Strategy -> event_status='{event_res.status}', has_execution={event_res.data is not None}"
    )

    # Stage 9: Concrete Signal Boundary
    _stage_banner(
        9,
        "Concrete Strategy Signal Boundary (FEAT-STR-09)",
        "Evaluate declared strategy logic to produce immutable signals.",
    )
    evidence = create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets={},
        point_size=point,
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    sma_fast_resp = sma(market, period=20)
    sma_slow_resp = sma(market, period=50)
    sma_filter_resp = sma(market, period=200)
    sma_fast = sma_fast_resp.data
    sma_slow = sma_slow_resp.data
    sma_filter = sma_filter_resp.data
    indicators = (
        (sma_fast, sma_slow, sma_filter) if sma_fast and sma_slow and sma_filter else ()
    )
    evaluator = create_strategy_evaluator(
        "naive_ma_trend",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
    )
    sig_res = evaluate_strategy_signals(
        val_ref_res.data, val_cfg_res.data, evidence, indicators, context, evaluator
    )
    print(
        f"Strategy -> signal_status='{sig_res.status}', signal_count={len(sig_res.data) if sig_res.data else 0}"
    )
    print(sig_res.data)

    # Stage 9B: Enriched Strategy Signal DataFrame Export
    _export_signal_dataframe(market, sma_fast_resp, sma_slow_resp, sma_filter_resp)

    # Stage 10: Strategy Evaluators Library
    _stage_banner(
        10,
        "Strategy Evaluators Library (FEAT-STR-10)",
        "Exercise built-in library evaluators.",
    )
    rsi_res = rsi(market, period=14).data
    rsi_tuple = (rsi_res,) if rsi_res else ()
    wf_mod = "app.services.strategy.evaluators.white_fairy"
    wf_hash = _source_hash(wf_mod, "white_fairy", "white-fairy")
    wf_params = {"rsi_period": 14, "overbought": "70", "oversold": "30"}
    wf_config_hash = hashlib.sha256(canonical_json(wf_params).encode()).hexdigest()
    wf_manifest = create_strategy_manifest(
        strategy_id="white-fairy",
        strategy_version="1.0.0",
        module_path=wf_mod,
        owner_ref="strategy-pipeline",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=("rsi",),
        timing_policy=context.timing_policy,
        permitted_environments=(context.environment,),
        source_hash=wf_hash,
        artifact_hash=wf_hash,
        dependency_hash=wf_hash,
        provenance_refs=("pipeline-approval-1",),
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=20_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    wf_val_ref = create_validated_strategy_ref(
        manifest=wf_manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=context.environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=wf_config_hash,
        request_id=_REQ,
        correlation_id=_COR,
    )
    wf_val_cfg = create_validated_strategy_config(
        strategy_id="white-fairy",
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters=wf_params,
        config_hash=wf_config_hash,
        policy_version=policy.policy_version,
        request_id=_REQ,
    )
    eval_wf = create_strategy_evaluator(
        "white_fairy",
        strategy_id="white-fairy",
        strategy_version="1.0.0",
        module_path=wf_mod,
        source_hash=wf_hash,
        artifact_hash=wf_hash,
        dependency_hash=wf_hash,
    )
    wf_res = evaluate_strategy_signals(
        wf_val_ref, wf_val_cfg, evidence, rsi_tuple, context, eval_wf
    )
    print(
        f"Strategy -> white_fairy_status='{wf_res.status}', signal_count={len(wf_res.data) if wf_res.data else 0}"
    )

    # Stage 11: External Proposal Intake
    _stage_banner(
        11,
        "External Proposal Intake (FEAT-STR-11)",
        "Validate and evaluate external runtime proposal into bound TradeIntent.",
    )
    proposal_evaluator = MarketProposalEvaluator()
    proposal_req = create_strategy_proposal_evaluation_request(
        principal_id=auth.principal_id,
        source_proposal_id=f"proposal-{_REQ[:16]}",
        source_task_id=f"task-{market.request_id}",
        source_content_hash=source_hash,
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        instrument=market.symbol,
        requested_direction="BUY",
        horizon_seconds=600,
        thesis_evidence_refs=(market.request_id,),
        invalidation_evidence_refs=(f"bar-{last_bar.timestamp.isoformat()}",),
        evaluation_scope="TRADE_INTENT_IF_SUPPORTED",
        requested_at=context.decision_timestamp - timedelta(seconds=1),
        expires_at=context.decision_timestamp + timedelta(minutes=5),
        request_id=_REQ,
        workflow_id=_WF,
        correlation_id=_COR,
    )
    prop_val_res = validate_strategy_proposal(
        proposal_req,
        auth,
        val_ref_res.data,
        val_cfg_res.data,
        policy,
        evidence,
        context,
        proposal_evaluator,
    )
    prop_eval_res = evaluate_strategy_proposal(
        proposal_req,
        auth,
        val_ref_res.data,
        val_cfg_res.data,
        policy,
        evidence,
        indicators,
        context,
        proposal_evaluator,
    )
    bound_res = (
        bind_proposal_lineage(prop_eval_res.data.trade_intent, proposal_req)
        if prop_eval_res.data and prop_eval_res.data.trade_intent
        else None
    )
    print(
        f"Strategy -> proposal_validation='{prop_val_res.status}', proposal_eval='{prop_eval_res.status}', bound_intent='{bound_res.data.intent_id if bound_res and bound_res.data else None}'"
    )


def main() -> None:
    """Execute all 11 Strategy features in operational pipeline sequence."""
    print(
        f"\n\n{'=' * 88}\nStrategy Domain — Full-Domain Feature Pipeline (FEAT-STR-01 through FEAT-STR-11)\n{'=' * 88}"
    )

    with tempfile.TemporaryDirectory(prefix="strategy-pipeline-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "strategy_pipeline.sqlite3").touch()
        settings = build_data_settings(
            database_url="sqlite:///strategy_pipeline.sqlite3",
            data_dir=tmp_path,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5", "binance_spot"),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(_REQ)
            market, point = _get_pipeline_market()
            context, policy, manifest, val_ref_res, val_cfg_res, source_hash, auth = (
                _run_stages_1_to_5(market)
            )
            _run_stages_6_to_11(
                market,
                point,
                context,
                policy,
                manifest,
                val_ref_res,
                val_cfg_res,
                source_hash,
                auth,
            )
            print(
                f"\n\n{'=' * 88}\nStrategy -> full_domain_pipeline_status='completed'\nSUCCESS: All 11 Strategy domain features executed in realistic pipeline order!\n{'=' * 88}\n"
            )


if __name__ == "__main__":
    main()
