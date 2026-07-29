"""Executable FEAT-AGT-14 Experiment Designer usage example.

Demonstrates the two registered public operations through the documented API.
The Simulation receiver arrives as an injected port bound to deterministic
doubles: no backtest executes, no network call occurs, and Agentic holds no
credential.

The point of the demonstration is where authority sits — the protocol is
pre-registered and hashed before any run, the receiver owns its request and its
result, and every conclusion is keyed by the run identifier that was actually
returned.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    retrieve_memory,
)
from app.agentic.agents.experimentation.experiment_designer import (
    build_experiment_spec,
    coordinate_simulation,
    design_experiment,
)
from app.agentic.agents.experimentation.experiment_designer.migrations import (
    get_experiment_migration_statements,
)
from app.agentic.agents.experimentation.experiment_designer.repository import (
    build_in_memory_experiment_store,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    SplitWindow,
    derive_spec_hash,
)
from app.agentic.agents.experimentation.experiment_designer.tools import (
    get_registered_tool_names,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst import (
    build_hypothesis,
    build_strategy_thesis,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agentic.fixtures import (
    build_designer_mandate,
    build_designer_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-experiment-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

BASELINE = "analytics.baseline:buy_and_hold_v1"
COST_MODEL = "simulator.execution_profile:retail_fx_v1"
INPUT_REFS = ("data.market_dataset:EURUSD-H1@v3",)
METRICS = ("sharpe_ratio", "max_drawdown")
EMBARGO = 7 * 24 * 3600
SEED = 20260729

SPLITS = (
    SplitWindow.model_validate(
        {
            "label": "discovery",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "end": datetime(2023, 1, 1, tzinfo=UTC),
        },
    ),
    SplitWindow.model_validate(
        {
            "label": "validation",
            "start": datetime(2023, 2, 1, tzinfo=UTC),
            "end": datetime(2024, 1, 1, tzinfo=UTC),
        },
    ),
    SplitWindow.model_validate(
        {
            "label": "holdout",
            "start": datetime(2024, 3, 1, tzinfo=UTC),
            "end": datetime(2025, 1, 1, tzinfo=UTC),
        },
    ),
)

REQUEST = {
    "schema_id": "simulation.backtest_request.v1",
    "config_hash": "sha256:config-a",
    "data_hash": "sha256:data-a",
    "seed": str(SEED),
}

RESULT = {
    "schema_id": "simulation.result.v1",
    "status": "completed",
    "run_id": "run-usage-a",
    "request_hash": "sha256:request-a",
    "config_hash": "sha256:config-a",
    "engine_version": "simulator-4.2.0",
    "journal_ref": "simulator.journal:run-usage-a",
    "artifact_manifest_ref": "simulator.artifacts:run-usage-a",
}

DESIGN_OUTPUT = {
    "falsification_outcome": (
        "The holdout Sharpe is at or below the baseline's over the same window."
    ),
    "stop_rules": (
        "Stop if the discovery split yields no effect above the baseline.\n"
        "Stop if data quality is warned on more than one session."
    ),
    "leakage_controls": (
        "Indicator warm-up is contained inside each split.\n"
        "Positions are closed before the embargo begins."
    ),
}

VERDICT_OUTPUT = {
    "outcome": "not_refuted",
    "conclusion": (
        "The declared refuting outcome did not occur on the evaluated split."
    ),
    "limitations": "One split cannot establish stability across regimes.",
    "conflicts": "Discovery and validation readings disagree on persistence.",
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicPort:
    """Deterministic Simulation port."""

    def __init__(self, result=None):
        self.result = RESULT if result is None else result
        self.calls = []
        self.requests = []

    def submit_backtest(self, request):
        """Execute one receiver-owned backtest request."""
        self.calls.append("backtest")
        self.requests.append(dict(request))
        return self.result

    def resolve_run(self, run_id):
        """Resolve one previously executed run."""
        self.calls.append(f"resolve:{run_id}")
        return self.result


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, outputs=None, status="ok", reasons=()):
        self.outputs = outputs or {}
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
                "output": self.outputs.get(node_id),
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 780,
                "latency_ms": 65,
                "cost": Decimal("0.04"),
            },
        )


def make_runtime(**overrides):
    """Build the deterministic runtime with per-node declared output."""
    outputs = {
        "design_experiment": dict(DESIGN_OUTPUT),
        "coordinate_simulation": dict(VERDICT_OUTPUT),
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
    """Build the bounded governed experiment task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "design_experiment",
            "workflow_version": "1.0.0",
            "objective": "Specify a protocol that could refute the thesis.",
            "input_refs": INPUT_REFS,
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": "idem-experiment-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def make_hypothesis(**overrides):
    """Build one falsifiable hypothesis under test."""
    data = {
        "hypothesis_id": derive_stable_id("id", "hyp-usage"),
        "task_id": TASK_ID,
        "statement": "London-session momentum persists into the overlap.",
        "asset_scope": ("EURUSD",),
        "horizon": "intraday",
        "mechanism": "Order flow from the London fix carries into the overlap.",
        "prerequisites": ("Liquid session overlap",),
        "confounders": ("Month-end rebalancing flows",),
        "rejection_criterion": (
            "Overlap moves show no positive relationship to London-session moves."
        ),
        "evidence_refs": INPUT_REFS,
    }
    data.update(overrides)
    return build_hypothesis(data)


def make_thesis():
    """Build the non-executable thesis this protocol tests."""
    return build_strategy_thesis(
        {
            "thesis_id": derive_stable_id("id", "thesis-usage"),
            "task_id": TASK_ID,
            "title": "Session-overlap momentum continuation",
            "summary": "Momentum formed in London may continue into the overlap.",
            "stance": "contested",
            "hypothesis_ids": (make_hypothesis().hypothesis_id,),
            "signals": {"momentum": "Sign and magnitude of the London-session move."},
            "intended_behaviour": {
                "momentum": "Participate while the overlap trend persists.",
            },
            "supporting_evidence": INPUT_REFS,
            "retained_conflicts": ("Mean-reversion evidence disagrees.",),
            "assumptions": ("Session boundaries are stable.",),
            "uncertainty": "One venue, one instrument, one year of observations.",
            "next_test": "Evaluate the overlap relationship on a held-out year of data.",
        },
    )


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-14",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("experiment_designer",),
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


def make_policy(**overrides):
    """Build the experiment-designer agent policy."""
    data = {
        "role_id": "experiment_designer",
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence",),
        "allowed_tools": get_registered_tool_names(),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    data.update(overrides)
    return build_agent_policy(data)


def make_registry():
    """Build the validated role registry for this role."""
    return get_role_registry(
        build_designer_mandate(),
        (build_designer_role_manifest(),),
        NOW,
    )


def design(**overrides):
    """Design one protocol with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "thesis": make_thesis(),
        "hypotheses": (make_hypothesis(),),
        "input_refs": INPUT_REFS,
        "splits": SPLITS,
        "embargo_seconds": EMBARGO,
        "baseline_ref": BASELINE,
        "cost_model_ref": COST_MODEL,
        "metrics": METRICS,
        "seed": SEED,
        "at_time": NOW,
    }
    data.update(overrides)
    return design_experiment(**data)


def coordinate(**overrides):
    """Coordinate one run with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "mandate": build_designer_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "port": DeterministicPort(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "spec": design().payload,
        "request": dict(REQUEST),
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return coordinate_simulation(**data)


def fr_agentic_040() -> None:
    """FR-AGENTIC-040: A protocol is complete or it does not exist."""
    _header(
        "FR-AGENTIC-040: Experiment design specifies immutable inputs, time "
        "splits, embargo, costs, seeds, baselines, metrics, stop rules, and "
        "falsification outcomes."
    )

    spec = design().payload
    print(f"  protocol digest:  {spec.spec_hash}")
    print(f"  inputs:           {spec.input_refs}")
    print(f"  baseline:         {spec.baseline_ref}")
    print(f"  cost model:       {spec.cost_model_ref}")
    print(f"  seed:             {spec.seed}")
    print(f"  embargo:          {spec.embargo_seconds}s")
    for window in spec.splits:
        print(
            f"  split {window.label:<11} {window.start.date()} -> {window.end.date()}"
        )
    print(f"  falsification:    {spec.falsification_outcome}")
    print(f"  stop rules:       {spec.stop_rules}")
    print(f"  leakage controls: {spec.leakage_controls}")

    poisoned = dict(DESIGN_OUTPUT)
    poisoned["seed"] = "99"
    poisoned["baseline_ref"] = "analytics.baseline:whatever_i_like"
    forged = design(runtime=make_runtime(design_experiment=poisoned)).payload
    print(f"  model-supplied seed ignored:     {forged.seed}")
    print(f"  model-supplied baseline ignored: {forged.baseline_ref}")

    rewritten = {
        **spec.model_dump(),
        "falsification_outcome": "Anything short of spectacular refutes it.",
    }
    print(
        f"  rewriting the criterion changes the digest: "
        f"{derive_spec_hash(rewritten) != spec.spec_hash}"
    )

    for label, override in (
        ("overlapping splits", {"embargo_seconds": 90 * 24 * 3600}),
        ("a missing split", {"splits": SPLITS[:2]}),
        ("no baseline", {"baseline_ref": ""}),
        ("no inputs", {"input_refs": ()}),
    ):
        runtime = make_runtime()
        result = design(runtime=runtime, **override)
        print(
            f"  {label:<22} -> {result.status} ({result.reasons[0]}), "
            f"model calls: {len(runtime.nodes)}"
        )

    for field in ("stop_rules", "leakage_controls", "metrics"):
        try:
            build_experiment_spec({**spec.model_dump(), field: ()})
            outcome = f"ERROR: a protocol with no {field} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"A protocol with no {field} is unrepresentable"
        print(f"  {outcome}")


def fr_agentic_041() -> None:
    """FR-AGENTIC-041: The receiver owns its request and its result."""
    _header(
        "FR-AGENTIC-041: Simulation coordination uses only the public "
        "Simulation request and result contracts and never invents or alters "
        "a result."
    )

    port = DeterministicPort()
    audit = build_in_memory_memory_store()
    result = coordinate(port=port, audit_store=audit)
    print(f"  governed tool calls: {port.calls}")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )
    print(f"  request passed through unchanged: {port.requests[0] == dict(REQUEST)}")
    print(f"  verdict outcome:     {result.payload.outcome}")

    tampered = {**RESULT, "config_hash": "sha256:not-the-submitted-config"}
    runtime = make_runtime()
    refused = coordinate(port=DeterministicPort(result=tampered), runtime=runtime)
    print(f"  tampered result   -> {refused.status} ({refused.reasons[0]})")
    print(f"  verdict model calls: {len(runtime.nodes)}")
    print(f"  detail: {refused.detail}")

    incomplete = {k: v for k, v in RESULT.items() if k != "journal_ref"}
    missing = coordinate(port=DeterministicPort(result=incomplete))
    print(f"  missing lineage   -> {missing.status} ({missing.reasons[0]})")

    denied_port = DeterministicPort()
    denied = coordinate(
        port=denied_port,
        tool_policies=make_tool_policies(enabled=False),
    )
    print(f"  disabled tool     -> {denied.status} ({denied.reasons[0]})")
    print(f"  receiver reached: {len(denied_port.calls)} times")


def fr_agentic_042() -> None:
    """FR-AGENTIC-042: Every conclusion names its run."""
    _header(
        "FR-AGENTIC-042: Experiment verdicts bind every conclusion to run IDs "
        "and distinguish discovery, validation, holdout, and null-data "
        "evidence."
    )

    store = build_in_memory_experiment_store()
    spec = design(store=store).payload
    verdict = coordinate(spec=spec, store=store, evidence_class="validation").payload
    for run_id, conclusion in verdict.conclusions.items():
        print(f"  [{run_id}]")
        print(f"    evidence class: {verdict.evidence_classes[run_id]}")
        print(f"    conclusion:     {conclusion}")
    print(f"  bound protocol digest: {verdict.spec_hash}")
    print(f"  recorded lineage: {sorted(store.list_runs(spec.spec_hash)[0])}")

    poisoned = {**VERDICT_OUTPUT, "run_id": "run-that-never-executed"}
    forged = coordinate(
        spec=spec,
        store=store,
        runtime=make_runtime(coordinate_simulation=poisoned),
        port=DeterministicPort(result={**RESULT, "run_id": "run-usage-b"}),
    ).payload
    print(f"  model-supplied run id ignored: {sorted(forged.conclusions)}")

    print("\n  Holdout is consumed, not borrowed:")
    print(f"    holdout spent before: {store.holdout_spent(spec.spec_hash)}")
    first = coordinate(
        spec=spec,
        store=store,
        evidence_class="holdout",
        port=DeterministicPort(result={**RESULT, "run_id": "run-usage-holdout"}),
    )
    print(
        f"    first look  -> {first.status}, consumed: {first.payload.holdout_consumed}"
    )
    second_port = DeterministicPort()
    second = coordinate(
        spec=spec, store=store, evidence_class="holdout", port=second_port
    )
    print(f"    second look -> {second.status} ({second.reasons[0]})")
    print(f"    receiver reached: {len(second_port.calls)} times")

    print("\n  The ledger makes scarcity durable:")
    holdout_table = next(
        statement
        for statement in get_experiment_migration_statements()
        if "agentic_experiment_holdout_use" in statement
    )
    print(f"    {'spec_hash TEXT PRIMARY KEY' in holdout_table = }")


def main() -> None:
    """Run every functional-requirement demonstration for the designer."""
    fr_agentic_040()
    fr_agentic_041()
    fr_agentic_042()


if __name__ == "__main__":
    main()
