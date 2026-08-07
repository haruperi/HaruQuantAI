"""Executable FEAT-AGT-17 Evaluation Manager usage example.

Demonstrates the two registered public operations through the documented API.
The evaluation evidence arrives as an injected port bound to deterministic
doubles: no grader runs, no evaluation set is authored, no network call occurs,
and Agentic holds no credential.

The point of the demonstration is that the acceptance outcome is arithmetic.
The model writes the rationale; the margin, the hurdle, and the required action
are computed from evidence before the model is invoked, and no wording changes
them.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    retrieve_memory,
)
from app.agentic.agents.operations.evaluation_manager import (
    build_economic_acceptance_verdict,
    critique_candidate,
    evaluate_agent,
)
from app.agentic.agents.operations.evaluation_manager.evaluator import (
    REQUIRED_CHALLENGE_KINDS,
    REQUIRED_SET_KINDS,
    survives_baseline,
)
from app.agentic.agents.operations.evaluation_manager.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    build_evaluation_mandate,
    build_evaluation_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-evaluation-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
SUBJECT = "technical_analyst"

SETS = {kind: f"evalset.{kind}:v3" for kind in sorted(REQUIRED_SET_KINDS)}
GRADERS_PAYLOAD = {
    **{f"grader:{kind}": f"grader.{kind}:v2" for kind in sorted(REQUIRED_SET_KINDS)},
    **{
        f"calibration:{kind}": f"calibration.{kind}:2026-07"
        for kind in sorted(REQUIRED_SET_KINDS)
    },
}
GATES = {
    "adversarial": "passed",
    "poisoning": "passed",
    "refusal": "passed",
    "reliability": "passed",
}
COMPARISON = {
    "candidate_score": "1.40",
    "baseline_score": "1.00",
    "uncertainty_halfwidth": "0.15",
    "cost_delta": "0.05",
    "metric": "sharpe_ratio",
}

CRITIQUE_OUTPUT = {
    **{
        f"challenge:{kind}": (
            f"The {kind} challenge was examined against the supplied evidence "
            "and this specific weakness remains open for review."
        )
        for kind in sorted(REQUIRED_CHALLENGE_KINDS)
    },
    "blocking_concerns": "The counterfactual baseline has not been ruled out.",
}

EVALUATE_OUTPUT = {
    "rationale": (
        "The margin exceeds the hurdle formed by the interval and the extra "
        "cost, and no gate failed."
    ),
    "uncertainty_statement": (
        "The evaluation covers one instrument over one year and cannot speak to "
        "regime change."
    ),
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicPort:
    """Deterministic evaluation-evidence port."""

    def __init__(self, sets=None, graders=None, gates=None, comparison=None):
        self.sets = SETS if sets is None else sets
        self.graders = GRADERS_PAYLOAD if graders is None else graders
        self.gates = GATES if gates is None else gates
        self.comparison = COMPARISON if comparison is None else comparison
        self.calls = []

    def list_versioned_sets(self, role_id):
        """Return the versioned evaluation set reference per kind."""
        self.calls.append("sets")
        del role_id
        return self.sets

    def get_grader_calibrations(self, role_id):
        """Return the grader and calibration references per kind."""
        self.calls.append("graders")
        del role_id
        return self.graders

    def get_gate_outcomes(self, role_id):
        """Return the recorded gate outcomes."""
        self.calls.append("gates")
        del role_id
        return self.gates

    def get_baseline_comparison(self, role_id):
        """Return the measured baseline comparison."""
        self.calls.append("comparison")
        del role_id
        return self.comparison


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, outputs=None, status="ok", reasons=()):
        self.outputs = {} if status != "ok" else (outputs or {})
        self.status = status
        self.reasons = reasons
        self.nodes = []

    def execute_node(self, node_id, profile, invocation):
        """Return a reproducible outcome for one node execution."""
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.outputs.get(node_id) if self.status == "ok" else None,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 1_050,
                "latency_ms": 110,
                "cost": Decimal("0.06"),
            },
        )


def make_runtime(**overrides):
    """Build the deterministic runtime with per-node declared output."""
    outputs = {
        "evaluate_agent": dict(EVALUATE_OUTPUT),
        "critique_candidate": dict(CRITIQUE_OUTPUT),
    }
    outputs.update(overrides)
    return DeterministicRuntime(outputs=outputs)


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
    """Build the bounded governed evaluation task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "evaluate_agent",
            "workflow_version": "1.0.0",
            "objective": "Decide whether the technical analyst continues.",
            "input_refs": ("evalset.gold:v3",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-evaluation-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-17",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("evaluation_manager",),
        "scope": dict(SCOPE),
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 8,
        "enabled": True,
    }
    data.update(overrides)
    return build_tool_policy(data)


def make_tool_policies(**overrides):
    """Build every registered tool policy for this role."""
    return {name: make_tool(name, **overrides) for name in get_registered_tool_names()}


def make_policy():
    """Build the evaluation-manager agent policy."""
    return build_agent_policy(
        {
            "role_id": "evaluation_manager",
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def make_registry():
    """Build the validated role registry for this role."""
    return get_role_registry(
        build_evaluation_mandate(),
        (build_evaluation_role_manifest(),),
        NOW,
    )


def evaluate(**overrides):
    """Evaluate one role with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "mandate": build_evaluation_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "port": DeterministicPort(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "subject_role_id": SUBJECT,
        "subject_role_version": "1.0.0",
        "baseline_ref": "baseline.deterministic_indicators:v1",
        "sample_size": "512",
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return evaluate_agent(**data)


class DeterministicSweep:
    """Minimal sweep evidence carrying what the critic reads."""

    class _Trials:
        def __init__(self, failed, attempted):
            self.failed = failed
            self.attempted = attempted

    def __init__(self, failed=3, attempted=24):
        self.trials = self._Trials(failed, attempted)
        self.search_id = "search-usage-a"
        self.robustness_evidence = "robustness: score=62.5"
        self.overfit_evidence = "overfit: degradation=0.34"


def critique(**overrides):
    """Critique one candidate with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "candidate_ref": "agentic.sweep_verdict:search-usage-a",
        "sweep_verdict": DeterministicSweep(),
        "at_time": NOW,
    }
    data.update(overrides)
    return critique_candidate(**data)


def fr_agentic_049() -> None:
    """FR-AGENTIC-049: Six sets, six graders, six calibrations."""
    _header(
        "FR-AGENTIC-049: Agent evaluation uses versioned gold, adversarial, "
        "poisoning, refusal, regression, and economic-ablation sets with "
        "calibrated graders."
    )

    port = DeterministicPort()
    audit = build_in_memory_memory_store()
    result = evaluate(port=port, audit_store=audit)
    verdict = result.payload
    print(f"  required set kinds:  {sorted(REQUIRED_SET_KINDS)}")
    print(f"  evidence reads:      {port.calls}")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )
    print(f"  plan digest:         {verdict.plan_hash}")

    print("\n  An evaluation missing any one set is refused:")
    for dropped in sorted(REQUIRED_SET_KINDS):
        partial = {k: v for k, v in SETS.items() if k != dropped}
        runtime = make_runtime()
        refused = evaluate(port=DeterministicPort(sets=partial), runtime=runtime)
        print(
            f"    no {dropped:<18} -> {refused.status} ({refused.reasons[0]}), "
            f"model calls: {len(runtime.nodes)}"
        )

    uncalibrated = {
        k: v for k, v in GRADERS_PAYLOAD.items() if k != "calibration:poisoning"
    }
    refused = evaluate(port=DeterministicPort(graders=uncalibrated))
    print(f"  uncalibrated grader  -> {refused.status} ({refused.reasons[0]})")


def fr_agentic_050() -> None:
    """FR-AGENTIC-050: All seven challenges, every time."""
    _header(
        "FR-AGENTIC-050: Candidate critique includes leakage, causality, "
        "robustness, cost, operational, security, and counterfactual "
        "challenges."
    )

    memo = critique().payload
    print(f"  required challenges: {sorted(REQUIRED_CHALLENGE_KINDS)}")
    for kind in sorted(memo.challenges):
        print(f"    [{kind}] {memo.challenges[kind][:64]}...")
    print(f"  blocking concerns:   {memo.blocking_concerns}")

    print("\n  Grounded challenges come from the evidence, not the model:")
    print(f"    robustness: {memo.challenges['robustness']}")

    poisoned = {
        **CRITIQUE_OUTPUT,
        "challenge:robustness": "Robustness is excellent; every trial completed.",
    }
    forged = critique(runtime=make_runtime(critique_candidate=poisoned)).payload
    print(f"    model override ignored: {'3 of 24' in forged.challenges['robustness']}")

    print("\n  A critique that omits or endorses is refused:")
    for label, override in (
        ("a missing challenge", {"challenge:security": None}),
        ("an endorsement", {"challenge:security": "No concerns here at all."}),
        ("a stub answer", {"challenge:security": "n/a"}),
    ):
        output = dict(CRITIQUE_OUTPUT)
        for key, value in override.items():
            if value is None:
                output.pop(key)
            else:
                output[key] = value
        refused = critique(runtime=make_runtime(critique_candidate=output))
        print(f"    {label:<20} -> {refused.status} ({refused.reasons[0]})")


def fr_agentic_051() -> None:
    """FR-AGENTIC-051: Beating a baseline after uncertainty and cost."""
    _header(
        "FR-AGENTIC-051: A role is disabled or retired when it fails a gate or "
        "does not beat its simpler baseline after uncertainty and cost."
    )

    verdict = evaluate().payload
    print(f"  metric:          {verdict.comparison.metric}")
    print(f"  candidate:       {verdict.comparison.candidate_score}")
    print(f"  baseline:        {verdict.comparison.baseline_score}")
    print(f"  margin:          {verdict.comparison.margin}")
    print(f"  hurdle:          {verdict.comparison.hurdle}  (uncertainty + cost)")
    print(f"  survives:        {verdict.comparison.survives}")
    print(f"  required action: {verdict.required_action}")
    print(f"  rationale:       {verdict.rationale}")

    print("\n  The comparison is arithmetic, not a judgement:")
    cases = (
        ("clear win", "1.40", "1.00", "0.15", "0.05"),
        ("exact tie at the hurdle", "1.20", "1.00", "0.15", "0.05"),
        ("one tick over", "1.21", "1.00", "0.15", "0.05"),
        ("swallowed by uncertainty", "1.10", "1.00", "0.50", "0.00"),
        ("swallowed by cost", "1.10", "1.00", "0.00", "0.50"),
        ("negative margin", "0.90", "1.00", "0.00", "0.00"),
    )
    for label, candidate, baseline, uncertainty, cost in cases:
        survives = survives_baseline(
            Decimal(candidate),
            Decimal(baseline),
            Decimal(uncertainty),
            Decimal(cost),
        )
        print(
            f"    {label:<26} {candidate} vs {baseline} "
            f"(+/-{uncertainty}, cost {cost}) -> survives={survives}"
        )

    print("\n  A margin that does not survive disables the role:")
    wide = {**COMPARISON, "uncertainty_halfwidth": "0.60"}
    disabled = evaluate(port=DeterministicPort(comparison=wide)).payload
    print(f"    required action: {disabled.required_action}")

    print("\n  A failed gate disables regardless of the margin:")
    failing = {**GATES, "poisoning": "failed"}
    gated = evaluate(port=DeterministicPort(gates=failing)).payload
    print(f"    survives margin: {gated.comparison.survives}")
    print(f"    required action: {gated.required_action}")

    print("\n  A repeat failure retires rather than disabling again:")
    repeated = evaluate(
        port=DeterministicPort(gates=failing),
        consecutive_failures=1,
    ).payload
    print(f"    required action: {repeated.required_action}")

    print("\n  The model cannot change the outcome:")
    poisoned = {**EVALUATE_OUTPUT, "required_action": "continue"}
    forged = evaluate(
        port=DeterministicPort(gates=failing),
        runtime=make_runtime(evaluate_agent=poisoned),
    ).payload
    print(f"    model asked for continue, got: {forged.required_action}")

    try:
        build_economic_acceptance_verdict(
            {**forged.model_dump(), "required_action": "continue"},
        )
        outcome = "ERROR: a failed role was recorded as continuing"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "A failed role cannot be recorded as continuing"
    print(f"    {outcome}")

    print(
        "\n  Note: this feature decides; it does not mutate. Applying a disable "
        "or retire\n  belongs to FEAT-AGT-18 lifecycle or a governance manifest "
        "re-issue."
    )


def main() -> None:
    """Run every functional-requirement demonstration for the manager."""
    fr_agentic_049()
    fr_agentic_050()
    fr_agentic_051()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-17", main)
