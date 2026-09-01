"""Executable FEAT-AGT-11 Technical Analyst usage example.

Demonstrates the registered public operation through the documented API. Every
receiver operation arrives as an injected port bound to deterministic doubles:
no broker, provider, or network call occurs, and Agentic holds no credential.

The point of the demonstration is the division of authority — bindings come
from deterministic tools, claims come from the model — and the governed tool
path that authorizes before invoking.
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
from app.agentic.agents.market_analysis.technical_analyst import (
    analyze_technical_context,
    build_technical_evidence_pack,
)
from app.agentic.agents.market_analysis.technical_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    build_technical_mandate,
    build_technical_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-technical-usage")
INSTRUMENT = "EURUSD"
TIMEFRAME = "H1"
INDICATORS = ("ema", "atr")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

MODEL_OUTPUT = {
    "claim:trend": "Price printed three consecutive higher lows on H1.",
    "confirmation:trend": "A close above the prior swing high confirms it.",
    "invalidation:trend": "A close below the 200-period EMA invalidates it.",
    "leakage:trend": "Evaluate using only bars closed before the decision time.",
    "claim:volatility": "Realized range widened across the London session.",
    "confirmation:volatility": "ATR above its 20-period median confirms it.",
    "invalidation:volatility": "ATR falling below that median invalidates it.",
    "leakage:volatility": "Compare only to ATR values available at decision time.",
    "uncertainty": "One session of observations under passing data quality.",
    "conflicts": "Momentum and mean-reversion readings disagree on continuation.",
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicPort:
    """Deterministic receiver-domain evidence port."""

    def __init__(self, quality_status="passed", indicator_versions=None):
        self.quality_status = quality_status
        self.indicator_versions = indicator_versions or {"ema": "1.0.0", "atr": "1.0.0"}
        self.calls = []

    def fetch_market_evidence(self, instrument, timeframe):
        """Return canonical market evidence."""
        self.calls.append("market")
        return {
            "dataset_ref": f"data.market_dataset:{instrument}-{timeframe}",
            "venue": "mt5-demo",
            "window_start": "2026-07-29T08:00:00Z",
            "window_end": "2026-07-29T12:00:00Z",
            "bars": "240",
        }

    def fetch_quality_evidence(self, instrument):
        """Return canonical data-quality evidence."""
        self.calls.append("quality")
        return {
            "report_ref": f"data.quality_report:{instrument}",
            "status": self.quality_status,
            "gaps": "0",
        }

    def fetch_session_evidence(self, instrument):
        """Return canonical session evidence."""
        del instrument
        self.calls.append("session")
        return {"session": "london", "tradable": "true"}

    def fetch_indicator_versions(self, indicators):
        """Return registered indicator versions."""
        self.calls.append("indicators")
        return {k: v for k, v in self.indicator_versions.items() if k in indicators}


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
                "tokens_used": 620,
                "latency_ms": 45,
                "cost": Decimal("0.03"),
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
    """Build the bounded governed technical task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "analyze_technical_context",
            "workflow_version": "1.0.0",
            "objective": "Describe EURUSD H1 structure for the London session.",
            "input_refs": ("data.market_dataset:EURUSD-H1",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=15),
            "idempotency_key": "idem-technical-usage",
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-11",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("technical_analyst",),
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
    """Build the technical-analyst agent policy."""
    data = {
        "role_id": "technical_analyst",
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
    """Run one technical analysis with the deterministic doubles."""
    data = {
        "registry": get_role_registry(
            build_technical_mandate(),
            (build_technical_role_manifest(),),
            NOW,
        ),
        "task": make_task(),
        "mandate": build_technical_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "port": DeterministicPort(),
        "runtime": DeterministicRuntime(output=dict(MODEL_OUTPUT)),
        "profile": make_profile(),
        "instrument": INSTRUMENT,
        "timeframe": TIMEFRAME,
        "indicators": INDICATORS,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return analyze_technical_context(**data)


def fr_agentic_031() -> None:
    """FR-AGENTIC-031: Canonical output, never an alternate definition."""
    _header(
        "FR-AGENTIC-031: Technical analysis consumes canonical Data and "
        "Indicators outputs and does not silently compute an alternate "
        "indicator definition."
    )

    port = DeterministicPort()
    audit = build_in_memory_memory_store()
    result = run(port=port, audit_store=audit)
    payload = result.payload

    print(f"  governed tool calls: {port.calls}")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )
    print(f"  indicator versions:  {dict(payload.indicator_versions)}")
    print("  Versions came from the Indicators receiver, not from the model.")

    poisoned = dict(MODEL_OUTPUT)
    poisoned["indicator_versions"] = "ema=9.9.9"
    forged = run(runtime=DeterministicRuntime(output=poisoned)).payload
    print(f"  model-supplied version ignored: {dict(forged.indicator_versions)}")

    denied_port = DeterministicPort()
    denied = run(port=denied_port, tool_policies=make_tool_policies(enabled=False))
    print(f"  disabled tool -> {denied.status} ({denied.reasons[0]})")
    print(f"  receiver reached: {len(denied_port.calls)} times")


def fr_agentic_032() -> None:
    """FR-AGENTIC-032: The reading is bound to an exact context."""
    _header(
        "FR-AGENTIC-032: Technical outputs bind instrument, venue, timeframe, "
        "session, observation window, indicator versions, and data-quality "
        "evidence."
    )

    runtime = DeterministicRuntime(output=dict(MODEL_OUTPUT))
    payload = run(runtime=runtime).payload
    print(f"  instrument:   {payload.instrument}")
    print(f"  venue:        {payload.venue}")
    print(f"  timeframe:    {payload.timeframe}")
    print(f"  session:      {payload.session}")
    print(
        f"  window:       {payload.observation_start.isoformat()} -> "
        f"{payload.observation_end.isoformat()}"
    )
    print(f"  quality:      {payload.data_quality_status} ({payload.data_quality_ref})")
    print(f"  market ref:   {payload.market_evidence_ref}")

    invocation = runtime.invocations[0]
    print(f"  trusted context keys:   {sorted(invocation.trusted_context)[:4]}...")
    print(f"  untrusted evidence keys:{sorted(invocation.untrusted_evidence)[:3]}...")
    print("  Bindings are trusted context; raw evidence stays untrusted.")

    failed = run(port=DeterministicPort(quality_status="failed"))
    print(f"  failed quality -> {failed.status} ({failed.reasons[0]})")


def fr_agentic_033() -> None:
    """FR-AGENTIC-033: Every claim states confirmation and invalidation."""
    _header(
        "FR-AGENTIC-033: Pattern or regime claims state confirmation, "
        "invalidation, and leakage-safe evaluation requirements."
    )

    payload = run().payload
    for claim_id, statement in payload.claims.items():
        print(f"  [{claim_id}]")
        print(f"    claim:        {statement}")
        print(f"    confirmation: {payload.confirmations[claim_id]}")
        print(f"    invalidation: {payload.invalidations[claim_id]}")
        print(f"    leakage-safe: {payload.leakage_notes[claim_id]}")
    print(f"  preserved conflicts: {payload.conflicts}")

    for label, dropped in (
        ("no confirmation", "confirmations"),
        ("no invalidation", "invalidations"),
        ("no leakage note", "leakage_notes"),
    ):
        try:
            build_technical_evidence_pack({**payload.model_dump(), dropped: {}})
            outcome = f"ERROR: a claim with {label} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"A claim with {label} is unrepresentable"
        print(f"  {outcome}")

    try:
        build_technical_evidence_pack(
            {**payload.model_dump(), "uncertainty": "Use a position size of two lots."},
        )
        outcome = "ERROR: execution language was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Execution language correctly rejected"
    print(f"  {outcome}")


def main() -> None:
    """Run every functional-requirement demonstration for the analyst."""
    fr_agentic_031()
    fr_agentic_032()
    fr_agentic_033()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-11", main)
