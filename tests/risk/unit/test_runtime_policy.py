"""Unit tests for FEAT-RISK-02 runtime policy operations."""

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    data_settings_context,
)
from app.services.risk import (
    build_development_risk_config,
    get_risk_policy,
    register_risk_policy,
    run_risk_migrations,
)
from app.services.risk.config.profiles import RiskConfig
from app.services.risk.config.runtime import _HASH_PATTERN
from app.services.risk.contracts.enums import RiskErrorCode
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.persistence.create import create_policy_version


def _settings(tmp_path: Path) -> object:
    return build_data_settings(
        database_url="sqlite:///test_risk_policy.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=5.0,
        approved_storage_roots=(Path(),),
    )


def test_register_and_get_risk_policy_end_to_end(tmp_path: Path) -> None:
    """Register one RiskConfig and read it back by canonical hash."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        config = cast("RiskConfig", build_development_risk_config())
        effective_at = datetime.now(UTC)
        request_id = generate_id("req")
        correlation_id = generate_id("cor")

        resp_reg = register_risk_policy(
            config,
            effective_at=effective_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        assert resp_reg.status == "success"
        config_hash = unwrap_risk_response(resp_reg, operation="register_risk_policy")
        assert isinstance(config_hash, str)
        assert _HASH_PATTERN.fullmatch(config_hash)

        resp_get = get_risk_policy(config_hash)
        assert resp_get.status == "success"
        reconstructed = unwrap_risk_response(resp_get, operation="get_risk_policy")
        assert reconstructed.profile == config.profile
        assert reconstructed.policy_version == config.policy_version


def test_register_policy_idempotent_replay(tmp_path: Path) -> None:
    """Verify that re-registering an identical configuration succeeds idempotently."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        config = cast("RiskConfig", build_development_risk_config())
        effective_at = datetime.now(UTC)
        request_id = generate_id("req")
        correlation_id = generate_id("cor")

        resp1 = register_risk_policy(
            config,
            effective_at=effective_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        assert resp1.status == "success"
        hash1 = unwrap_risk_response(resp1, operation="register_risk_policy")

        resp2 = register_risk_policy(
            config,
            effective_at=effective_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        assert resp2.status == "success"
        hash2 = unwrap_risk_response(resp2, operation="register_risk_policy")
        assert hash1 == hash2


def test_register_policy_conflict_fails_closed(tmp_path: Path) -> None:
    """Verify that inserting a conflicting payload under an existing hash fails."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        config_hash = "a" * 64
        effective_at = datetime.now(UTC).isoformat()

        create_policy_version(
            config_hash=config_hash,
            policy_version="v1",
            profile="simulation",
            payload_json='{"foo": "bar"}',
            effective_at=effective_at,
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
        )

        with pytest.raises(ValueError, match="Risk policy version identity conflict"):
            create_policy_version(
                config_hash=config_hash,
                policy_version="v1",
                profile="simulation",
                payload_json='{"foo": "baz"}',
                effective_at=effective_at,
                request_id=generate_id("req"),
                correlation_id=generate_id("cor"),
            )


def test_register_policy_naive_timestamp_rejected() -> None:
    """Reject naive non-UTC timestamps."""
    config = cast("RiskConfig", build_development_risk_config())
    naive_dt = datetime(2026, 8, 6, 12, 0, 0)  # noqa: DTZ001

    resp = register_risk_policy(
        config,
        effective_at=naive_dt,
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
    )
    assert resp.status == "error"
    assert resp.error is not None
    assert resp.error.code == RiskErrorCode.VALIDATION_FAILED.value


def test_get_policy_missing_and_invalid_hash(tmp_path: Path) -> None:
    """Return explicit error for invalid hash format or missing policy version."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        resp_bad = get_risk_policy("invalid_hash")
        assert resp_bad.status == "error"
        assert resp_bad.error is not None
        assert resp_bad.error.code == RiskErrorCode.VALIDATION_FAILED.value

        missing_hash = "f" * 64
        resp_missing = get_risk_policy(missing_hash)
        assert resp_missing.status == "error"
        assert resp_missing.error is not None
        assert resp_missing.error.code == RiskErrorCode.MISSING_EVIDENCE.value


def test_get_policy_invalid_hash_log_redacts_caller_input(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Reject and redact credential-like text supplied as a policy hash."""
    hostile_input = "password=plain-text-secret"

    with caplog.at_level("ERROR"):
        response = get_risk_policy(hostile_input)

    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.VALIDATION_FAILED.value
    assert hostile_input not in caplog.text
    assert "plain-text-secret" not in caplog.text
    assert "input_type=str" in caplog.text
    assert f"input_length={len(hostile_input)}" in caplog.text


def test_get_policy_malformed_payload_logs_semantic_error(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify semantic failure log on malformed or tampered policy payload."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        config_hash = "b" * 64
        effective_at = datetime.now(UTC).isoformat()

        create_policy_version(
            config_hash=config_hash,
            policy_version="v1",
            profile="simulation",
            payload_json='{"invalid_json": true}',
            effective_at=effective_at,
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
        )

        with caplog.at_level("WARNING"):
            resp = get_risk_policy(config_hash)
            assert resp.status == "error"
            assert resp.error is not None
            assert resp.error.code == RiskErrorCode.INVALID_RISK_CONFIG.value
            assert f"config_hash={config_hash}" in caplog.text
            assert "invalid_json" not in caplog.text


def test_register_and_get_policy_logging_has_no_secrets(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify trace IDs in registration logs and ensure no secrets are exposed."""
    with data_settings_context(_settings(tmp_path)):
        run_risk_migrations(request_id=generate_id("req"))
        config = cast("RiskConfig", build_development_risk_config())
        effective_at = datetime.now(UTC)
        request_id = generate_id("req")
        correlation_id = generate_id("cor")

        with caplog.at_level("INFO"):
            register_risk_policy(
                config,
                effective_at=effective_at,
                request_id=request_id,
                correlation_id=correlation_id,
            )
            assert f"request_id={request_id}" in caplog.text
            assert f"correlation_id={correlation_id}" in caplog.text
            assert "approval_signing_key_ref" not in caplog.text
            assert "password" not in caplog.text
