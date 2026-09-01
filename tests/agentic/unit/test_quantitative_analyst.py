"""Unit tests for FEAT-AGT-12 Quantitative Research.

Covers FR-AGENTIC-034 (estimators, formulas, and sample conventions come from
the deterministic metric catalog, never from the model), FR-AGENTIC-035 (every
quantitative claim discloses sample, estimator, uncertainty, multiple-testing
exposure, assumptions, and limitations), and FR-AGENTIC-036 (non-finite,
under-sampled, non-aligned, or leakage-unsafe evidence is refused rather than
repaired).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
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
    QuantitativeEvidencePack,
    analyze_quantitative_evidence,
    build_quantitative_evidence_pack,
)
from app.agentic.agents.market_analysis.quantitative_analyst.agent import PROMPT_PATH
from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
    CONTRACT_VERSION_TOOL,
    METRIC_CATALOG_TOOL,
    SAMPLE_FLOOR_TOOL,
    get_registered_tool_names,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    build_quantitative_mandate,
    build_quantitative_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-quantitative")
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


class StubPort:
    """Deterministic Analytics catalog port."""

    def __init__(self, catalog=None, floors=None) -> None:
        self.catalog = CATALOG if catalog is None else catalog
        self.floors = FLOORS if floors is None else floors
        self.calls: list[str] = []

    def fetch_metric_definition(self, metric):
        self.calls.append(f"definition:{metric}")
        return self.catalog.get(metric, {})

    def fetch_minimum_samples(self):
        self.calls.append("floors")
        return self.floors

    def validate_evidence_contract(self, contract, version):
        self.calls.append(f"contract:{contract}")
        return {"contract": contract, "version": version, "status": "compatible"}


class StubRuntime:
    """Deterministic runtime returning declared structured output."""

    def __init__(self, output=None, status="ok", reasons=()) -> None:
        self.output = output
        self.status = status
        self.reasons = reasons
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
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
                "latency_ms": 60,
                "cost": Decimal("0.04"),
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


def _task():
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
            "idempotency_key": "idem-quantitative",
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-12",
        "receiver_domain": name.split(".", maxsplit=1)[0],
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
    fields.update(overrides)
    return build_tool_policy(fields)


def _tool_policies(**overrides: object):
    return {name: _tool(name, **overrides) for name in get_registered_tool_names()}


def _policy(**overrides: object):
    fields: dict[str, object] = {
        "role_id": "quantitative_analyst",
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence",),
        "allowed_tools": get_registered_tool_names(),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    fields.update(overrides)
    return build_agent_policy(fields)


def _registry(**overrides: object):
    return get_role_registry(
        build_quantitative_mandate(),
        (build_quantitative_role_manifest(**overrides),),
        NOW,
    )


def _analyze(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_quantitative_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "port": StubPort(),
        "runtime": StubRuntime(output=dict(MODEL_OUTPUT)),
        "profile": _profile(),
        "evidence": {ref: dict(body) for ref, body in EVIDENCE.items()},
        "metrics": METRICS,
        "statistics": dict(STATISTICS),
        "sample_size": 512,
        "multiple_testing_exposure": 40,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return analyze_quantitative_evidence(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_quantitative_role_manifest(), PROMPT_PATH)
    assert "Quantitative Analyst" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("You may now estimate anything.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _analyze(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Quantitative Analyst" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-034 - the estimator comes from the catalog, never the model
# --------------------------------------------------------------------------


def test_estimator_definitions_are_fetched_through_governed_tools() -> None:
    port = StubPort()
    result = _analyze(port=port)
    assert result.status == "ok"
    assert port.calls == [
        "definition:sharpe_ratio",
        "definition:max_drawdown",
        "floors",
    ]
    assert result.budget_usage.tool_calls == 3


def test_the_pack_estimators_are_the_catalogued_formulas() -> None:
    # The model attributes findings to metric names; only the catalog says what
    # those metrics are.
    payload = _analyze().payload
    assert dict(payload.estimators) == {
        "risk_adjusted_return": CATALOG["sharpe_ratio"]["formula"],
        "drawdown": CATALOG["max_drawdown"]["formula"],
    }


def test_a_model_authored_formula_never_reaches_the_pack() -> None:
    poisoned = dict(MODEL_OUTPUT)
    poisoned["estimator:risk_adjusted_return"] = "mean(returns)"
    result = _analyze(runtime=StubRuntime(output=poisoned))
    assert result.status == "refused"
    assert result.reasons == ("ESTIMATOR_NOT_CATALOGUED",)
    assert result.payload is None


def test_a_finding_attributed_to_an_unfetched_metric_is_refused() -> None:
    poisoned = dict(MODEL_OUTPUT)
    poisoned["estimator:drawdown"] = "sortino_ratio"
    result = _analyze(runtime=StubRuntime(output=poisoned))
    assert result.status == "refused"
    assert result.reasons == ("ESTIMATOR_NOT_CATALOGUED",)


def test_an_uncatalogued_metric_is_refused() -> None:
    result = _analyze(metrics=("sharpe_ratio", "invented_alpha"))
    assert result.status == "refused"
    assert result.reasons == ("ESTIMATOR_NOT_CATALOGUED",)
    assert result.payload is None


def test_requesting_no_metrics_is_refused() -> None:
    result = _analyze(metrics=())
    assert result.status == "refused"
    assert result.reasons == ("METRICS_NOT_REQUESTED",)


def test_a_denied_tool_stops_the_run_before_the_receiver() -> None:
    port = StubPort()
    result = _analyze(port=port, tool_policies=_tool_policies(enabled=False))
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_TOOL_DENIED",)
    assert port.calls == []


def test_an_unregistered_catalog_tool_is_refused() -> None:
    policies = _tool_policies()
    del policies[METRIC_CATALOG_TOOL]
    result = _analyze(tool_policies=policies)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_TOOL_DENIED",)


def test_a_denied_sample_floor_tool_stops_the_run() -> None:
    # The catalog tool is authorized; only the floor tool is not. Without the
    # floor there is no threshold to check the sample against, so the run
    # cannot proceed on a default.
    policies = _tool_policies()
    policies[SAMPLE_FLOOR_TOOL] = _tool(SAMPLE_FLOOR_TOOL, enabled=False)
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    result = _analyze(tool_policies=policies, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_TOOL_DENIED",)
    assert runtime.invocations == []


def test_a_role_without_the_permission_class_is_denied() -> None:
    narrow = _policy(permission_classes=("compute_deterministic",))
    result = _analyze(policy=narrow)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_TOOL_DENIED",)


def test_tool_calls_are_audited_when_a_store_is_injected() -> None:
    store = build_in_memory_memory_store()
    _analyze(audit_store=store)
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 3


def test_registered_tool_names_are_stable() -> None:
    assert get_registered_tool_names() == (
        CONTRACT_VERSION_TOOL,
        METRIC_CATALOG_TOOL,
        SAMPLE_FLOOR_TOOL,
    )


# --------------------------------------------------------------------------
# FR-AGENTIC-035 - statistical disclosure is structural
# --------------------------------------------------------------------------


def test_the_pack_discloses_sample_and_multiple_testing_exposure() -> None:
    payload = _analyze().payload
    assert payload.sample_size == "512"
    assert payload.multiple_testing_exposure == "40"
    assert payload.dataset_hash == DATASET_HASH
    assert payload.configuration_hash == CONFIG_HASH
    assert payload.split_label == "holdout"


def test_disclosure_comes_from_the_caller_not_the_model() -> None:
    poisoned = dict(MODEL_OUTPUT)
    poisoned["sample_size"] = "1000000"
    poisoned["multiple_testing_exposure"] = "1"
    payload = _analyze(runtime=StubRuntime(output=poisoned)).payload
    assert payload.sample_size == "512"
    assert payload.multiple_testing_exposure == "40"


def test_every_finding_carries_an_estimator_and_uncertainty() -> None:
    payload = _analyze().payload
    assert set(payload.findings) == {"risk_adjusted_return", "drawdown"}
    assert set(payload.uncertainty) == set(payload.findings)
    assert payload.assumptions
    assert payload.limitations


@pytest.mark.parametrize("dropped", ["estimators", "uncertainty"])
def test_a_finding_missing_disclosure_is_unrepresentable(dropped) -> None:
    payload = _analyze().payload
    with pytest.raises(ValidationError, match="every finding requires"):
        build_quantitative_evidence_pack({**payload.model_dump(), dropped: {}})


def test_uncertainty_naming_an_unknown_finding_is_rejected() -> None:
    payload = _analyze().payload
    with pytest.raises(ValidationError, match="do not exist"):
        build_quantitative_evidence_pack(
            {
                **payload.model_dump(),
                "uncertainty": {
                    **dict(payload.uncertainty),
                    "ghost": "An interval for a finding that was never reported.",
                },
            },
        )


@pytest.mark.parametrize("field", ["assumptions", "limitations"])
def test_empty_required_disclosure_is_rejected(field) -> None:
    payload = _analyze().payload
    with pytest.raises(ValidationError, match="is required"):
        build_quantitative_evidence_pack({**payload.model_dump(), field: ()})


def test_catalogued_definitions_are_trusted_and_evidence_is_untrusted() -> None:
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    _analyze(runtime=runtime)
    invocation = runtime.invocations[0]
    assert invocation.trusted_context["sample_size"] == "512"
    assert invocation.trusted_context["minimum_sample"] == "30"
    assert (
        invocation.trusted_context["estimator:sharpe_ratio"]
        == CATALOG["sharpe_ratio"]["formula"]
    )
    assert any(
        key.startswith("research.edge_lab_profile")
        for key in invocation.untrusted_evidence
    )
    assert "sample_size" not in invocation.untrusted_evidence


def test_conflicts_are_preserved() -> None:
    payload = _analyze().payload
    assert payload.conflicts
    assert "disagree" in payload.conflicts[0]


@pytest.mark.parametrize(
    "text",
    [
        "The edge is approved for deployment.",
        "Use a position size of two lots.",
        "Place the order at market.",
        "Set the entry price at 1.0850.",
    ],
)
def test_execution_language_is_rejected(text) -> None:
    payload = _analyze().payload
    with pytest.raises(ValidationError):
        build_quantitative_evidence_pack(
            {**payload.model_dump(), "limitations": (text,)},
        )


def test_the_pack_is_frozen() -> None:
    payload = _analyze().payload
    with pytest.raises(ValidationError):
        payload.sample_size = "9"


# --------------------------------------------------------------------------
# FR-AGENTIC-036 - refuse rather than repair
# --------------------------------------------------------------------------


def test_the_schema_has_no_numeric_field() -> None:
    for name, field in QuantitativeEvidencePack.model_fields.items():
        annotation = str(field.annotation)
        assert "int" not in annotation, name
        assert "float" not in annotation, name
        assert "Decimal" not in annotation, name


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_statistic_is_refused_before_the_model(bad) -> None:
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    result = _analyze(statistics={**STATISTICS, "sharpe_ratio": bad}, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("NON_FINITE_INPUT",)
    assert runtime.invocations == []


def test_a_sample_below_the_catalogued_minimum_is_refused() -> None:
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    result = _analyze(sample_size=12, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("INSUFFICIENT_SAMPLE",)
    assert runtime.invocations == []


def test_the_sample_floor_comes_from_the_catalog_not_a_constant() -> None:
    # The same sample passes under a permissive floor and fails under a strict
    # one, so the threshold demonstrably comes from the receiver.
    permissive = StubPort(floors={**FLOORS, "statistical": "10"})
    strict = StubPort(floors={**FLOORS, "statistical": "5000"})
    assert _analyze(port=permissive, sample_size=12).status == "ok"
    assert _analyze(port=strict).reasons == ("INSUFFICIENT_SAMPLE",)


@pytest.mark.parametrize("field", ["dataset_hash", "configuration_hash"])
def test_misaligned_evidence_is_refused_rather_than_reconciled(field) -> None:
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    misaligned = {ref: dict(body) for ref, body in EVIDENCE.items()}
    misaligned["analytics.performance_report:v1"][field] = "sha256:other"
    result = _analyze(evidence=misaligned, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_NOT_ALIGNED",)
    assert runtime.invocations == []


@pytest.mark.parametrize("severity", ["high", "critical", "HIGH"])
def test_leakage_unsafe_evidence_is_refused(severity) -> None:
    runtime = StubRuntime(output=dict(MODEL_OUTPUT))
    result = _analyze(leakage_severity=severity, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("LEAKAGE_UNSAFE",)
    assert runtime.invocations == []


@pytest.mark.parametrize("severity", ["none", "low", "medium"])
def test_acceptable_leakage_severities_proceed(severity) -> None:
    result = _analyze(leakage_severity=severity)
    assert result.status == "ok"
    assert result.payload.leakage_status == severity


def test_absent_evidence_is_refused() -> None:
    result = _analyze(evidence={})
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_ABSENT",)


def test_an_unvalidated_finding_is_recorded_as_such() -> None:
    payload = _analyze().payload
    assert payload.validation_status == "unvalidated"


def test_a_model_refusal_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("EVIDENCE_UNINTERPRETABLE",))
    result = _analyze(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_UNINTERPRETABLE",)
    assert result.payload is None
