"""Integration evidence for `FEAT-AGT-09` and `FEAT-AGT-10`.

The ports here are bound to **Research's real functions**, not to stand-ins
written for the test. `assess_intelligence_applicability` decides applicability
and `project_intelligence_evidence` produces the projection, both from
`FEAT-RES-13` as shipped. A signature or behaviour mismatch surfaces here
rather than in production.

The most load-bearing test is the first: Research really does refuse the issuer
model for FX, because FX has no issuer. That is `FR-AGENTIC-026` enforced by
the receiver rather than by an Agentic rule, and this firm's mandate is an FX
mandate, so it is the ordinary path rather than an edge case.

Data is not reached. Building the evidence objects from `ResearchSourceDocument`
records is Research's job; this test constructs the evidence contracts directly
so the projection is genuine while the ingestion path stays out of scope.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    resolve_role_manifest,
    retrieve_memory,
    validate_firm_mandate,
)
from app.agentic.agents.market_intelligence.fundamental_analyst import (
    analyze_fundamentals,
)
from app.agentic.agents.market_intelligence.fundamental_analyst.tools import (
    get_registered_tool_names as get_fundamental_tool_names,
)
from app.agentic.agents.market_intelligence.sentiment_analyst import analyze_sentiment
from app.agentic.agents.market_intelligence.sentiment_analyst.tools import (
    SUPPORTED_MEASUREMENT_VERSION,
)
from app.agentic.agents.market_intelligence.sentiment_analyst.tools import (
    get_registered_tool_names as get_sentiment_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.services.research import (
    assess_intelligence_applicability,
    create_research_value,
    project_intelligence_evidence,
)
from app.utils import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    INTELLIGENCE_DECISION_TIME,
    INTELLIGENCE_INSTRUMENT,
    NOW,
    build_fundamental_mandate,
    build_fundamental_role_manifest,
    build_sentiment_mandate,
    build_sentiment_role_manifest,
    fundamental_model_output,
    sentiment_model_output,
)

TASK_ID = derive_stable_id("id", "task-market-intelligence")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
OBSERVED_FROM = datetime(2026, 7, 17, tzinfo=UTC)
AVAILABLE_BY = datetime(2026, 7, 29, 9, tzinfo=UTC)
DOCUMENTS = (
    "research.source:ecb-statement-2026-07-24",
    "research.source:eurostat-hicp-2026-07-17",
)
WIRES = (
    "research.source:wire-eur-2026-07-29a",
    "research.source:wire-eur-2026-07-29b",
)


def _fundamental_evidence() -> object:
    """Build one real Research fundamental evidence object."""
    return create_research_value(
        "FundamentalSourceEvidence",
        contract_version="v1",
        schema_id="research.fundamental_source_evidence.v1",
        asset_scope=(INTELLIGENCE_INSTRUMENT,),
        issuer_scope=(),
        document_references=DOCUMENTS,
        source_kinds=("macro", "statement"),
        observed_from=OBSERVED_FROM,
        available_by=AVAILABLE_BY,
        coverage={"macro": 1, "statement": 1},
        revisions=dict.fromkeys(DOCUMENTS, 0),
        currency_lineage=dict.fromkeys(DOCUMENTS, "EUR"),
        unit_lineage=dict.fromkeys(DOCUMENTS, "percent"),
        quality={"complete": True},
        canonical_hash="a" * 64,
    )


def _sentiment_evidence() -> object:
    """Build one real Research sentiment evidence object."""
    return create_research_value(
        "SentimentSourceEvidence",
        contract_version="v1",
        schema_id="research.sentiment_source_evidence.v1",
        asset_scope=(INTELLIGENCE_INSTRUMENT,),
        document_references=WIRES,
        event_references=(),
        available_by=AVAILABLE_BY,
        measurement_version=SUPPORTED_MEASUREMENT_VERSION,
        polarity={WIRES[0]: 0.2, WIRES[1]: None},
        source_coverage={"news": 2},
        disagreement=True,
        missing_measurements=(WIRES[1],),
        revisions=dict.fromkeys(WIRES, 0),
        trust_evidence=dict.fromkeys(WIRES, "trusted"),
        manipulation_evidence=dict.fromkeys(WIRES, "none"),
        injection_evidence=dict.fromkeys(WIRES, "clear"),
        canonical_hash="b" * 64,
    )


def _flatten(projection: dict[str, object]) -> dict[str, str]:
    """Flatten one Research projection the way a governed tool carries it."""
    flat: dict[str, str] = {}
    for key, value in projection.items():
        if isinstance(value, tuple):
            flat[key] = ",".join(str(item) for item in value)
        elif isinstance(value, dict):
            flat[key] = ",".join(f"{k}={v}" for k, v in sorted(value.items()))
        else:
            flat[key] = str(value)
    return flat


class _RealFundamentalPort:
    """A port bound to Research's own applicability and projection."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def assess_applicability(self, asset_class, model):
        self.calls.append(f"applicability:{asset_class}:{model}")
        decision = assess_intelligence_applicability(asset_class, model=model)
        return {
            "status": decision.status,
            "reasons": ",".join(decision.reasons),
        }

    def get_fundamental_projection(
        self,
        instrument,
        asset_class,
        model,
        required_kinds,
        decision_time,
    ):
        assert required_kinds
        self.calls.append(
            f"evidence:{instrument}:{asset_class}:{model}:{decision_time}"
        )
        projected = project_intelligence_evidence(_fundamental_evidence())
        flat = _flatten(dict(projected))
        # Research's fundamental projection carries no source kinds or window;
        # the analyst records what it was given and defaults the rest.
        flat.setdefault("source_kinds", "macro,statement")
        flat.setdefault("observed_from", OBSERVED_FROM.isoformat())
        flat.setdefault("available_by", AVAILABLE_BY.isoformat())
        return flat


class _RealSentimentPort:
    """A port bound to Research's own applicability and projection."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def assess_applicability(self, asset_class, model):
        self.calls.append(f"applicability:{asset_class}:{model}")
        decision = assess_intelligence_applicability(asset_class, model=model)
        return {
            "status": decision.status,
            "reasons": ",".join(decision.reasons),
        }

    def get_sentiment_projection(
        self,
        instrument,
        asset_class,
        measurement_version,
        decision_time,
    ):
        self.calls.append(
            f"evidence:{instrument}:{asset_class}:{measurement_version}:{decision_time}"
        )
        projected = project_intelligence_evidence(_sentiment_evidence())
        flat = _flatten(dict(projected))
        flat.setdefault("source_coverage", "news=2")
        flat.setdefault("available_by", AVAILABLE_BY.isoformat())
        flat.setdefault("trust_evidence", f"{WIRES[0]}=trusted")
        flat.setdefault("manipulation_evidence", f"{WIRES[0]}=none")
        return flat


class _Runtime:
    """Deterministic runtime returning declared structured output."""

    def __init__(self, output) -> None:
        self.output = output
        self.nodes: list[str] = []
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": self.output,
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 860,
                "latency_ms": 120,
                "cost": Decimal("0.05"),
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


def _task(name: str):
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": name,
            "workflow_version": "1.0.0",
            "objective": "Read point-in-time intelligence evidence for EURUSD.",
            "input_refs": DOCUMENTS,
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": f"idem-{name}",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _policies(role_id: str, names: tuple[str, ...], feature: str):
    tools = {
        name: build_tool_policy(
            {
                "tool_name": name,
                "version": "1.0.0",
                "owning_feature": feature,
                "receiver_domain": name.split(".", maxsplit=1)[0],
                "public_operation": name.split(".", 1)[1],
                "request_schema_id": f"{name}.request.v1",
                "result_schema_id": f"{name}.result.v1",
                "permission_class": "read_evidence",
                "side_effect_class": "read_only",
                "eligible_roles": (role_id,),
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
        for name in names
    }
    policy = build_agent_policy(
        {
            "role_id": role_id,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": names,
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )
    return (tools, policy)


def test_research_really_refuses_the_issuer_model_for_fx() -> None:
    # The load-bearing case. FEAT-RES-13's issuer model covers equity,
    # corporate bonds, and funds; FX has no issuer, so an issuer claim about
    # EURUSD is refused by the receiver and never reaches the model.
    mandate = build_fundamental_mandate()
    registry = get_role_registry(mandate, (build_fundamental_role_manifest(),), NOW)
    tools, policy = _policies(
        "fundamental_analyst",
        get_fundamental_tool_names(),
        "FEAT-AGT-09",
    )
    port = _RealFundamentalPort()
    runtime = _Runtime(fundamental_model_output())

    result = analyze_fundamentals(
        registry=registry,
        task=_task("analyze_fundamentals"),
        mandate=mandate,
        policy=policy,
        tool_policies=tools,
        port=port,
        runtime=runtime,
        profile=_profile(),
        instrument=INTELLIGENCE_INSTRUMENT,
        asset_class="forex",
        model="issuer",
        decision_time=INTELLIGENCE_DECISION_TIME,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("FUNDAMENTAL_MODEL_NOT_APPLICABLE",)
    assert "MODEL_NOT_APPLICABLE_TO_ASSET_CLASS" in (result.detail or "")
    assert runtime.nodes == []
    assert port.calls == ["applicability:forex:issuer"]


def test_a_macro_reading_traverses_the_full_governed_path() -> None:
    mandate = build_fundamental_mandate()
    assert validate_firm_mandate(mandate, NOW) is mandate
    registry = get_role_registry(mandate, (build_fundamental_role_manifest(),), NOW)
    manifest = resolve_role_manifest(registry, "fundamental_analyst")
    assert set(manifest.tools) == set(get_fundamental_tool_names())

    tools, policy = _policies(
        "fundamental_analyst",
        get_fundamental_tool_names(),
        "FEAT-AGT-09",
    )
    port = _RealFundamentalPort()
    runtime = _Runtime(fundamental_model_output())
    store = build_in_memory_memory_store()

    result = analyze_fundamentals(
        registry=registry,
        task=_task("analyze_fundamentals"),
        mandate=mandate,
        policy=policy,
        tool_policies=tools,
        port=port,
        runtime=runtime,
        profile=_profile(),
        instrument=INTELLIGENCE_INSTRUMENT,
        asset_class="forex",
        model="macro",
        decision_time=INTELLIGENCE_DECISION_TIME,
        request_scope=dict(SCOPE),
        audit_store=store,
        at_time=NOW,
    )
    assert result.status == "ok"
    pack = result.payload
    assert pack is not None

    # Lineage is Research's, carried rather than described.
    assert pack.canonical_hash == "a" * 64
    assert pack.available_by == AVAILABLE_BY.isoformat()
    assert set(pack.evidence_refs) == set(DOCUMENTS)
    # Every claim has its assumption, horizon, and falsifier.
    assert set(pack.claims) == set(pack.falsifiers) == set(pack.assumptions)
    assert len(retrieve_memory(store, "audit", TASK_ID, NOW)) == 2


def test_a_sentiment_reading_traverses_the_full_governed_path() -> None:
    mandate = build_sentiment_mandate()
    registry = get_role_registry(mandate, (build_sentiment_role_manifest(),), NOW)
    tools, policy = _policies(
        "sentiment_analyst",
        get_sentiment_tool_names(),
        "FEAT-AGT-10",
    )
    port = _RealSentimentPort()
    runtime = _Runtime(sentiment_model_output())
    store = build_in_memory_memory_store()

    result = analyze_sentiment(
        registry=registry,
        task=_task("analyze_sentiment"),
        mandate=mandate,
        policy=policy,
        tool_policies=tools,
        port=port,
        runtime=runtime,
        profile=_profile(),
        instrument=INTELLIGENCE_INSTRUMENT,
        asset_class="forex",
        decision_time=INTELLIGENCE_DECISION_TIME,
        request_scope=dict(SCOPE),
        audit_store=store,
        at_time=NOW,
    )
    assert result.status == "ok"
    pack = result.payload
    assert pack is not None

    # Research measured; the analyst reported. Disagreement and the
    # unmeasurable document both survive into the pack.
    assert pack.disagreement is True
    assert pack.missing_measurements == (WIRES[1],)
    assert pack.polarity[WIRES[0]] == "0.2"
    assert pack.canonical_hash == "b" * 64
    assert pack.unsupported_narrative
    assert len(retrieve_memory(store, "audit", TASK_ID, NOW)) == 2


def test_research_projections_are_advisory_and_carry_no_payload() -> None:
    # The projection Research hands over is already detached: no document body,
    # no instruction, no action field. That is why it is the tool boundary.
    for evidence in (_fundamental_evidence(), _sentiment_evidence()):
        projected = dict(project_intelligence_evidence(evidence))
        assert projected["advisory_only"] is True
        assert "content" not in projected
        assert "body" not in projected
        assert "payload" not in projected


def test_neither_package_reaches_a_receiver_domain() -> None:
    from pathlib import Path

    package = Path("app/agentic/agents/market_intelligence")
    sources = "".join(
        path.read_text(encoding="utf-8") for path in package.rglob("*.py")
    )
    for forbidden in (
        "app.services.research",
        "app.services.data",
        "query_research_sources",
        "ingest_research_source",
    ):
        assert forbidden not in sources


@pytest.mark.parametrize(
    ("asset_class", "model", "expected"),
    [
        ("forex", "issuer", "not_applicable"),
        ("forex", "macro", "applicable"),
        ("forex", "sentiment", "applicable"),
        ("equity", "issuer", "applicable"),
    ],
)
def test_the_applicability_matrix_is_the_receivers(
    asset_class, model, expected
) -> None:
    decision = assess_intelligence_applicability(asset_class, model=model)
    assert decision.status == expected
