"""Integration evidence for durable Risk runtime state."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.services.risk import (
    build_risk_state_store,
    create_allocation_risk_decision,
    execute_risk_state_store_operation,
    get_decision_state,
)
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///risk-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _decision(version: str, predecessor: str | None) -> object:
    """Build one valid active allocation decision.

    Returns:
        Opaque Risk decision.
    """
    now = datetime(2026, 8, 1, tzinfo=UTC)
    return create_allocation_risk_decision(
        decision_id=f"decision-{version}",
        portfolio_id="portfolio-one",
        reviewed_version=version,
        state=get_decision_state("approve"),
        capped_weights={"strategy-one": Decimal("0.5")},
        risk_budget_projection={"max_drawdown": Decimal("0.05")},
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": "evidence-one"},
        issued_at=now,
        expires_at=now + timedelta(days=1),
        active=True,
        predecessor_version=predecessor,
        audit_ref="audit-one",
    )


def test_risk_allocation_state_is_durable_and_guarded(tmp_path: Path) -> None:
    """Allocation activation survives reconstruction and checks predecessors."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.risk.runtime.migrations",
            request_id=request_id,
        )
        store = build_risk_state_store()
        first = _decision("v1", None)
        assert execute_risk_state_store_operation(
            store,
            "save_review_if_absent",
            first,
            timeout_seconds=None,
        )
        assert execute_risk_state_store_operation(
            store,
            "activate_compare_and_swap",
            first,
            expected_predecessor_version=None,
            timeout_seconds=None,
        )
        reconstructed = build_risk_state_store()
        active = execute_risk_state_store_operation(
            reconstructed,
            "get_active",
            "portfolio-one",
            timeout_seconds=None,
        )
        assert active == first
        second = _decision("v2", "v1")
        assert not execute_risk_state_store_operation(
            reconstructed,
            "activate_compare_and_swap",
            second,
            expected_predecessor_version="wrong",
            timeout_seconds=None,
        )
        assert execute_risk_state_store_operation(
            reconstructed,
            "activate_compare_and_swap",
            second,
            expected_predecessor_version="v1",
            timeout_seconds=None,
        )
