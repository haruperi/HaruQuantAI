"""Integration evidence for API approval and idempotency persistence."""

from pathlib import Path

import pytest
from app.services.api import (
    consume_api_approval,
    create_api_approval,
    finalize_api_idempotency_key,
    reserve_api_idempotency_key,
    run_api_migrations,
)
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id


def test_scoped_approval_and_terminal_idempotency_replay(tmp_path: Path) -> None:
    """Consume approval once and replay only an identical terminal request."""
    settings = build_data_settings(
        database_url="sqlite:///api-governance.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    evidence = {"portfolio_id": "portfolio-1", "version": 2}
    with data_settings_context(settings):
        assert run_api_migrations(generate_id("req")).status == "success"
        approval = create_api_approval(
            issuer_id="operator-2",
            subject_id="operator-1",
            scope="portfolio.activate",
            evidence=evidence,
            ttl_seconds=60,
            request_id=generate_id("req"),
        )
        consumed = consume_api_approval(
            approval.approval_id,
            subject_id="operator-1",
            scope="portfolio.activate",
            evidence=evidence,
            request_id=generate_id("req"),
        )
        assert consumed.consumed_at is not None
        with pytest.raises(RuntimeError, match="APPROVAL_INVALID"):
            consume_api_approval(
                approval.approval_id,
                subject_id="operator-1",
                scope="portfolio.activate",
                evidence=evidence,
                request_id=generate_id("req"),
            )
        reservation = reserve_api_idempotency_key(
            principal_id="operator-1",
            method="POST",
            route="/api/v1/portfolio/activations",
            key="idempotency-1",
            request_material=evidence,
            request_id=generate_id("req"),
        )
        assert reservation.state == "reserved"
        finalize_api_idempotency_key(
            principal_id="operator-1",
            method="POST",
            route="/api/v1/portfolio/activations",
            key="idempotency-1",
            response_json='{"status":"success"}',
            status_code=200,
            request_id=generate_id("req"),
        )
        replay = reserve_api_idempotency_key(
            principal_id="operator-1",
            method="POST",
            route="/api/v1/portfolio/activations",
            key="idempotency-1",
            request_material=evidence,
            request_id=generate_id("req"),
        )
        assert replay.state == "replay"
        with pytest.raises(RuntimeError, match="IDEMPOTENCY_CONFLICT"):
            reserve_api_idempotency_key(
                principal_id="operator-1",
                method="POST",
                route="/api/v1/portfolio/activations",
                key="idempotency-1",
                request_material={"portfolio_id": "different"},
                request_id=generate_id("req"),
            )
