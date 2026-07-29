"""Shared bounded secret-safe Agentic test fixtures.

Builds a realistic `sandbox` mandate and roster through the public governance
builders, so every consumer exercises the same integrity-digest chain the
registry validates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.agentic import build_firm_mandate, build_role_manifest
from app.agentic.agents.experimentation.experiment_designer.agent import (
    PROMPT_PATH as DESIGNER_PROMPT_PATH,
)
from app.agentic.agents.experimentation.experiment_designer.tools import (
    get_registered_tool_names as get_designer_tool_names,
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
from app.agentic.agents.strategy_desk.strategy_thesis_analyst.agent import (
    PROMPT_PATH as THESIS_PROMPT_PATH,
)
from app.agentic.governance import FirmMandate, RoleManifest
from app.agentic.governance.models import UNIVERSAL_PROHIBITIONS
from app.agentic.governance.registry import normalize_prompt_text
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
