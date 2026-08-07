"""Executable FEAT-AGT-12 Quantitative Analyst usage example.

Demonstrates the registered public operation through the documented API. The
Analytics metric catalog arrives as an injected port bound to deterministic
doubles: no network call occurs, and Agentic holds no credential.

The point of the demonstration is where authority sits — estimators and sample
floors come from the catalog, disclosure comes from the caller, and evidence
that cannot be analysed is refused before the model is ever reached.
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
from app.agentic.agents.market_analysis.quantitative_analyst import (
    analyze_quantitative_evidence,
    build_quantitative_evidence_pack,
)
from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    build_quantitative_mandate,
    build_quantitative_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-quantitative-usage")
METRICS = ("sharpe_ratio", "max_drawdown")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

DATASET_HASH = "sha256:dataset-a"
CONFIG_HASH = "sha256:config-a"

EVIDENCE = {
    "research.edge_lab_profile:v1": {
        "dataset_hash": DATASET_HASH,
        "configuration_hash": CONFIG_HASH,
        "split": "holdout",
        "trials": "40",
    },
    "analytics.performance_report:v1": {
        "dataset_hash": DATASET_HASH,
        "configuration_hash": CONFIG_HASH,
        "split": "holdout",
        "observations": "512",
    },
}

STATISTICS = {"sharpe_ratio": 0.42, "max_drawdown": -0.18}

CATALOG = {
    "sharpe_ratio": {
        "formula": "mean(excess_returns) / stdev(excess_returns)",
        "unit": "ratio",
        "sample_convention": "per_bar",
        "minimum_sample": "30",
    },
    "max_drawdown": {
        "formula": "min(equity / cummax(equity) - 1)",
        "unit": "fraction",
        "sample_convention": "per_bar",
        "minimum_sample": "30",
    },
}

FLOORS = {"variance": "2", "tail": "30", "statistical": "30"}

MODEL_OUTPUT = {
    "finding:risk_adjusted_return": (
        "Risk-adjusted return is positive but small on the holdout split."
    ),
    "estimator:risk_adjusted_return": "sharpe_ratio",
    "uncertainty:risk_adjusted_return": (
        "The bootstrap interval spans zero at the 95 percent level."
    ),
    "finding:drawdown": "The worst peak-to-trough decline occurred in one regime.",
    "estimator:drawdown": "max_drawdown",
    "uncertainty:drawdown": "A single episode drives the statistic; it is unstable.",
    "assumptions": (
        "Returns are treated as independent across bars.\n"
        "The holdout split is assumed stationary over the window."
    ),
    "limitations": (
        "This evidence cannot establish out-of-sample profitability.\n"
        "No transaction-cost model was applied."
    ),
    "conflicts": "The two findings disagree on whether the edge is regime-specific.",
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicPort:
    """Deterministic Analytics catalog port."""

    def __init__(self, catalog=None, floors=None):
        self.catalog = CATALOG if catalog is None else catalog
        self.floors = FLOORS if floors is None else floors
        self.calls = []

    def fetch_metric_definition(self, metric):
        """Return one registered metric definition."""
        self.calls.append(f"definition:{metric}")
        return self.catalog.get(metric, {})

    def fetch_minimum_samples(self):
        """Return registered minimum-sample thresholds."""
        self.calls.append("floors")
        return self.floors

    def validate_evidence_contract(self, contract, version):
        """Validate one evidence contract version."""
        self.calls.append(f"contract:{contract}")
        return {"contract": contract, "version": version, "status": "compatible"}


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
    """Build the bounded governed quantitative task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "analyze_quantitative_evidence",
            "workflow_version": "1.0.0",
            "objective": "State what the holdout statistics do and do not support.",
            "input_refs": tuple(sorted(EVIDENCE)),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=15),
            "idempotency_key": "idem-quantitative-usage",
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-12",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("quantitative_analyst",),
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
    """Build the quantitative-analyst agent policy."""
    data = {
        "role_id": "quantitative_analyst",
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


def run(**overrides):
    """Run one quantitative analysis with the deterministic doubles."""
    data = {
        "registry": get_role_registry(
            build_quantitative_mandate(),
            (build_quantitative_role_manifest(),),
            NOW,
        ),
        "task": make_task(),
        "mandate": build_quantitative_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "port": DeterministicPort(),
        "runtime": DeterministicRuntime(output=dict(MODEL_OUTPUT)),
        "profile": make_profile(),
        "evidence": {ref: dict(body) for ref, body in EVIDENCE.items()},
        "metrics": METRICS,
        "statistics": dict(STATISTICS),
        "sample_size": 512,
        "multiple_testing_exposure": 40,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return analyze_quantitative_evidence(**data)


def fr_agentic_034() -> None:
    """FR-AGENTIC-034: The catalog defines estimators, not the model."""
    _header(
        "FR-AGENTIC-034: Quantitative work uses registered metric definitions, "
        "formulas, and sample conventions from the Analytics catalog."
    )

    port = DeterministicPort()
    audit = build_in_memory_memory_store()
    result = run(port=port, audit_store=audit)
    payload = result.payload

    print(f"  governed tool calls: {port.calls}")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )
    for finding_id, estimator in payload.estimators.items():
        print(f"  [{finding_id}] estimator: {estimator}")
    print("  Formulas came from the catalog; the model only named the metric.")

    poisoned = dict(MODEL_OUTPUT)
    poisoned["estimator:risk_adjusted_return"] = "mean(returns)"
    forged = run(runtime=DeterministicRuntime(output=poisoned))
    print(f"  model-authored formula -> {forged.status} ({forged.reasons[0]})")

    unknown = run(metrics=("sharpe_ratio", "invented_alpha"))
    print(f"  uncatalogued metric    -> {unknown.status} ({unknown.reasons[0]})")

    denied_port = DeterministicPort()
    denied = run(port=denied_port, tool_policies=make_tool_policies(enabled=False))
    print(f"  disabled tool          -> {denied.status} ({denied.reasons[0]})")
    print(f"  receiver reached: {len(denied_port.calls)} times")


def fr_agentic_035() -> None:
    """FR-AGENTIC-035: Statistical disclosure is structural."""
    _header(
        "FR-AGENTIC-035: Every quantitative claim discloses sample, estimator, "
        "uncertainty, multiple-testing exposure, assumptions, and limitations."
    )

    payload = run().payload
    print(f"  sample size:               {payload.sample_size}")
    print(f"  multiple-testing exposure: {payload.multiple_testing_exposure}")
    print(
        f"  dataset / configuration:   {payload.dataset_hash} / "
        f"{payload.configuration_hash}"
    )
    print(f"  split:                     {payload.split_label}")
    print(f"  validation:                {payload.validation_status}")
    for finding_id, statement in payload.findings.items():
        print(f"  [{finding_id}]")
        print(f"    finding:     {statement}")
        print(f"    estimator:   {payload.estimators[finding_id]}")
        print(f"    uncertainty: {payload.uncertainty[finding_id]}")
    print(f"  assumptions: {payload.assumptions}")
    print(f"  limitations: {payload.limitations}")
    print(f"  preserved conflicts: {payload.conflicts}")

    poisoned = dict(MODEL_OUTPUT)
    poisoned["sample_size"] = "1000000"
    forged = run(runtime=DeterministicRuntime(output=poisoned)).payload
    print(f"  model-supplied sample ignored: {forged.sample_size}")

    for label, dropped in (
        ("no estimator", "estimators"),
        ("no uncertainty", "uncertainty"),
    ):
        try:
            build_quantitative_evidence_pack({**payload.model_dump(), dropped: {}})
            outcome = f"ERROR: a finding with {label} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"A finding with {label} is unrepresentable"
        print(f"  {outcome}")

    try:
        build_quantitative_evidence_pack(
            {
                **payload.model_dump(),
                "limitations": ("Use a position size of two lots.",),
            },
        )
        outcome = "ERROR: execution language was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Execution language correctly rejected"
    print(f"  {outcome}")


def fr_agentic_036() -> None:
    """FR-AGENTIC-036: Refuse rather than repair."""
    _header(
        "FR-AGENTIC-036: Non-finite, under-sampled, non-aligned, or "
        "leakage-unsafe evidence is refused, never imputed or reconciled."
    )

    numeric_fields = [
        name
        for name, field in payload_fields().items()
        if any(kind in str(field.annotation) for kind in ("int", "float", "Decimal"))
    ]
    print(f"  numeric fields in the output schema: {numeric_fields}")
    print("  There is nowhere in the schema to place an imputed statistic.")

    cases = {
        "non-finite statistic": {
            "statistics": {**STATISTICS, "sharpe_ratio": float("nan")},
        },
        "sample below catalog floor": {"sample_size": 12},
        "leakage-unsafe evidence": {"leakage_severity": "high"},
        "absent evidence": {"evidence": {}},
    }
    misaligned = {ref: dict(body) for ref, body in EVIDENCE.items()}
    misaligned["analytics.performance_report:v1"]["dataset_hash"] = "sha256:other"
    cases["non-aligned evidence"] = {"evidence": misaligned}

    for label, overrides in cases.items():
        runtime = DeterministicRuntime(output=dict(MODEL_OUTPUT))
        result = run(runtime=runtime, **overrides)
        print(
            f"  {label:<28} -> {result.status} ({result.reasons[0]}), "
            f"model calls: {len(runtime.invocations)}"
        )

    strict = DeterministicPort(floors={**FLOORS, "statistical": "5000"})
    result = run(port=strict)
    print(f"  the floor is the catalog's, not a constant: {result.reasons[0]}")


def payload_fields():
    """Return the declared fields of the quantitative output schema."""
    from app.agentic.agents.market_analysis.quantitative_analyst import (
        QuantitativeEvidencePack,
    )

    return QuantitativeEvidencePack.model_fields


def main() -> None:
    """Run every functional-requirement demonstration for the analyst."""
    fr_agentic_034()
    fr_agentic_035()
    fr_agentic_036()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-12", main)
