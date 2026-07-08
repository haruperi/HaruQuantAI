"""Unit tests for Risk Governance Phase 5 entry and readiness validation.

Verifies dependency statuses, mode matrix, delivery plan requirements,
dry-run compilation, and manifest construction.
"""

from __future__ import annotations

import pytest
from app.services.risk.readiness import (
    DependencyStatus,
    DryRunReport,
    ReadinessDeliveryPlan,
    RiskModeMatrix,
    RiskReadinessManifest,
    build_readiness_dry_run,
    validate_delivery_plan,
    validate_phase_dependencies,
    validate_risk_mode_matrix,
)
from pydantic import ValidationError


def test_dependency_status_and_validation() -> None:
    """Test verification of required file/module dependencies."""
    # 1. Successful scenario
    deps = {
        "ports": DependencyStatus(
            file_path="app/services/risk/storage/ports.py",
            implemented=True,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        ),
        "in_memory": DependencyStatus(
            file_path="app/services/risk/storage/in_memory.py",
            implemented=True,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        ),
    }

    res = validate_phase_dependencies(deps)
    assert res.ready is True
    assert len(res.failure_reasons) == 0

    # 2. Failure scenarios
    unready_deps = {
        "ports": DependencyStatus(
            file_path="app/services/risk/storage/ports.py",
            implemented=False,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        ),
        "in_memory": DependencyStatus(
            file_path="app/services/risk/storage/in_memory.py",
            implemented=True,
            importable=False,
            side_effect_safe=False,
            covered_by_tests=False,
        ),
    }
    res_fail = validate_phase_dependencies(unready_deps)
    assert res_fail.ready is False
    assert len(res_fail.failure_reasons) == 4
    assert any("not implemented" in r for r in res_fail.failure_reasons)
    assert any("not importable" in r for r in res_fail.failure_reasons)
    assert any("side-effects" in r for r in res_fail.failure_reasons)
    assert any("lacks unit test" in r for r in res_fail.failure_reasons)


def test_risk_mode_matrix() -> None:
    """Test validation of trading and safety environments coverage matrix."""
    # 1. Valid matrix
    valid_matrix = RiskModeMatrix(
        covered_modes=[
            "offline",
            "simulation",
            "paper",
            "shadow",
            "read-only live",
            "micro-live",
            "full-live",
        ],
        policies_mapped={
            "offline": "default",
            "simulation": "default",
            "paper": "paper",
            "shadow": "live_conservative",
            "read-only live": "live_conservative",
            "micro-live": "live_conservative",
            "full-live": "live_conservative",
        },
    )
    val_res = validate_risk_mode_matrix(valid_matrix)
    assert val_res["valid"] is True

    # 2. Invalid matrix - missing required modes on construction
    with pytest.raises(ValidationError):
        RiskModeMatrix(
            covered_modes=["offline", "simulation", "paper"],
            policies_mapped={"offline": "default"},
        )


def test_readiness_delivery_plan() -> None:
    """Test validation of safety constraints for the implementation plan."""
    # 1. Valid plan
    valid_plan = ReadinessDeliveryPlan(
        traceability_matrix_present=True,
        synthetic_fixtures_only=True,
        deterministic_seeds={"stress": 42},
        benchmark_dataset_shapes={"var": (100, 10)},
        redaction_rules_defined=True,
        tool_classifications={"validate_phase_dependencies": "helper"},
        audit_failure_policy="fail-closed",
    )
    res = validate_delivery_plan(valid_plan)
    assert res["valid"] is True

    # 2. Missing traceability matrix
    plan_no_trace = valid_plan.model_copy(update={"traceability_matrix_present": False})
    res_no_trace = validate_delivery_plan(plan_no_trace)
    assert res_no_trace["valid"] is False
    assert "Traceability matrix is missing" in res_no_trace["message"]

    # 3. Non-synthetic fixtures allowed
    plan_no_synth = valid_plan.model_copy(update={"synthetic_fixtures_only": False})
    res_no_synth = validate_delivery_plan(plan_no_synth)
    assert res_no_synth["valid"] is False
    assert "allows unsafe live production data" in res_no_synth["message"]

    # 4. Missing redaction rules
    plan_no_redact = valid_plan.model_copy(update={"redaction_rules_defined": False})
    res_no_redact = validate_delivery_plan(plan_no_redact)
    assert res_no_redact["valid"] is False
    assert "Redaction rules not defined" in res_no_redact["message"]

    # 5. Fail-open audit failure policy
    plan_fail_open = valid_plan.model_copy(update={"audit_failure_policy": "fail-open"})
    res_fail_open = validate_delivery_plan(plan_fail_open)
    assert res_fail_open["valid"] is False
    assert "Audit failure policy must be 'fail-closed'" in res_fail_open["message"]

    # 6. Missing deterministic seeds
    plan_no_seeds = valid_plan.model_copy(update={"deterministic_seeds": {}})
    res_no_seeds = validate_delivery_plan(plan_no_seeds)
    assert res_no_seeds["valid"] is False
    assert "Deterministic random seeds are not defined" in res_no_seeds["message"]

    # 7. Missing benchmark dataset shapes
    plan_no_shapes = valid_plan.model_copy(update={"benchmark_dataset_shapes": {}})
    res_no_shapes = validate_delivery_plan(plan_no_shapes)
    assert res_no_shapes["valid"] is False
    assert "Benchmark dataset shapes are not defined" in res_no_shapes["message"]


def test_manifest_construction_and_dry_run() -> None:
    """Test compilation of DryRunReport and validation of ReadinessManifest."""
    deps = {
        "ports": DependencyStatus(
            file_path="app/services/risk/storage/ports.py",
            implemented=True,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        )
    }
    matrix = RiskModeMatrix(
        covered_modes=[
            "offline",
            "simulation",
            "paper",
            "shadow",
            "read-only live",
            "micro-live",
            "full-live",
        ],
        policies_mapped={},
    )
    plan = ReadinessDeliveryPlan(
        traceability_matrix_present=True,
        synthetic_fixtures_only=True,
        deterministic_seeds={"stress": 42},
        benchmark_dataset_shapes={"var": (100, 10)},
        redaction_rules_defined=True,
        tool_classifications={},
        audit_failure_policy="fail-closed",
    )

    # 1. Successful construction
    manifest = RiskReadinessManifest(
        dependencies=deps,
        mode_matrix=matrix,
        delivery_plan=plan,
        author="agentic-builder",
    )
    assert manifest.author == "agentic-builder"

    # 2. Build dry run report
    report = build_readiness_dry_run(manifest)
    assert isinstance(report, DryRunReport)
    assert "app/services/risk/storage/ports.py" in report.files_to_read
    assert len(report.files_to_change) > 0

    # 3. Failed manifest - unready dependencies
    unready_deps = {
        "ports": DependencyStatus(
            file_path="app/services/risk/storage/ports.py",
            implemented=False,
            importable=True,
            side_effect_safe=True,
            covered_by_tests=True,
        )
    }
    with pytest.raises(ValidationError):
        RiskReadinessManifest(
            dependencies=unready_deps,
            mode_matrix=matrix,
            delivery_plan=plan,
            author="agentic-builder",
        )
