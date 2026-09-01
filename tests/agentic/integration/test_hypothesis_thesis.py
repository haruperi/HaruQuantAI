"""Integration evidence for FEAT-AGT-13 chained to its real upstream inputs.

Exercises the documented dependency: the Technical Analyst (`FEAT-AGT-11`) and
the Simulation Interpreter (`FEAT-AGT-08`) produce real evidence packs, and the
Strategy Thesis Analyst consumes them to form a falsifiable hypothesis and a
non-executable thesis. Deliberation dissent (`FEAT-AGT-07`) travels through to
the thesis stance.

Nothing here reaches a broker, a provider, or a network: every receiver
operation and the agent-graph runtime are deterministic doubles.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
)
from app.agentic.agents.experimentation.simulation_interpreter import (
    interpret_analytics_evidence,
)
from app.agentic.agents.market_analysis.technical_analyst import (
    analyze_technical_context,
)
from app.agentic.agents.market_analysis.technical_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst import (
    develop_hypothesis,
    develop_strategy_thesis,
)
from app.agentic.deliberation import DissentRecord
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    NOW,
    TECHNICAL_ROLE_ID,
    build_interpreter_mandate,
    build_interpreter_manifest,
    build_technical_mandate,
    build_technical_role_manifest,
    build_thesis_mandate,
    build_thesis_role_manifest,
)

SCOPE = {"environment": "sandbox", "asset_class": "fx"}


def _task(task_id: str, workflow: str, objective: str, refs: tuple[str, ...]):
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": derive_stable_id("id", task_id),
            "workflow_name": workflow,
            "workflow_version": "1.0.0",
            "objective": objective,
            "input_refs": refs,
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": f"idem-{task_id}",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _profile():
    return build_model_profile(
        {
            "profile_id": "profile-market-analysis-a",
            "version": "1.0.0",
            "provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "region": "europe-west4",
            "credential_ref": "vault://agentic/gemini",
            "structured_output_mode": "json_schema",
            "max_context_tokens": 120_000,
            "max_output_tokens": 8_000,
            "max_latency_ms": 30_000,
            "max_cost_per_call": Decimal("0.50"),
            "retention_policy": "zero-retention",
            "training_use_permitted": False,
            "fallback_profile_id": None,
            "evaluation_state": "evaluated",
            "enabled": True,
        },
    )


class _Runtime:
    """Deterministic runtime returning per-node declared output."""

    def __init__(self, by_node: dict[str, dict[str, str]]) -> None:
        self.by_node = by_node

    def execute_node(self, node_id, profile, invocation):
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": dict(self.by_node[node_id]),
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 500,
                "latency_ms": 40,
                "cost": Decimal("0.02"),
            },
        )


class _Port:
    """Deterministic receiver-domain evidence port."""

    def fetch_market_evidence(self, instrument, timeframe):
        return {
            "dataset_ref": f"data.market_dataset:{instrument}-{timeframe}",
            "venue": "mt5-demo",
            "window_start": "2026-07-29T08:00:00Z",
            "window_end": "2026-07-29T12:00:00Z",
        }

    def fetch_quality_evidence(self, instrument):
        return {"report_ref": f"data.quality_report:{instrument}", "status": "passed"}

    def fetch_session_evidence(self, instrument):
        del instrument
        return {"session": "london", "tradable": "true"}

    def fetch_indicator_versions(self, indicators):
        return dict.fromkeys(indicators, "1.0.0")


TECHNICAL_OUTPUT = {
    "claim:trend": "Three consecutive higher lows on H1.",
    "confirmation:trend": "A close above the prior swing high confirms it.",
    "invalidation:trend": "A close below the 200-period EMA invalidates it.",
    "leakage:trend": "Evaluate using only bars closed before the decision time.",
    "uncertainty": "One session under passing quality.",
}

INTERPRETATION_OUTPUT = {
    "fact:analytics.report.sharpe": "The report states a Sharpe ratio of 1.24.",
    "inference:analytics.report.sharpe": "Unlikely to be noise alone.",
    "limitations": "One instrument only.",
    "uncertainty": "Six months, no holdout.",
}

HYPOTHESIS_OUTPUT = {
    "statement": "EURUSD trends persist through the London session open.",
    "asset_scope": "EURUSD",
    "horizon": "intraday",
    "mechanism": "Session-open liquidity concentrates directional order flow.",
    "prerequisites": "Continuous H1 coverage",
    "confounders": "Scheduled macro releases",
    "rejection_criterion": "No positive continuation across 200 sessions.",
    "leakage_constraints": "Use only bars closed before the session open.",
}

THESIS_OUTPUT = {
    "title": "London-open trend persistence",
    "summary": "Trends before the London open tend to persist briefly.",
    "stance": "supported",
    "signal:trend_state": "Direction of the prior three H1 swings.",
    "behaviour:trend_state": "Expected to continue for one to four hours.",
    "uncertainty": "One instrument, six months.",
    "next_test": "A walk-forward split across two further instruments.",
}


def _technical_pack():
    mandate = build_technical_mandate()
    registry = get_role_registry(mandate, (build_technical_role_manifest(),), NOW)
    tools = {
        name: build_tool_policy(
            {
                "tool_name": name,
                "version": "1.0.0",
                "owning_feature": "FEAT-AGT-11",
                "receiver_domain": name.split(".", maxsplit=1)[0],
                "public_operation": name.split(".", 1)[1],
                "request_schema_id": f"{name}.request.v1",
                "result_schema_id": f"{name}.result.v1",
                "permission_class": "read_evidence",
                "side_effect_class": "read_only",
                "eligible_roles": (TECHNICAL_ROLE_ID,),
                "scope": dict(SCOPE),
                "idempotent": True,
                "requires_approval": False,
                "max_input_bytes": 8_192,
                "max_output_bytes": 1_048_576,
                "timeout_seconds": 30,
                "max_calls_per_task": 8,
                "enabled": True,
            },
        )
        for name in get_registered_tool_names()
    }
    policy = build_agent_policy(
        {
            "role_id": TECHNICAL_ROLE_ID,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )
    return analyze_technical_context(
        registry,
        _task(
            "task-chain-technical", "analyze_technical_context", "Describe EURUSD.", ()
        ),
        mandate,
        policy,
        tools,
        _Port(),
        _Runtime({"analyze_technical_context": TECHNICAL_OUTPUT}),
        _profile(),
        "EURUSD",
        "H1",
        ("ema", "atr"),
        request_scope=dict(SCOPE),
        at_time=NOW,
    )


def _interpretation():
    registry = get_role_registry(
        build_interpreter_mandate(),
        (build_interpreter_manifest(),),
        NOW,
    )
    return interpret_analytics_evidence(
        registry,
        _task("task-chain-interp", "interpret_evidence", "Explain the report.", ()),
        {
            "evidence_ref": "analytics.performance_report:run-0001",
            "schema_id": "analytics.performance_report.v1",
            "contract_version": "v1",
        },
        _Runtime({"interpret_evidence": INTERPRETATION_OUTPUT}),
        _profile(),
        at_time=NOW,
    )


def test_specialist_packs_feed_a_falsifiable_hypothesis_and_thesis() -> None:
    # 1. Two real upstream features produce genuine typed evidence.
    technical = _technical_pack()
    interpretation = _interpretation()
    assert technical.status == "ok"
    assert interpretation.status == "ok"

    packs = {
        f"agentic.technical_pack:{technical.payload.pack_id}": {
            f"claim:{key}": value for key, value in technical.payload.claims.items()
        },
        f"agentic.run_interpretation:{interpretation.payload.interpretation_id}": {
            f"fact:{key}": value
            for key, value in interpretation.payload.measured_facts.items()
        },
    }

    # 2. The thesis analyst forms a falsifiable hypothesis from those packs.
    registry = get_role_registry(
        build_thesis_mandate(),
        (build_thesis_role_manifest(),),
        NOW,
    )
    task = _task(
        "task-chain-thesis",
        "develop_strategy_thesis",
        "Form a testable thesis about EURUSD session behaviour.",
        tuple(sorted(packs)),
    )
    hypothesis_result = develop_hypothesis(
        registry,
        task,
        packs,
        _Runtime({"develop_hypothesis": HYPOTHESIS_OUTPUT}),
        _profile(),
        at_time=NOW,
    )
    assert hypothesis_result.status == "ok"
    hypothesis = hypothesis_result.payload
    assert hypothesis.rejection_criterion
    # Evidence refs are the packs actually supplied, not a model claim.
    assert hypothesis.evidence_refs == tuple(sorted(packs))

    # 3. Synthesis carries the upstream evidence into a non-executable thesis.
    thesis_result = develop_strategy_thesis(
        registry,
        task,
        (hypothesis,),
        packs,
        _Runtime({"develop_strategy_thesis": THESIS_OUTPUT}),
        _profile(),
        at_time=NOW,
    )
    assert thesis_result.status == "ok"
    thesis = thesis_result.payload
    assert thesis.stance == "supported"
    assert thesis.hypothesis_ids == (hypothesis.hypothesis_id,)
    assert thesis.supporting_evidence == tuple(sorted(packs))

    # 4. The thesis expresses no order, price, size, or approval anywhere.
    flat = str(thesis.model_dump(mode="json")).lower()
    for token in ("position size", "entry price", "approved", "place the order"):
        assert token not in flat


def test_unresolved_dissent_reaches_the_thesis_stance() -> None:
    technical = _technical_pack()
    packs = {
        f"agentic.technical_pack:{technical.payload.pack_id}": {
            f"claim:{key}": value for key, value in technical.payload.claims.items()
        },
    }
    registry = get_role_registry(
        build_thesis_mandate(),
        (build_thesis_role_manifest(),),
        NOW,
    )
    task = _task(
        "task-chain-contested",
        "develop_strategy_thesis",
        "Form a thesis where specialists disagree.",
        tuple(sorted(packs)),
    )
    hypothesis = develop_hypothesis(
        registry,
        task,
        packs,
        _Runtime({"develop_hypothesis": HYPOTHESIS_OUTPUT}),
        _profile(),
        at_time=NOW,
    ).payload

    dissent = DissentRecord.model_validate(
        {
            "dissent_id": "d-chain",
            "task_id": task.task_id,
            "dissenting_role_id": "quantitative_analyst",
            "statement": "The sample cannot separate signal from noise.",
            "basis": "insufficient_evidence",
            "targets_claim_id": None,
            "unresolved": True,
        },
    )
    thesis = develop_strategy_thesis(
        registry,
        task,
        (hypothesis,),
        packs,
        _Runtime({"develop_strategy_thesis": THESIS_OUTPUT}),
        _profile(),
        dissent=(dissent,),
        at_time=NOW,
    ).payload

    # The model declared "supported"; the deliberation record overrode it.
    assert thesis.stance == "contested"
    assert thesis.retained_conflicts
    assert "quantitative_analyst" in thesis.retained_conflicts[0]
