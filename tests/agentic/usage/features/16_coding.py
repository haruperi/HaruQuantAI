"""Executable FEAT-AGT-16 Coder usage example.

Demonstrates the registered public operation through the documented API. The
sandbox and the Indicators registry both arrive as injected doubles: nothing is
executed, no receiver is reached, no network call occurs, and Agentic holds no
credential.

The point of the demonstration is where authority sits — a human authorises the
specification, an attested lease gates generation, the registry decides which
indicators exist, and every declared path is checked before a byte is written.

Everything is staged under a temporary directory that this program creates and
removes. Nothing is written inside the repository.
"""

import shutil
import sys
import tempfile
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
from app.agentic.agents.engineering.coder import (
    author_code_artifact,
    build_code_artifact,
    build_code_specification,
)
from app.agentic.agents.engineering.coder.agent import AUTHORING_PERMISSION
from app.agentic.agents.engineering.coder.artifact_store import (
    validate_relative_path,
    verify_staged_artifact,
)
from app.agentic.agents.engineering.coder.sandbox import build_deterministic_sandbox
from app.agentic.agents.engineering.coder.schemas import derive_artifact_hash
from app.agentic.agents.engineering.coder.tools import get_registered_tool_names
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    build_coder_mandate,
    build_coder_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-coder-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
PRINCIPAL = "operator-owner"

REGISTERED = {"ema": "1.0.0", "atr": "1.0.0", "rsi": "1.0.0"}

SOURCE = '''"""Generated session-overlap momentum evaluator."""


class OverlapMomentumEvaluator:
    """Consumes precomputed indicators and emits signals."""

    strategy_id = "overlap-momentum"
    strategy_version = "0.1.0"

    def evaluate_signals(self, evidence, indicators, config, context):
        """Emit signals from precomputed indicators only."""
        del evidence, config, context
        return indicators
'''

TEST_SOURCE = '''"""Generated tests for the overlap momentum evaluator."""


def test_evaluator_declares_the_contract_fields():
    assert True
'''

MODEL_OUTPUT = {
    "file:overlap_momentum.py": SOURCE,
    "file:tests/test_overlap_momentum.py": TEST_SOURCE,
    "dependency:numpy": "2.4.6",
    "search_history": (
        "attempt 1: drafted the evaluator against SignalEvaluator\n"
        "attempt 2: added the warmup boundary test"
    ),
}

HOSTILE_PATHS = (
    "/etc/passwd",
    "../../escape.py",
    "C:/Windows/System32/evil.py",
    "CON.py",
    "evil.py:stream",
    "a/./b.py",
    "trailing.py.",
    "run.exe",
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicAuth:
    """Structural stand-in for an authenticated human principal."""

    def __init__(self, **overrides):
        self.principal_id = overrides.get("principal_id", PRINCIPAL)
        self.principal_type = overrides.get("principal_type", "USER")
        self.permissions = overrides.get("permissions", (AUTHORING_PERMISSION,))
        self.tenant_or_environment = overrides.get("tenant_or_environment", "sandbox")


class DeterministicRegistryPort:
    """Deterministic Indicators registry port."""

    def __init__(self, registered=None):
        self.registered = REGISTERED if registered is None else registered
        self.calls = []

    def list_registered_indicators(self):
        """Return every registered indicator and its version."""
        self.calls.append("list")
        return dict(self.registered)


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, output=None, status="ok", reasons=()):
        self.output = None if status != "ok" else (output or MODEL_OUTPUT)
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
                "tokens_used": 2_200,
                "latency_ms": 850,
                "cost": Decimal("0.11"),
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
    """Build the bounded governed authoring task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "author_code_artifact",
            "workflow_version": "1.0.0",
            "objective": "Author a staged evaluator for the overlap thesis.",
            "input_refs": ("agentic.strategy_thesis:overlap",),
            "principal_id": PRINCIPAL,
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-coder-usage",
            "budgets": {"cost": Decimal("3.00")},
        },
    )


def make_specification(**overrides):
    """Build the authenticated human code specification."""
    data = {
        "specification_id": derive_stable_id("id", "spec-usage"),
        "task_id": TASK_ID,
        "principal_id": PRINCIPAL,
        "artifact_kinds": ("strategy_evaluator",),
        "objective": "Implement a session-overlap momentum evaluator.",
        "target_contract": "strategy.signal_evaluator.v1",
        "acceptance_criteria": (
            "Consumes precomputed indicators only.",
            "Uses no value unavailable at decision time.",
        ),
        "required_indicators": ("ema", "atr"),
        "thesis_refs": ("agentic.strategy_thesis:overlap",),
        "environment": "sandbox",
    }
    data.update(overrides)
    return build_code_specification(data)


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-16",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("coder",),
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
    """Build the coder agent policy."""
    return build_agent_policy(
        {
            "role_id": "coder",
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def author(staging, **overrides):
    """Author one artefact with the deterministic doubles."""
    data = {
        "registry": get_role_registry(
            build_coder_mandate(),
            (build_coder_role_manifest(),),
            NOW,
        ),
        "task": make_task(),
        "mandate": build_coder_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "registry_port": DeterministicRegistryPort(),
        "sandbox": build_deterministic_sandbox(str(staging)),
        "runtime": DeterministicRuntime(),
        "profile": make_profile(),
        "specification": make_specification(),
        "auth": DeterministicAuth(),
        "staging_root": staging,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return author_code_artifact(**data)


def fr_agentic_046(staging: Path) -> None:
    """FR-AGENTIC-046: Authenticated specification and attested isolation."""
    _header(
        "FR-AGENTIC-046: Code generation requires an authenticated "
        "specification and an ephemeral, resource-bounded, credential-free, "
        "network-denied sandbox."
    )

    sandbox = build_deterministic_sandbox(str(staging))
    audit = build_in_memory_memory_store()
    result = author(staging, sandbox=sandbox, audit_store=audit)
    print(f"  authored:            {result.status}")
    print(f"  leases opened:       {len(sandbox.opened)}")
    print(f"  leases closed:       {len(sandbox.closed)}  (ephemeral, so destroyed)")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )

    print("\n  A lease missing any one property fails closed:")
    for missing in ("ephemeral", "credential_free", "network_denied"):
        runtime = DeterministicRuntime()
        refused = author(
            staging,
            sandbox=build_deterministic_sandbox(str(staging), **{missing: False}),
            runtime=runtime,
        )
        print(
            f"    no {missing:<16} -> {refused.status} ({refused.reasons[0]}), "
            f"model calls: {len(runtime.invocations)}"
        )

    print("\n  A specification that is not authenticated by a human is refused:")
    for label, override in (
        ("service account", {"principal_type": "SERVICE_ACCOUNT"}),
        ("no permission", {"permissions": ()}),
        ("different principal", {"principal_id": "someone-else"}),
        ("wrong environment", {"tenant_or_environment": "production"}),
    ):
        runtime = DeterministicRuntime()
        refused = author(
            staging,
            auth=DeterministicAuth(**override),
            runtime=runtime,
        )
        print(
            f"    {label:<20} -> {refused.status} ({refused.reasons[0]}), "
            f"model calls: {len(runtime.invocations)}"
        )


def fr_agentic_047(staging: Path) -> None:
    """FR-AGENTIC-047: The manifest is complete or the artefact does not exist."""
    _header(
        "FR-AGENTIC-047: Generated artefacts record files, dependency data, "
        "tests, hashes, model/prompt/tool provenance, and complete search "
        "history."
    )

    artifact = author(staging).payload
    print(f"  artefact digest:  {artifact.artifact_hash}")
    print(f"  kind:             {artifact.kind}")
    print(f"  dependencies:     {dict(artifact.dependencies)}")
    print(f"  tests:            {artifact.tests}")
    print(f"  tool refs:        {artifact.tool_refs}")
    print(f"  model profile:    {artifact.model_profile_id}")
    print(f"  prompt digest:    {artifact.base_prompt_hash[:32]}...")
    print(f"  instruction hash: {artifact.composite_instruction_hash[:32]}...")
    for entry in artifact.search_history:
        print(f"  search history:   {entry}")
    for generated in artifact.files:
        print(
            f"  file {generated.relative_path:<34} "
            f"{generated.byte_count:>5} bytes  {generated.content_hash[:16]}..."
        )

    altered = {**artifact.model_dump(), "search_history": ("attempt 1: nothing",)}
    print(
        "  altering the manifest changes its digest: "
        f"{derive_artifact_hash(altered) != artifact.artifact_hash}"
    )

    for field in ("tests", "search_history"):
        try:
            build_code_artifact({**artifact.model_dump(), field: ()})
            outcome = f"ERROR: an artefact with no {field} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"An artefact with no {field} is unrepresentable"
        print(f"  {outcome}")


def fr_agentic_048(staging: Path) -> None:
    """FR-AGENTIC-048: Staging only, and never imported or executed."""
    _header(
        "FR-AGENTIC-048: The coder writes only to staging; generated code is "
        "never imported, executed, registered, or deployed."
    )

    artifact = author(staging).payload
    written = sorted(
        path.relative_to(staging).as_posix()
        for path in staging.rglob("*")
        if path.is_file()
    )
    print(f"  staged under:    {artifact.staging_path}")
    for path in written:
        print(f"  wrote:           {path}")
    print(f"  digests verify:  {verify_staged_artifact(staging, artifact) == ()}")

    print("\n  Hostile paths are rejected rather than normalized:")
    for candidate in HOSTILE_PATHS:
        failure = validate_relative_path(candidate)
        print(f"    {candidate:<34} -> {failure}")

    print("\n  Promotion readiness is structural:")
    blocked = author(
        staging,
        specification=make_specification(
            artifact_kinds=("indicator_candidate", "strategy_evaluator"),
            required_indicators=("ema", "kalman_slope"),
        ),
    ).payload
    print(f"    unregistered indicators: {blocked.unregistered_indicators}")
    print(f"    promotion status:        {blocked.promotion_status}")
    try:
        build_code_artifact({**blocked.model_dump(), "promotion_status": "ready"})
        outcome = "ERROR: a blocked artefact claimed readiness"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "A blocked artefact cannot claim readiness"
    print(f"    {outcome}")

    runtime = DeterministicRuntime()
    refused = author(
        staging,
        specification=make_specification(required_indicators=("ema", "kalman_slope")),
        runtime=runtime,
    )
    print(
        f"    unauthorised indicator -> {refused.status} ({refused.reasons[0]}), "
        f"model calls: {len(runtime.invocations)}"
    )


def main() -> None:
    """Run every functional-requirement demonstration for the coder."""
    staging = Path(tempfile.mkdtemp(prefix="agentic-coder-usage-"))
    try:
        fr_agentic_046(staging)
        fr_agentic_047(staging)
        fr_agentic_048(staging)
        print(f"\nStaging root used and removed: {staging}")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-16", main)
