"""Shared bounded secret-safe Agentic test fixtures.

Builds a realistic `sandbox` mandate and roster through the public governance
builders, so every consumer exercises the same integrity-digest chain the
registry validates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.agentic import build_firm_mandate, build_role_manifest
from app.agentic.agents.engineering.coder.agent import (
    PROMPT_PATH as CODER_PROMPT_PATH,
)
from app.agentic.agents.engineering.coder.schemas import (
    CodeArtifact,
    build_code_artifact,
    build_generated_file,
    build_sandbox_result,
)
from app.agentic.agents.engineering.coder.tools import (
    get_registered_tool_names as get_coder_tool_names,
)
from app.agentic.agents.experimentation.experiment_designer.agent import (
    PROMPT_PATH as DESIGNER_PROMPT_PATH,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    ExperimentVerdict,
    build_experiment_verdict,
)
from app.agentic.agents.experimentation.experiment_designer.tools import (
    get_registered_tool_names as get_designer_tool_names,
)
from app.agentic.agents.experimentation.optimization_coordinator.agent import (
    PROMPT_PATH as SWEEP_PROMPT_PATH,
)
from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
    SweepVerdict,
    build_sweep_verdict,
    build_trial_ledger,
)
from app.agentic.agents.experimentation.optimization_coordinator.tools import (
    get_registered_tool_names as get_sweep_tool_names,
)
from app.agentic.agents.experimentation.simulation_interpreter.agent import (
    PROMPT_PATH,
)
from app.agentic.agents.experimentation.simulation_interpreter.agent import (
    ROLE_ID as INTERPRETER_ROLE_ID,
)
from app.agentic.agents.market_analysis.quantitative_analyst.agent import (
    PROMPT_PATH as QUANT_PROMPT_PATH,
)
from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
    get_registered_tool_names as get_quant_tool_names,
)
from app.agentic.agents.market_analysis.technical_analyst.agent import (
    PROMPT_PATH as TECHNICAL_PROMPT_PATH,
)
from app.agentic.agents.market_analysis.technical_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.agents.market_intelligence.fundamental_analyst.agent import (
    PROMPT_PATH as FUNDAMENTAL_PROMPT_PATH,
)
from app.agentic.agents.market_intelligence.fundamental_analyst.tools import (
    get_registered_tool_names as get_fundamental_tool_names,
)
from app.agentic.agents.market_intelligence.sentiment_analyst.agent import (
    PROMPT_PATH as SENTIMENT_PROMPT_PATH,
)
from app.agentic.agents.market_intelligence.sentiment_analyst.tools import (
    get_registered_tool_names as get_sentiment_tool_names,
)
from app.agentic.agents.operations.evaluation_manager.agent import (
    PROMPT_PATH as EVALUATION_PROMPT_PATH,
)
from app.agentic.agents.operations.evaluation_manager.evaluator import (
    REQUIRED_CHALLENGE_KINDS,
)
from app.agentic.agents.operations.evaluation_manager.schemas import (
    CritiqueMemo,
    build_critique_memo,
)
from app.agentic.agents.operations.evaluation_manager.tools import (
    get_registered_tool_names as get_evaluation_tool_names,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.agent import (
    PROMPT_PATH as ADVISOR_PROMPT_PATH,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    REQUIRED_RISK_KINDS,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (
    ACCOUNT_STATE_TOOL,
    ALLOCATION_EVIDENCE_TOOL,
    COMMON_MODE_TOOL,
    CORRELATION_TOOL,
    FIRM_MANDATE_TOOL,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (
    get_registered_tool_names as get_advisor_tool_names,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst.agent import (
    PROMPT_PATH as THESIS_PROMPT_PATH,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst.schemas import (
    StrategyThesis,
    build_strategy_thesis,
)
from app.agentic.agents.strategy_desk.trader.agent import (
    PROMPT_PATH as TRADER_PROMPT_PATH,
)
from app.agentic.governance import FirmMandate, RoleManifest
from app.agentic.governance.models import UNIVERSAL_PROHIBITIONS
from app.agentic.governance.registry import normalize_prompt_text
from app.agentic.lifecycle.models import PROMOTION_PERMISSION
from app.utils import canonical_digest

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
MANDATE_START = datetime(2026, 7, 1, tzinfo=UTC)
MANDATE_END = datetime(2026, 12, 31, tzinfo=UTC)

LIMITS_PROFILE_ID = "agentic-limits-sandbox-v1"
MODEL_PROFILE_ID = "profile-market-analysis-a"
FALLBACK_PROFILE_ID = "profile-market-analysis-b"

TECHNICAL_ROLE_ID = "technical_analyst"
QUANT_ROLE_ID = "quantitative_analyst"

PROMPT_DIGEST = canonical_digest("technical-analyst-base-prompt")

READ_TOOL = "data.get_market_data"
COMPUTE_TOOL = "indicators.validate_indicator"


def mandate_fields(**overrides: object) -> dict[str, object]:
    """Return complete firm-mandate fields excluding derived values.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        Complete mandate constructor data.
    """
    data: dict[str, object] = {
        "mandate_id": "mandate-sandbox",
        "version": "1.0.0",
        "environment": "sandbox",
        "effective_at": MANDATE_START,
        "expires_at": MANDATE_END,
        "owner_principal": "operator-owner",
        "objectives": ("market_research", "risk_advisory"),
        "asset_scopes": {"asset_class": "fx", "venue": "otc"},
        "enabled_features": ("FEAT-AGT-11", "FEAT-AGT-12"),
        "enabled_roles": (TECHNICAL_ROLE_ID, QUANT_ROLE_ID),
        "model_profiles": (MODEL_PROFILE_ID, FALLBACK_PROFILE_ID),
        "tool_scopes": {
            READ_TOOL: "read_evidence",
            COMPUTE_TOOL: "compute_deterministic",
        },
        "limits_profile_id": LIMITS_PROFILE_ID,
        "budgets": {"cost": Decimal("50.00"), "tokens": Decimal(500_000)},
        "approval_policy": ("artifact_promotion", "trade_proposal_submission"),
        "retention_policy": {"evidence": "365d", "audit": "730d"},
        "prohibited_actions": UNIVERSAL_PROHIBITIONS,
        "fallback_policy": "refuse",
    }
    data.update(overrides)
    return data


def manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete role-manifest fields excluding derived digests.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data: dict[str, object] = {
        "role_id": TECHNICAL_ROLE_ID,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-11",
        "department": "market_analysis",
        "agent_package": "agents/market_analysis/technical_analyst",
        "description": "Interprets canonical Data and Indicators evidence.",
        "objective": "Describe observable market structure with invalidation.",
        "expertise_boundary": "Does not size positions or approve any action.",
        "supported_assets": ("fx",),
        "refusal_conditions": ("missing_evidence", "stale_evidence"),
        "input_schema_id": "agentic.technical_request.v1",
        "output_schema_id": "agentic.technical_evidence_pack.v1",
        "base_prompt_hash": canonical_digest("technical-analyst-base-prompt"),
        "role_instruction": None,
        "model_profile_id": MODEL_PROFILE_ID,
        "permitted_fallback": FALLBACK_PROFILE_ID,
        "tools": (READ_TOOL, COMPUTE_TOOL),
        "permission_classes": ("read_evidence", "compute_deterministic"),
        "data_requirements": ("canonical_market_data", "indicator_versions"),
        "freshness_seconds": 900,
        "budgets": {"cost": Decimal("2.50"), "tokens": Decimal(40_000)},
        "evaluation_set_id": "eval-technical-v1",
        "baseline_id": "baseline-deterministic-indicators",
        "enabled": True,
    }
    data.update(overrides)
    return data


def quant_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete quantitative-analyst manifest fields.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=QUANT_ROLE_ID,
        owning_feature="FEAT-AGT-12",
        agent_package="agents/market_analysis/quantitative_analyst",
        description="Analyses versioned Research and Analytics evidence.",
        input_schema_id="agentic.quantitative_request.v1",
        output_schema_id="agentic.quantitative_evidence_pack.v1",
        base_prompt_hash=canonical_digest("quantitative-analyst-base-prompt"),
        evaluation_set_id="eval-quantitative-v1",
    )
    data.update(overrides)
    return data


def build_sandbox_mandate(**overrides: object) -> FirmMandate:
    """Build the validated sandbox firm mandate.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    return build_firm_mandate(mandate_fields(**overrides), "owner-signature-sandbox")


def build_technical_manifest(**overrides: object) -> RoleManifest:
    """Build the validated technical-analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(manifest_fields(**overrides))


def build_quant_manifest(**overrides: object) -> RoleManifest:
    """Build the validated quantitative-analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(quant_manifest_fields(**overrides))


INTERPRETER_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(PROMPT_PATH.read_text(encoding="utf-8")),
)


def interpreter_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Simulation Interpreter manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=INTERPRETER_ROLE_ID,
        owning_feature="FEAT-AGT-08",
        department="experimentation",
        agent_package="agents/experimentation/simulation_interpreter",
        description=(
            "Interprets completed deterministic evidence without recomputation."
        ),
        objective="State what an artefact shows, omits, and leaves unanswered.",
        expertise_boundary="Does not recompute, size, approve, or execute.",
        input_schema_id="agentic.run_interpretation_request.v1",
        output_schema_id="agentic.run_interpretation.v1",
        base_prompt_hash=INTERPRETER_PROMPT_DIGEST,
        evaluation_set_id="eval-simulation-interpreter-v1",
        tools=(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_interpreter_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Simulation Interpreter role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(interpreter_manifest_fields(**overrides))


def build_interpreter_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate enabling only the Simulation Interpreter.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-08",),
        "enabled_roles": (INTERPRETER_ROLE_ID,),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


TECHNICAL_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(TECHNICAL_PROMPT_PATH.read_text(encoding="utf-8")),
)


def technical_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Technical Analyst manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        base_prompt_hash=TECHNICAL_PROMPT_DIGEST,
        tools=get_registered_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_technical_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Technical Analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(technical_role_manifest_fields(**overrides))


def build_technical_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the technical analyst tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-11",),
        "enabled_roles": (TECHNICAL_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_registered_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


QUANT_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(QUANT_PROMPT_PATH.read_text(encoding="utf-8")),
)


def quantitative_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Quantitative Analyst manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = quant_manifest_fields(
        objective="State what the statistics support and what would refute it.",
        expertise_boundary="Interprets statistics; computes and estimates none.",
        base_prompt_hash=QUANT_PROMPT_DIGEST,
        tools=get_quant_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_quantitative_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Quantitative Analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(quantitative_role_manifest_fields(**overrides))


def build_quantitative_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the quantitative analyst tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-12",),
        "enabled_roles": (QUANT_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_quant_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


THESIS_ROLE_ID = "strategy_thesis_analyst"

THESIS_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(THESIS_PROMPT_PATH.read_text(encoding="utf-8")),
)


def thesis_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Strategy Thesis Analyst manifest fields.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=THESIS_ROLE_ID,
        owning_feature="FEAT-AGT-13",
        department="strategy_desk",
        agent_package="agents/strategy_desk/strategy_thesis_analyst",
        description="Forms falsifiable hypotheses and non-executable theses.",
        objective="State what may be true, why, and what would refute it.",
        expertise_boundary="Writes no code and specifies no order, price, or size.",
        input_schema_id="agentic.thesis_request.v1",
        output_schema_id="agentic.strategy_thesis.v1",
        base_prompt_hash=THESIS_PROMPT_DIGEST,
        evaluation_set_id="eval-strategy-thesis-v1",
        tools=(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_thesis_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Strategy Thesis Analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(thesis_role_manifest_fields(**overrides))


def build_thesis_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate enabling only the thesis analyst.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-13",),
        "enabled_roles": (THESIS_ROLE_ID,),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


DESIGNER_ROLE_ID = "experiment_designer"

DESIGNER_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(DESIGNER_PROMPT_PATH.read_text(encoding="utf-8")),
)


def designer_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Experiment Designer manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=DESIGNER_ROLE_ID,
        owning_feature="FEAT-AGT-14",
        department="experimentation",
        agent_package="agents/experimentation/experiment_designer",
        description="Designs pre-registered protocols and reads executed runs.",
        objective="Specify what would refute a thesis, then read what ran.",
        expertise_boundary="Runs nothing and authors no receiver request.",
        input_schema_id="agentic.experiment_request.v1",
        output_schema_id="agentic.experiment_spec.v1",
        base_prompt_hash=DESIGNER_PROMPT_DIGEST,
        evaluation_set_id="eval-experiment-designer-v1",
        tools=get_designer_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_designer_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Experiment Designer role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(designer_role_manifest_fields(**overrides))


def build_designer_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the experiment designer tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-14",),
        "enabled_roles": (DESIGNER_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_designer_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


CODER_ROLE_ID = "coder"

CODER_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(CODER_PROMPT_PATH.read_text(encoding="utf-8")),
)


def coder_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Coder manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=CODER_ROLE_ID,
        owning_feature="FEAT-AGT-16",
        department="engineering",
        agent_package="agents/engineering/coder",
        description="Authors staged code artefacts under a human specification.",
        objective="Implement the declared contract and the tests that refute it.",
        expertise_boundary="Stages only; imports, executes, and deploys nothing.",
        input_schema_id="agentic.code_specification.v1",
        output_schema_id="agentic.code_artifact.v1",
        base_prompt_hash=CODER_PROMPT_DIGEST,
        evaluation_set_id="eval-coder-v1",
        tools=get_coder_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_coder_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Coder role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(coder_role_manifest_fields(**overrides))


def build_coder_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the coder tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-16",),
        "enabled_roles": (CODER_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_coder_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


SWEEP_ROLE_ID = "optimization_coordinator"

SWEEP_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(SWEEP_PROMPT_PATH.read_text(encoding="utf-8")),
)


def sweep_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Optimization Coordinator manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=SWEEP_ROLE_ID,
        owning_feature="FEAT-AGT-15",
        department="experimentation",
        agent_package="agents/experimentation/optimization_coordinator",
        description="Declares bounded searches and reads them for robustness.",
        objective="Report what the whole search showed, not its best row.",
        expertise_boundary="Runs no sweep and computes no robustness measure.",
        input_schema_id="agentic.sweep_request.v1",
        output_schema_id="agentic.sweep_verdict.v1",
        base_prompt_hash=SWEEP_PROMPT_DIGEST,
        evaluation_set_id="eval-optimization-coordinator-v1",
        tools=get_sweep_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_sweep_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Optimization Coordinator role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(sweep_role_manifest_fields(**overrides))


def build_sweep_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the optimization tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-15",),
        "enabled_roles": (SWEEP_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_sweep_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


EVALUATION_ROLE_ID = "evaluation_manager"

EVALUATION_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(EVALUATION_PROMPT_PATH.read_text(encoding="utf-8")),
)


def evaluation_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Evaluation Manager manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=EVALUATION_ROLE_ID,
        owning_feature="FEAT-AGT-17",
        department="operations",
        agent_package="agents/operations/evaluation_manager",
        description="Evaluates roles and critiques candidates adversarially.",
        objective="Find the reason a candidate should not proceed.",
        expertise_boundary="Grades nothing, computes nothing, mutates nothing.",
        input_schema_id="agentic.evaluation_request.v1",
        output_schema_id="agentic.economic_acceptance_verdict.v1",
        base_prompt_hash=EVALUATION_PROMPT_DIGEST,
        evaluation_set_id="eval-evaluation-manager-v1",
        tools=get_evaluation_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_evaluation_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Evaluation Manager role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(evaluation_role_manifest_fields(**overrides))


def build_evaluation_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the evaluation tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-17",),
        "enabled_roles": (EVALUATION_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_evaluation_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


# --------------------------------------------------------------------------
# FEAT-AGT-18 promotion evidence
#
# Lifecycle has no role and therefore no manifest. What it needs instead are
# real instances of the four contracts a promotion packet carries, built
# through the owning features' own constructors so the packet is assembled
# from the same objects production would hand it.
# --------------------------------------------------------------------------

PROMOTION_TASK_ID = "task-promotion-a"
PROMOTION_ENVIRONMENT = "sandbox"
PROMOTION_APPROVER_ID = "user-reviewer-a"


class ApprovingUser:
    """A human principal shaped like a `utils.auth_context.v1`."""

    def __init__(
        self,
        principal_id: str = PROMOTION_APPROVER_ID,
        principal_type: str = "USER",
        permissions: tuple[str, ...] = (PROMOTION_PERMISSION,),
        tenant_or_environment: str = PROMOTION_ENVIRONMENT,
    ) -> None:
        """Initialize the approving principal.

        Args:
            principal_id: Authenticated identity.
            principal_type: USER or SERVICE_ACCOUNT.
            permissions: Fine-grained permissions held.
            tenant_or_environment: Environment the context was issued for.
        """
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.permissions = permissions
        self.tenant_or_environment = tenant_or_environment


def build_promotion_artifact(**overrides: object) -> CodeArtifact:
    """Build a real `FEAT-AGT-16` staged artefact as promotion evidence.

    Args:
        **overrides: Optional field overrides for artefact variants.

    Returns:
        A validated immutable artefact carrying its manifest digest.
    """
    data: dict[str, object] = {
        "artifact_id": "artifact-promotion-a",
        "task_id": PROMOTION_TASK_ID,
        "specification_id": "spec-promotion-a",
        "kind": "strategy_evaluator",
        "files": (
            build_generated_file(
                "momentum/evaluator.py",
                "def evaluate_signals(bars):\n    return ()\n",
            ),
        ),
        "dependencies": {"numpy": "2.4.6"},
        "tests": ("test_evaluate_signals_returns_no_signal_on_empty_bars",),
        "required_indicators": ("sma",),
        "unregistered_indicators": (),
        "model_profile_id": MODEL_PROFILE_ID,
        "base_prompt_hash": CODER_PROMPT_DIGEST,
        "composite_instruction_hash": canonical_digest("coder-composite-a"),
        "tool_refs": ("indicators.list_indicators",),
        "search_history": ("attempt 1: authored the evaluator",),
        "sandbox_result": build_sandbox_result(
            {
                "result_id": "sandbox-promotion-a",
                "lease_id": "lease-promotion-a",
                "compiled": True,
                "tests_run": 1,
                "tests_passed": 1,
                "duration_seconds": 3,
            },
        ),
        "staging_path": "artifact-promotion-a",
        "promotion_status": "ready",
    }
    data.update(overrides)
    return build_code_artifact(data)


def build_promotion_experiment_verdict(**overrides: object) -> ExperimentVerdict:
    """Build a real `FEAT-AGT-14` experiment verdict as promotion evidence.

    Args:
        **overrides: Optional field overrides for verdict variants.

    Returns:
        A validated immutable experiment verdict.
    """
    data: dict[str, object] = {
        "verdict_id": "verdict-experiment-promotion-a",
        "task_id": PROMOTION_TASK_ID,
        "spec_id": "spec-experiment-a",
        "spec_hash": canonical_digest("experiment-spec-a"),
        "conclusions": {"run-a": "The refuting outcome did not occur."},
        "evidence_classes": {"run-a": "validation"},
        "outcome": "not_refuted",
        "holdout_consumed": False,
        "limitations": ("One split cannot establish stability across regimes.",),
    }
    data.update(overrides)
    return build_experiment_verdict(data)


def build_promotion_sweep_verdict(**overrides: object) -> SweepVerdict:
    """Build a real `FEAT-AGT-15` sweep verdict as promotion evidence.

    Args:
        **overrides: Optional field overrides for verdict variants.

    Returns:
        A validated immutable sweep verdict.
    """
    data: dict[str, object] = {
        "verdict_id": "verdict-sweep-promotion-a",
        "task_id": PROMOTION_TASK_ID,
        "plan_id": "plan-sweep-a",
        "plan_hash": canonical_digest("sweep-plan-a"),
        "search_id": "search-promotion-a",
        "reproducibility_hash": canonical_digest("sweep-evidence-a"),
        "receiver_decision": "validation_needed",
        "trials": build_trial_ledger(
            {
                "attempted": 24,
                "completed": 24,
                "failed": 0,
                "failure_reasons": {},
                "budget": 24,
            },
        ),
        "selected_parameters": {"period": "20"},
        "robustness_evidence": "robustness: score=62.5",
        "instability_evidence": "stability: stability_percentage=41.7",
        "overfit_evidence": "overfit: degradation=0.34",
        "economic_effect": "The gain exceeds the modelled spread.",
        "unresolved_risk": ("The optimum sits on a narrow ridge.",),
        "holdout_consumed": False,
        "lifetime_trials": 24,
    }
    data.update(overrides)
    return build_sweep_verdict(data)


def build_promotion_critique(**overrides: object) -> CritiqueMemo:
    """Build a real `FEAT-AGT-17` critique memo as promotion evidence.

    Args:
        **overrides: Optional field overrides for memo variants.

    Returns:
        A validated immutable critique memo.
    """
    data: dict[str, object] = {
        "memo_id": "memo-promotion-a",
        "task_id": PROMOTION_TASK_ID,
        "candidate_ref": "agentic.code_artifact:artifact-promotion-a",
        "challenges": {
            kind: (
                f"The {kind} challenge was examined against the supplied "
                "evidence and what it could not establish is stated."
            )
            for kind in sorted(REQUIRED_CHALLENGE_KINDS)
        },
        "unsubstantiated": (),
        "blocking_concerns": (),
        "evidence_refs": ("agentic.sweep_verdict:search-promotion-a",),
    }
    data.update(overrides)
    return build_critique_memo(data)


ADVISOR_ROLE_ID = "portfolio_risk_advisor"

ADVISOR_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(ADVISOR_PROMPT_PATH.read_text(encoding="utf-8")),
)


def advisor_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Portfolio and Risk Advisor manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=ADVISOR_ROLE_ID,
        owning_feature="FEAT-AGT-19",
        department="portfolio_risk_advisory",
        agent_package="agents/portfolio_risk_advisory/portfolio_risk_advisor",
        description="Describes exposure and critiques what could go wrong.",
        objective="State where emphasis sits and what the evidence cannot show.",
        expertise_boundary="Approves nothing, sizes nothing, computes nothing.",
        input_schema_id="agentic.advisory_request.v1",
        output_schema_id="agentic.allocation_proposal.v1",
        base_prompt_hash=ADVISOR_PROMPT_DIGEST,
        evaluation_set_id="eval-portfolio-risk-advisor-v1",
        tools=get_advisor_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_advisor_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Portfolio and Risk Advisor role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(advisor_role_manifest_fields(**overrides))


def build_advisor_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the advisory tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-19",),
        "enabled_roles": (ADVISOR_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_advisor_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


ADVISORY_PORTFOLIO_ID = "portfolio-fx-core"
ADVISORY_MANDATE_ID = "mandate-sandbox"


def advisory_evidence(
    observed_at: str, **overrides: object
) -> dict[
    str,
    dict[str, str],
]:
    """Return the five receiver readings an advisory rests on.

    Every reading carries its own observation instant, because freshness is
    established from what the receiver reported rather than from the model.

    Args:
        observed_at: ISO-8601 observation instant for every reading.
        **overrides: Optional per-tool reading overrides.

    Returns:
        Tool identity to bounded receiver evidence.
    """
    data: dict[str, dict[str, str]] = {
        ALLOCATION_EVIDENCE_TOOL: {
            "observed_at": observed_at,
            "evidence_ref": "analytics.portfolio_allocation_evidence:v3",
            "base_currency": "USD",
            "candidates": "momentum_fx,carry_fx",
        },
        COMMON_MODE_TOOL: {
            "observed_at": observed_at,
            "report_ref": "portfolio.common_mode_exposure:2026-07-29",
            "shared_software_dependencies": "mt5_bridge",
            "breached_accounts": "none",
        },
        CORRELATION_TOOL: {
            "observed_at": observed_at,
            "report_ref": "portfolio.cross_account_correlation:2026-07-29",
            "highest_pair": "momentum_fx/carry_fx",
            "highest_value": "0.62",
        },
        ACCOUNT_STATE_TOOL: {
            "observed_at": observed_at,
            "snapshot_ref": "data.account_state_snapshot:2026-07-29T11:58Z",
            "currency": "USD",
            "headroom_state": "within_limits",
        },
        FIRM_MANDATE_TOOL: {
            "observed_at": observed_at,
            "mandate_id": ADVISORY_MANDATE_ID,
            "mandate_version": "1.0.0",
            "asset_class": "fx",
            "base_currency": "USD",
        },
    }
    for key, value in overrides.items():
        if isinstance(value, dict):
            data[key] = {str(k): str(v) for k, v in value.items()}
    return data


def advisor_model_output(**overrides: object) -> dict[str, str]:
    """Return a well-formed advisory model output.

    Args:
        **overrides: Optional field overrides for output variants.

    Returns:
        The model output an advisory run would parse.
    """
    data: dict[str, str] = {
        "weight:momentum_fx": "greater emphasis than the carry candidate",
        "weight:carry_fx": "reduced emphasis while correlation stays elevated",
        "rationale": (
            "Cross-account correlation between the two candidates is elevated, "
            "so emphasis is shifted toward the candidate whose drawdown is "
            "less dependent on the shared bridge."
        ),
        "constraints_respected": (
            "The view stays inside the fx asset scope.\n"
            "The view stays inside the USD base currency."
        ),
        "limitations": (
            "One correlation reading cannot establish stability under stress.\n"
            "Account headroom was read once and may move within the session."
        ),
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


def advisor_critique_output(**overrides: object) -> dict[str, str]:
    """Return a well-formed risk-critique model output.

    Args:
        **overrides: Optional field overrides for output variants.

    Returns:
        The model output a critique run would parse.
    """
    data: dict[str, str] = {
        f"risk:{kind}": (
            f"The {kind} risk was examined against the supplied evidence and "
            "what it could not establish is stated."
        )
        for kind in sorted(REQUIRED_RISK_KINDS)
    }
    data["unresolved_risks"] = (
        "The tail estimate rests on too few joint moves to be relied upon."
    )
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


TRADER_ROLE_ID = "trader"

TRADER_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(TRADER_PROMPT_PATH.read_text(encoding="utf-8")),
)

PROPOSAL_TASK_ID = "task-trade-proposal-a"
PROPOSAL_STRATEGY_ID = "strat-london-overlap"
PROPOSAL_STRATEGY_VERSION = "1.4.0"
PROPOSAL_INSTRUMENT = "EURUSD"
PROPOSAL_EVIDENCE_REFS = (
    "agentic.technical_evidence_pack:overlap-a",
    "agentic.quantitative_evidence_pack:overlap-a",
)


def trader_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Trader manifest fields.

    The base prompt digest is derived from the real package artefact, so the
    fixture exercises the same integrity chain production uses.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=TRADER_ROLE_ID,
        owning_feature="FEAT-AGT-20",
        department="strategy_desk",
        agent_package="agents/strategy_desk/trader",
        description="Turns a supported thesis into an evaluable proposal.",
        objective="State the view, its horizon, and what would invalidate it.",
        expertise_boundary="Sizes nothing, prices nothing, routes nothing.",
        input_schema_id="agentic.trade_proposal_request.v1",
        output_schema_id="agentic.trade_proposal.v1",
        base_prompt_hash=TRADER_PROMPT_DIGEST,
        evaluation_set_id="eval-trader-v1",
        tools=(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_trader_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Trader role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(trader_role_manifest_fields(**overrides))


def build_trader_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate enabling the trader.

    The trader's manifest registers no tool: it composes from a thesis it was
    handed and submits through the receiver's own intake, so there is nothing
    for it to read through the governed tool path. The mandate keeps its
    firm-wide tool scopes, which the trader is simply not eligible for.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-20",),
        "enabled_roles": (TRADER_ROLE_ID,),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


def build_proposable_thesis(**overrides: object) -> StrategyThesis:
    """Build a real `FEAT-AGT-13` thesis a proposal may rest on.

    Args:
        **overrides: Optional field overrides for thesis variants.

    Returns:
        A validated immutable strategy thesis.
    """
    data: dict[str, object] = {
        "thesis_id": "thesis-london-overlap",
        "task_id": PROPOSAL_TASK_ID,
        "title": "Session-overlap momentum continuation",
        "summary": "Momentum formed in London may continue into the overlap.",
        "stance": "supported",
        "hypothesis_ids": ("hypothesis-overlap-a",),
        "signals": {"momentum": "Sign and magnitude of the London-session move."},
        "intended_behaviour": {
            "momentum": "Participate while the overlap trend persists.",
        },
        "supporting_evidence": PROPOSAL_EVIDENCE_REFS,
        "retained_conflicts": (),
        "assumptions": ("Session boundaries are stable.",),
        "uncertainty": "One venue, one instrument, one year of observations.",
        "next_test": "Evaluate the overlap relationship on a held-out year of data.",
    }
    data.update(overrides)
    return build_strategy_thesis(data)


def trader_model_output(**overrides: object) -> dict[str, str]:
    """Return a well-formed trader model output.

    Args:
        **overrides: Optional field overrides for output variants.

    Returns:
        The model output a proposal run would parse.
    """
    data: dict[str, str] = {
        "rationale": (
            "The thesis holds that momentum formed in the London session "
            "continues into the overlap, and the supplied evidence covers the "
            "overlap window on this instrument."
        ),
        "invalidation": (
            "The overlap move reverses the London-session direction on a "
            "majority of sessions in the horizon.\n"
            "The London-session move fails to exceed the noise band the "
            "evidence established."
        ),
        "uncertainty": (
            "The evidence covers one venue and one year and says nothing about "
            "behaviour across a policy-driven regime change."
        ),
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


def receiver_result(**overrides: object) -> dict[str, object]:
    """Return a well-formed Strategy proposal-evaluation result.

    Args:
        **overrides: Optional field overrides for result variants.

    Returns:
        The receiver fields a receipt would be built from.
    """
    data: dict[str, object] = {
        "evaluation_request_id": "proposal-eval-" + ("a" * 64),
        "status": "accepted_for_evaluation",
        "reason_codes": (),
        "signals_evaluated": 1,
        "audit_event_ref": "strategy.audit:proposal-a",
    }
    data.update(overrides)
    return data


FUNDAMENTAL_ROLE_ID = "fundamental_analyst"
SENTIMENT_ROLE_ID = "sentiment_analyst"

FUNDAMENTAL_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(FUNDAMENTAL_PROMPT_PATH.read_text(encoding="utf-8")),
)
SENTIMENT_PROMPT_DIGEST = canonical_digest(
    normalize_prompt_text(SENTIMENT_PROMPT_PATH.read_text(encoding="utf-8")),
)

INTELLIGENCE_TASK_ID = "task-intelligence-a"
INTELLIGENCE_INSTRUMENT = "EURUSD"
INTELLIGENCE_DECISION_TIME = "2026-07-29T11:00:00+00:00"


def fundamental_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Fundamental Analyst manifest fields.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=FUNDAMENTAL_ROLE_ID,
        owning_feature="FEAT-AGT-09",
        department="market_intelligence",
        agent_package="agents/market_intelligence/fundamental_analyst",
        description="Reads point-in-time filings, transcripts, and macro releases.",
        objective="State what the evidence supports and what would falsify it.",
        expertise_boundary="Fetches nothing, computes nothing, recommends nothing.",
        input_schema_id="agentic.fundamental_request.v1",
        output_schema_id="agentic.fundamental_evidence_pack.v1",
        base_prompt_hash=FUNDAMENTAL_PROMPT_DIGEST,
        evaluation_set_id="eval-fundamental-analyst-v1",
        tools=get_fundamental_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_fundamental_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Fundamental Analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(fundamental_role_manifest_fields(**overrides))


def build_fundamental_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the fundamental tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-09",),
        "enabled_roles": (FUNDAMENTAL_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_fundamental_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


def sentiment_role_manifest_fields(**overrides: object) -> dict[str, object]:
    """Return complete Sentiment Analyst manifest fields.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        Complete manifest constructor data.
    """
    data = manifest_fields(
        role_id=SENTIMENT_ROLE_ID,
        owning_feature="FEAT-AGT-10",
        department="market_intelligence",
        agent_package="agents/market_intelligence/sentiment_analyst",
        description="Reads measured point-in-time news and social evidence.",
        objective="Report what was measured, separately from what it might mean.",
        expertise_boundary="Measures nothing, fetches nothing, recommends nothing.",
        input_schema_id="agentic.sentiment_request.v1",
        output_schema_id="agentic.sentiment_evidence_pack.v1",
        base_prompt_hash=SENTIMENT_PROMPT_DIGEST,
        evaluation_set_id="eval-sentiment-analyst-v1",
        tools=get_sentiment_tool_names(),
        permission_classes=("read_evidence",),
    )
    data.update(overrides)
    return data


def build_sentiment_role_manifest(**overrides: object) -> RoleManifest:
    """Build the validated Sentiment Analyst role manifest.

    Args:
        **overrides: Optional field overrides for manifest variants.

    Returns:
        A validated manifest with derived integrity digests.
    """
    return build_role_manifest(sentiment_role_manifest_fields(**overrides))


def build_sentiment_mandate(**overrides: object) -> FirmMandate:
    """Build a sandbox mandate registering the sentiment tools.

    Args:
        **overrides: Optional field overrides for mandate variants.

    Returns:
        A validated firm mandate with a derived content digest.
    """
    data: dict[str, object] = {
        "enabled_features": ("FEAT-AGT-10",),
        "enabled_roles": (SENTIMENT_ROLE_ID,),
        "tool_scopes": dict.fromkeys(get_sentiment_tool_names(), "read_evidence"),
    }
    data.update(overrides)
    return build_sandbox_mandate(**data)


def fundamental_projection(**overrides: object) -> dict[str, str]:
    """Return a well-formed Research fundamental projection.

    The shape mirrors `research.project_intelligence_evidence` for a
    `FundamentalSourceEvidence`, flattened to bounded strings as the governed
    tool boundary carries it.

    Args:
        **overrides: Optional field overrides for projection variants.

    Returns:
        Bounded projection fields.
    """
    data: dict[str, str] = {
        "schema_id": "research.fundamental_source_evidence.v1",
        "asset_scope": INTELLIGENCE_INSTRUMENT,
        "document_references": (
            "research.source:ecb-statement-2026-07-24,"
            "research.source:fed-minutes-2026-07-18,"
            "research.source:eurostat-hicp-2026-07-17"
        ),
        "source_kinds": "macro,statement",
        "coverage": "macro=2,statement=1",
        "observed_from": "2026-07-17T00:00:00+00:00",
        "available_by": "2026-07-29T09:00:00+00:00",
        "canonical_hash": "a" * 64,
        "advisory_only": "True",
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


def sentiment_projection(**overrides: object) -> dict[str, str]:
    """Return a well-formed Research sentiment projection.

    Args:
        **overrides: Optional field overrides for projection variants.

    Returns:
        Bounded projection fields.
    """
    data: dict[str, str] = {
        "schema_id": "research.sentiment_source_evidence.v1",
        "asset_scope": INTELLIGENCE_INSTRUMENT,
        "document_references": (
            "research.source:wire-eur-2026-07-29a,"
            "research.source:wire-eur-2026-07-29b,"
            "research.source:social-eur-2026-07-29c"
        ),
        "polarity": (
            "research.source:wire-eur-2026-07-29a=0.2,"
            "research.source:wire-eur-2026-07-29b=-0.1,"
            "research.source:social-eur-2026-07-29c=none"
        ),
        "source_coverage": "news=2,social=1",
        "trust_evidence": (
            "research.source:wire-eur-2026-07-29a=trusted,"
            "research.source:social-eur-2026-07-29c=unverified"
        ),
        "manipulation_evidence": "research.source:social-eur-2026-07-29c=coordinated",
        "missing_measurements": "research.source:social-eur-2026-07-29c",
        "disagreement": "true",
        "available_by": "2026-07-29T10:30:00+00:00",
        "canonical_hash": "b" * 64,
        "advisory_only": "True",
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


def fundamental_model_output(**overrides: object) -> dict[str, str]:
    """Return a well-formed fundamental model output.

    Args:
        **overrides: Optional field overrides for output variants.

    Returns:
        The model output a fundamental run would parse.
    """
    data: dict[str, str] = {
        "claim:policy_divergence": (
            "The supplied statements describe a widening policy-rate gap "
            "between the two currency blocs over the observed window."
        ),
        "assumption:policy_divergence": (
            "The statements are assumed to reflect the committees' settled "
            "positions rather than provisional drafts."
        ),
        "horizon:policy_divergence": (
            "Asserted over the six weeks to the next scheduled meeting of "
            "either committee."
        ),
        "falsifier:policy_divergence": (
            "Either committee publishes a statement reversing the direction "
            "described, or an unscheduled decision moves rates the other way."
        ),
        "uncertainty": (
            "The evidence covers three macro releases and no issuer filings, "
            "and says nothing about how the gap transmits to spot pricing."
        ),
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data


def sentiment_model_output(**overrides: object) -> dict[str, str]:
    """Return a well-formed sentiment model output.

    Args:
        **overrides: Optional field overrides for output variants.

    Returns:
        The model output a sentiment run would parse.
    """
    data: dict[str, str] = {
        "event:research.source:wire-eur-2026-07-29a": "policy_statement",
        "event:research.source:wire-eur-2026-07-29b": "data_release",
        "unsupported_narrative": (
            "The two wire items frame the same release differently, which the "
            "lexicon does not measure and which may be nothing."
        ),
        "uncertainty": (
            "One of three documents could not be measured, and the two that "
            "were disagree in sign."
        ),
    }
    data.update({str(key): str(value) for key, value in overrides.items()})
    return data
