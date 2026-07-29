"""Executable FEAT-AGT-13 Strategy Thesis Analyst usage example.

Demonstrates both registered public operations through the documented API. The
agent-graph runtime is the deterministic in-repo double, so what runs is the
falsifiability, non-execution, and conflict-retention discipline — not real
reasoning.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.agentic import build_agent_task, build_model_profile, get_role_registry
from app.agentic.agents.strategy_desk.strategy_thesis_analyst import (
    build_strategy_thesis,
    develop_hypothesis,
    develop_strategy_thesis,
)
from app.agentic.deliberation import DissentRecord
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agentic.fixtures import (
    build_thesis_mandate,
    build_thesis_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-thesis-usage")

EVIDENCE_PACKS = {
    "agentic.technical_pack:EURUSD-H1": {
        "claim:trend": "Three consecutive higher lows on H1.",
        "invalidation:trend": "A close below the 200-period EMA.",
    },
    "agentic.run_interpretation:run-0001": {
        "fact:sharpe": "The report states a Sharpe ratio of 1.24.",
    },
}

HYPOTHESIS_OUTPUT = {
    "statement": "EURUSD trends persist through the London session open.",
    "asset_scope": "EURUSD\nmajor FX pairs on MT5 demo",
    "horizon": "intraday, one to four hours",
    "mechanism": "Session-open liquidity concentrates directional order flow.",
    "prerequisites": "Continuous H1 coverage\nVerified session calendar",
    "confounders": "Scheduled macro releases\nMonth-end rebalancing flow",
    "rejection_criterion": "No positive continuation across 200 sampled sessions.",
    "leakage_constraints": "Use only bars closed before the session open.",
}

THESIS_OUTPUT = {
    "title": "London-open trend persistence",
    "summary": "Trends observed before the London open tend to persist briefly.",
    "stance": "supported",
    "signal:trend_state": "Direction of the prior three H1 swings.",
    "behaviour:trend_state": "Expected to continue for one to four hours.",
    "assumptions": "Session calendar is accurate.",
    "uncertainty": "One instrument, one session, six months of observations.",
    "next_test": "A walk-forward split across two further instruments.",
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, output=None, status="ok", reasons=()):
        self.output = output
        self.status = status
        self.reasons = reasons
        self.invocations = []

    def execute_node(self, node_id, profile, invocation):
        """Return a reproducible outcome for one node execution."""
        del node_id
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.output,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 700,
                "latency_ms": 55,
                "cost": Decimal("0.04"),
            },
        )


def make_profile():
    """Build the evaluated model profile."""
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


def make_task():
    """Build the bounded governed thesis task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "develop_strategy_thesis",
            "workflow_version": "1.0.0",
            "objective": "Form a testable thesis about EURUSD session behaviour.",
            "input_refs": tuple(sorted(EVIDENCE_PACKS)),
            "principal_id": "operator-owner",
            "scope": {"environment": "sandbox"},
            "deadline_at": NOW + timedelta(minutes=20),
            "idempotency_key": "idem-thesis-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def make_registry():
    """Build the validated registry enabling the thesis analyst."""
    return get_role_registry(
        build_thesis_mandate(),
        (build_thesis_role_manifest(),),
        NOW,
    )


def make_dissent(unresolved=True):
    """Build one preserved dissent record."""
    return DissentRecord.model_validate(
        {
            "dissent_id": "d-1",
            "task_id": TASK_ID,
            "dissenting_role_id": "quantitative_analyst",
            "statement": "The sample is too small to separate signal from noise.",
            "basis": "insufficient_evidence",
            "targets_claim_id": None,
            "unresolved": unresolved,
        },
    )


def fr_agentic_037() -> None:
    """FR-AGENTIC-037: A hypothesis is falsifiable."""
    _header(
        "FR-AGENTIC-037: A hypothesis is falsifiable and binds asset scope, "
        "horizon, evidence, mechanism, prerequisites, confounders, and a "
        "rejection criterion."
    )

    result = develop_hypothesis(
        make_registry(),
        make_task(),
        EVIDENCE_PACKS,
        DeterministicRuntime(output=dict(HYPOTHESIS_OUTPUT)),
        make_profile(),
        at_time=NOW,
    )
    h = result.payload
    print(f"  statement:    {h.statement}")
    print(f"  asset scope:  {h.asset_scope}")
    print(f"  horizon:      {h.horizon}")
    print(f"  mechanism:    {h.mechanism}")
    print(f"  prerequisites:{h.prerequisites}")
    print(f"  confounders:  {h.confounders}")
    print(f"  REJECTED IF:  {h.rejection_criterion}")
    print(f"  evidence:     {h.evidence_refs}")

    poisoned = dict(HYPOTHESIS_OUTPUT)
    poisoned["evidence_refs"] = "agentic.invented_pack:fabricated"
    forged = develop_hypothesis(
        make_registry(),
        make_task(),
        EVIDENCE_PACKS,
        DeterministicRuntime(output=poisoned),
        make_profile(),
        at_time=NOW,
    ).payload
    print(f"  model-claimed evidence ignored: {forged.evidence_refs}")

    empty = develop_hypothesis(
        make_registry(),
        make_task(),
        {},
        DeterministicRuntime(output=dict(HYPOTHESIS_OUTPUT)),
        make_profile(),
        at_time=NOW,
    )
    print(f"  no evidence -> {empty.status} ({empty.reasons[0]})")


def fr_agentic_038() -> None:
    """FR-AGENTIC-038: A thesis is not a plan."""
    _header(
        "FR-AGENTIC-038: A strategy thesis describes signals and intended "
        "behaviour but contains no executable code, broker command, approval, "
        "or authoritative size."
    )

    hypothesis = develop_hypothesis(
        make_registry(),
        make_task(),
        EVIDENCE_PACKS,
        DeterministicRuntime(output=dict(HYPOTHESIS_OUTPUT)),
        make_profile(),
        at_time=NOW,
    ).payload
    thesis = develop_strategy_thesis(
        make_registry(),
        make_task(),
        (hypothesis,),
        EVIDENCE_PACKS,
        DeterministicRuntime(output=dict(THESIS_OUTPUT)),
        make_profile(),
        at_time=NOW,
    ).payload

    print(f"  title:    {thesis.title}")
    print(f"  stance:   {thesis.stance}")
    for signal, description in thesis.signals.items():
        print(f"  signal    [{signal}] {description}")
        print(f"  behaviour [{signal}] {thesis.intended_behaviour[signal]}")
    print(f"  next test: {thesis.next_test}")

    for label, text in (
        ("approval", "The thesis is approved for live trading."),
        ("position size", "Use a position size of two lots."),
        ("entry price", "Set the entry price at 1.0850."),
        ("executable code", "def signal(df): pass"),
    ):
        try:
            build_strategy_thesis({**thesis.model_dump(), "summary": text})
            outcome = f"ERROR: {label} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"{label} correctly rejected"
        print(f"  {outcome}")


def fr_agentic_039() -> None:
    """FR-AGENTIC-039: Conflict is retained; agreement does not promote."""
    _header(
        "FR-AGENTIC-039: Thesis synthesis retains conflicting evidence and does "
        "not promote a proposal solely because agents agree."
    )

    hypothesis = develop_hypothesis(
        make_registry(),
        make_task(),
        EVIDENCE_PACKS,
        DeterministicRuntime(output=dict(HYPOTHESIS_OUTPUT)),
        make_profile(),
        at_time=NOW,
    ).payload

    def synth(dissent, output=None):
        return develop_strategy_thesis(
            make_registry(),
            make_task(),
            (hypothesis,),
            EVIDENCE_PACKS,
            DeterministicRuntime(output=dict(output or THESIS_OUTPUT)),
            make_profile(),
            dissent=dissent,
            at_time=NOW,
        ).payload

    agreed = synth(())
    print(
        f"  no dissent:        stance={agreed.stance} "
        f"conflicts={len(agreed.retained_conflicts)}"
    )

    contested = synth((make_dissent(unresolved=True),))
    print(
        f"  unresolved dissent:stance={contested.stance} "
        f"conflicts={len(contested.retained_conflicts)}"
    )
    print(f"    retained: {contested.retained_conflicts[0]}")
    print("  The model declared 'supported'; the unresolved conflict overrode it.")

    silenced = dict(THESIS_OUTPUT)
    silenced["retained_conflicts"] = ""
    suppressed = synth((make_dissent(unresolved=True),), silenced)
    print(
        f"  model tried to drop the conflict -> retained anyway: "
        f"{len(suppressed.retained_conflicts)}"
    )

    try:
        build_strategy_thesis(
            {**contested.model_dump(), "retained_conflicts": ()},
        )
        outcome = "ERROR: a contested thesis dropped its conflicts"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "A contested thesis cannot drop the conflicts that contest it"
    print(f"  {outcome}")


def main() -> None:
    """Run every functional-requirement demonstration for the thesis analyst."""
    fr_agentic_037()
    fr_agentic_038()
    fr_agentic_039()


if __name__ == "__main__":
    main()
