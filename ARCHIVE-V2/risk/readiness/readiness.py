"""Phase 5 entry and delivery readiness validation.

This module validates dependency importable status, side-effect safety,
risk mode mapping matrix, and delivery plan constraints (such as synthetic
data only, deterministic seeds, and validation of paths) prior to execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.services.risk.models.contracts import RiskContract
from app.utils.logger import logger
from pydantic import Field, model_validator

if TYPE_CHECKING:
    from app.services.risk.validations import ValidationResult


class DependencyStatus(RiskContract):
    """Tracking structure for a required software dependency."""

    file_path: str = Field(..., description="File path of the dependency.")
    implemented: bool = Field(..., description="Whether the file is implemented.")
    importable: bool = Field(..., description="Whether the file can be imported.")
    side_effect_safe: bool = Field(
        ...,
        description=(
            "Whether importing the file triggers side-effects (should be True)."
        ),
    )
    covered_by_tests: bool = Field(
        ..., description="Whether the file is covered by tests."
    )


class ReadinessAssessment(RiskContract):
    """The outcome of validating all dependency contracts."""

    ready: bool = Field(..., description="Overall readiness status.")
    dependencies_checked: dict[str, DependencyStatus] = Field(
        default_factory=dict, description="Mapped status of checked dependencies."
    )
    failure_reasons: list[str] = Field(
        default_factory=list, description="Reason descriptions if not ready."
    )


class RiskModeMatrix(RiskContract):
    """Matrix defining covered modes and their policy profile mappings."""

    covered_modes: list[str] = Field(
        ..., description="List of environment/trading modes covered."
    )
    policies_mapped: dict[str, str] = Field(
        default_factory=dict, description="Mapping of mode to policy profile name."
    )

    @model_validator(mode="after")
    def validate_mode_coverage(self) -> RiskModeMatrix:
        """Verify that all required safety/operational modes are present."""
        required_modes = {
            "offline",
            "simulation",
            "paper",
            "shadow",
            "read-only live",
            "micro-live",
            "full-live",
        }
        missing = required_modes - set(self.covered_modes)
        if missing:
            msg = f"Missing required safety modes in matrix: {sorted(missing)}"
            raise ValueError(msg)
        return self


class ReadinessDeliveryPlan(RiskContract):
    """Delivery plan validation requirements."""

    traceability_matrix_present: bool = Field(
        ..., description="Whether requirements traceability mapping is present."
    )
    synthetic_fixtures_only: bool = Field(
        ...,
        description="Enforces that only synthetic account and market data are used.",
    )
    deterministic_seeds: dict[str, int] = Field(
        ..., description="Seeds for stochastic simulations/tests."
    )
    benchmark_dataset_shapes: dict[str, tuple[int, ...]] = Field(
        ..., description="Dataset shape sizes for performance validation."
    )
    redaction_rules_defined: bool = Field(
        ...,
        description="Whether credential/private data logging rules are defined.",
    )
    tool_classifications: dict[str, str] = Field(
        ..., description="Classification of each tool function."
    )
    audit_failure_policy: str = Field(
        ..., description="Behavior when audit persistent storage fails."
    )


class DryRunReport(RiskContract):
    """Report outlining planned workspace edits and boundaries."""

    files_to_read: list[str] = Field(..., description="List of files to read.")
    files_to_change: list[str] = Field(
        ..., description="List of files to modify or create."
    )
    commands_planned: list[str] = Field(..., description="List of commands to execute.")
    scope_boundaries: list[str] = Field(..., description="List of active scopes.")
    blockers: list[str] = Field(..., description="Identified execution blockers.")
    rollback_points: list[str] = Field(
        ..., description="Git rollback boundary markers."
    )


class RiskReadinessManifest(RiskContract):
    """Immutable pre-runtime manifest validating deployment readiness."""

    dependencies: dict[str, DependencyStatus] = Field(
        ..., description="Status map of checked dependencies."
    )
    mode_matrix: RiskModeMatrix = Field(..., description="Checked risk mode matrix.")
    delivery_plan: ReadinessDeliveryPlan = Field(
        ..., description="Checked delivery plan details."
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Manifest creation timestamp.",
    )
    author: str = Field(..., description="Operator generating the manifest.")

    @model_validator(mode="after")
    def validate_readiness_manifest(self) -> RiskReadinessManifest:
        """Validate all subsystems inside the manifest on construction."""
        # 1. Validate dependencies ready
        dep_assessment = validate_phase_dependencies(self.dependencies)
        if not dep_assessment.ready:
            msg = f"Dependency checks failed: {dep_assessment.failure_reasons}"
            raise ValueError(msg)

        # 2. Validate mode matrix
        mode_res = validate_risk_mode_matrix(self.mode_matrix)
        if not mode_res["valid"]:
            raise ValueError(mode_res["message"])

        # 3. Validate delivery plan
        plan_res = validate_delivery_plan(self.delivery_plan)
        if not plan_res["valid"]:
            raise ValueError(plan_res["message"])

        return self


def validate_phase_dependencies(
    dependencies: Mapping[str, DependencyStatus],
) -> ReadinessAssessment:
    """Validate that all target dependencies are implemented and covered.

    Args:
        dependencies: Map of dependency keys to statuses.

    Returns:
        ReadinessAssessment: Summary of dependency readiness.
    """
    logger.info("Starting validation of phase dependencies.")
    reasons: list[str] = []
    checked: dict[str, DependencyStatus] = {}

    for dep_name, status in dependencies.items():
        checked[dep_name] = status
        if not status.implemented:
            reasons.append(f"Dependency '{dep_name}' is not implemented.")
        if not status.importable:
            reasons.append(f"Dependency '{dep_name}' is not importable.")
        if not status.side_effect_safe:
            reasons.append(f"Dependency '{dep_name}' imports with side-effects.")
        if not status.covered_by_tests:
            reasons.append(f"Dependency '{dep_name}' lacks unit test coverage.")

    ready = len(reasons) == 0
    if ready:
        logger.info("All phase dependencies verified successfully.")
    else:
        logger.warning(f"Dependency checks failed with {len(reasons)} reasons.")

    return ReadinessAssessment(
        ready=ready,
        dependencies_checked=checked,
        failure_reasons=reasons,
    )


def validate_risk_mode_matrix(matrix: RiskModeMatrix) -> ValidationResult:
    """Validate that the risk mode matrix is valid and complete.

    Args:
        matrix: The matrix config model.

    Returns:
        ValidationResult: The validation outcome dictionary.
    """
    logger.info("Validating risk mode matrix.")
    required_modes = {
        "offline",
        "simulation",
        "paper",
        "shadow",
        "read-only live",
        "micro-live",
        "full-live",
    }
    missing = required_modes - set(matrix.covered_modes)
    if missing:
        msg = f"Missing required safety modes in matrix: {sorted(missing)}"
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "MISSING_EVIDENCE",
            "details": {"missing_modes": list(missing)},
        }

    logger.info("Risk mode matrix validation passed.")
    return {
        "valid": True,
        "message": "Risk mode matrix is valid.",
        "code": "OK",
        "details": {},
    }


def validate_delivery_plan(plan: ReadinessDeliveryPlan) -> ValidationResult:
    """Validate structural constraints of the delivery plan.

    Args:
        plan: The delivery plan details.

    Returns:
        ValidationResult: The validation outcome dictionary.
    """
    logger.info("Validating readiness delivery plan.")
    errors: list[tuple[str, str]] = []

    if not plan.traceability_matrix_present:
        errors.append(("Traceability matrix is missing.", "MISSING_EVIDENCE"))
    if not plan.synthetic_fixtures_only:
        errors.append(
            (
                "Delivery plan allows unsafe live production data in test fixtures.",
                "POLICY_BLOCKED",
            )
        )
    if not plan.redaction_rules_defined:
        errors.append(("Redaction rules not defined.", "MISSING_EVIDENCE"))
    if plan.audit_failure_policy.lower() != "fail-closed":
        errors.append(("Audit failure policy must be 'fail-closed'.", "POLICY_BLOCKED"))
    if not plan.deterministic_seeds:
        errors.append(
            ("Deterministic random seeds are not defined.", "MISSING_EVIDENCE")
        )
    if not plan.benchmark_dataset_shapes:
        errors.append(("Benchmark dataset shapes are not defined.", "MISSING_EVIDENCE"))

    if errors:
        msg, code = errors[0]
        return {
            "valid": False,
            "message": msg,
            "code": code,
            "details": {},
        }

    logger.info("Readiness delivery plan validation passed.")
    return {
        "valid": True,
        "message": "Delivery plan is valid.",
        "code": "OK",
        "details": {},
    }


def build_readiness_dry_run(manifest: RiskReadinessManifest) -> DryRunReport:
    """Build a dry run report based on the readiness manifest content.

    Args:
        manifest: Validated readiness manifest.

    Returns:
        DryRunReport: The generated dry-run report.
    """
    logger.info("Building readiness dry run report.")
    files_read = []
    for status in manifest.dependencies.values():
        files_read.append(status.file_path)

    report = DryRunReport(
        files_to_read=sorted(files_read),
        files_to_change=[
            "app/services/risk/readiness/readiness.py",
            "app/services/risk/readiness/__init__.py",
        ],
        commands_planned=[
            "uv run pytest tests/risk/unit/test_readiness.py",
            "uv run ruff check .",
            "uv run mypy .",
        ],
        scope_boundaries=["offline", "simulation", "paper"],
        blockers=[],
        rollback_points=["git checkout -- app/services/risk/"],
    )
    logger.info("Readiness dry run report compiled successfully.")
    return report
