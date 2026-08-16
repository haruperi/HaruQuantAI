"""Offline safety tests for the genuine L5 certificate collector."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.simulator import compare_parity_evidence, get_parity_envelope
from pydantic import SecretStr

from tests.simulator.integration.l5_certificate_collection import (
    _evidence,
    _has_sensitive_key,
    _required_secret_text,
    _strip_collection_only,
    build_collector_provider_settings,
    build_mt5_credential_mapping,
    require_terminal_executable,
    validate_authority_interval,
    validate_collection_output,
    validate_collection_preflight,
    validate_l5_certificate_bundle,
    write_certificate_bundle,
)
from tests.simulator.integration.test_parity_relationships import paired_evidence


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (
            {
                "execute_demo": False,
                "environment": "dev",
                "route": "demo",
                "symbol": "BTCUSD",
            },
            "--execute-demo",
        ),
        (
            {
                "execute_demo": True,
                "environment": "prod",
                "route": "demo",
                "symbol": "BTCUSD",
            },
            "dev/demo",
        ),
        (
            {
                "execute_demo": True,
                "environment": "dev",
                "route": "live",
                "symbol": "BTCUSD",
            },
            "dev/demo",
        ),
        (
            {
                "execute_demo": True,
                "environment": "dev",
                "route": "demo",
                "symbol": "EURUSD",
            },
            "BTCUSD",
        ),
    ],
)
def test_collection_preflight_fails_closed(
    values: dict[str, object], message: str
) -> None:
    """Missing explicit authorization or scope identity blocks collection."""
    with pytest.raises(RuntimeError, match=message):
        validate_collection_preflight(**values)  # type: ignore[arg-type]


def test_sensitive_key_detection_is_recursive() -> None:
    """Credential-shaped nested fields are rejected without inspecting values."""
    assert (
        _has_sensitive_key(
            {"nested": [{"password": "redacted"}]}  # pragma: allowlist secret
        )
        is True
    )
    assert _has_sensitive_key({"server_digest": "a" * 64, "secret_free": True}) is False


def test_secret_login_is_unwrapped_only_for_in_memory_account_reference() -> None:
    """A masked SecretStr representation is never used as the account reference."""
    value = SecretStr("demo-subject")  # pragma: allowlist secret
    assert str(value) != "demo-subject"  # pragma: allowlist secret
    assert (
        _required_secret_text(value, "login") == "demo-subject"
    )  # pragma: allowlist secret
    with pytest.raises(TypeError, match="malformed"):
        _required_secret_text("masked", "login")


def test_terminal_must_be_explicitly_configured_before_adapter_creation(
    tmp_path: Path,
) -> None:
    """Missing or nonexistent terminal configuration fails before provider use."""
    with pytest.raises(RuntimeError, match="not configured"):
        require_terminal_executable(None)
    with pytest.raises(RuntimeError, match="does not exist"):
        require_terminal_executable(tmp_path / "missing.exe")
    terminal = tmp_path / "terminal64.exe"
    terminal.touch()
    assert require_terminal_executable(terminal) == terminal.resolve()
    redacted_terminal = SecretStr(str(terminal))
    assert require_terminal_executable(redacted_terminal) == terminal.resolve()


def test_provider_settings_are_composed_from_database_system_values(
    tmp_path: Path,
) -> None:
    """Collector composition uses explicit database settings and demo route."""
    terminal = tmp_path / "terminal64.exe"
    terminal.touch()
    settings = build_collector_provider_settings(
        {"MT5_ENABLED": "true", "MT5_TERMINAL_PATH": str(terminal)}
    )
    assert settings.mt5_enabled is True
    assert settings.mt5_environment == "demo"
    assert require_terminal_executable(settings.mt5_terminal_path) == terminal.resolve()
    with pytest.raises(RuntimeError, match="not enabled"):
        build_collector_provider_settings(
            {"MT5_ENABLED": "false", "MT5_TERMINAL_PATH": str(terminal)}
        )
    with pytest.raises(RuntimeError, match="absent"):
        build_collector_provider_settings({"MT5_ENABLED": "true"})


def test_broker_credential_mapping_preserves_every_secret_wrapper() -> None:
    """Broker configuration receives only named non-empty SecretStr values."""
    slot = {
        "login": SecretStr("subject"),  # pragma: allowlist secret
        "password": SecretStr("credential"),  # pragma: allowlist secret
        "server": SecretStr("provider"),  # pragma: allowlist secret
    }
    terminal = SecretStr("terminal.exe")  # pragma: allowlist secret
    credentials = build_mt5_credential_mapping(slot, terminal)
    assert set(credentials) == {"login", "password", "server", "terminal_path"}
    assert all(isinstance(value, SecretStr) for value in credentials.values())
    assert credentials["terminal_path"] is terminal
    with pytest.raises(RuntimeError, match="absent or malformed"):
        build_mt5_credential_mapping({**slot, "password": None}, terminal)


def test_collection_output_is_confined_to_exact_artifact_identity(
    tmp_path: Path,
) -> None:
    """Generated output cannot escape its root or use a mismatched ID."""
    expected = Path("artifacts/sim_live_parity/mt5-operational/v2/cert-1")
    assert (
        validate_collection_output(expected, "cert-1", workspace_root=tmp_path)
        == (tmp_path / expected).resolve()
    )
    with pytest.raises(RuntimeError, match="artifact root"):
        validate_collection_output(
            Path("outside/cert-1"), "cert-1", workspace_root=tmp_path
        )


def test_authority_interval_requires_cleanup_and_no_foreign_activity() -> None:
    """Incomplete cleanup or any unowned history fails closed."""
    state = {"account": {"balance": "100"}, "orders": [], "positions": []}
    validate_authority_interval(
        initial=state,
        final=state,
        created_order_id="own-order",
        observed_order_ids={"own-order"},
        observed_deal_count=0,
    )
    with pytest.raises(RuntimeError, match="reconcile"):
        validate_authority_interval(
            initial=state,
            final={**state, "orders": [{"order_id": "own-order"}]},
            created_order_id="own-order",
            observed_order_ids={"own-order"},
            observed_deal_count=0,
        )
    with pytest.raises(RuntimeError, match="foreign/manual"):
        validate_authority_interval(
            initial=state,
            final=state,
            created_order_id="own-order",
            observed_order_ids={"own-order", "foreign-order"},
            observed_deal_count=0,
        )


def test_bundle_writer_is_deterministic_and_secret_free(tmp_path: Path) -> None:
    """The collector writes the exact validated bundle from bounded evidence."""
    envelope = get_parity_envelope("v2")
    applicability = envelope["operational_applicability"]
    scope = envelope["certificate_scope"]
    assert isinstance(applicability, dict)
    assert isinstance(scope, dict)
    left, right = paired_evidence()
    bundle = tmp_path / "bundle"
    write_certificate_bundle(
        bundle,
        manifest={
            "schema_version": "l5-mt5-operational-certificate.v1",
            "certificate_id": "offline-collector-fixture",
            "envelope_version": "v2",
            "evidence_route": applicability["evidence_route"],
            "provider_routes": applicability["provider_routes"],
            "certified_semantics": applicability["certified_semantics"],
            "excluded_empirical_claims": applicability["excluded_empirical_claims"],
            "asset_class": scope["asset_class"],
            "status": "valid",
            "test_fixture_only": True,
        },
        left=left,
        right=right,
        environment={
            "environment": "dev",
            "provider": "mt5",
            "route": "demo",
            "target_build": "offline-fixture",
            "server_digest": "a" * 64,
            "subject_digest": "b" * 64,
            "secret_free": True,
        },
        command="offline collector fixture",
    )
    validate_l5_certificate_bundle(bundle)
    assert len(tuple(bundle.iterdir())) == 9
    for path in bundle.glob("*.json"):
        assert _has_sensitive_key(json.loads(path.read_text(encoding="utf-8"))) is False


def test_bundle_writer_refuses_existing_target(tmp_path: Path) -> None:
    """An existing output directory is never overwritten."""
    bundle = tmp_path / "existing"
    bundle.mkdir()
    with pytest.raises(FileExistsError):
        write_certificate_bundle(
            bundle,
            manifest={},
            left={},
            right={},
            environment={},
            command="offline",
        )


def test_collected_trace_shape_passes_v2_operational_comparison() -> None:
    """Collector-built sim/demo lifecycle evidence satisfies the strict schema."""
    now = datetime(2026, 8, 16, 10, tzinfo=UTC)
    stamps = (now, now + timedelta(seconds=1), now + timedelta(seconds=2))
    identity = {
        "execution_model_hash": "a" * 64,
        "config_hash": "b" * 64,
        "source_lineage_hash": "c" * 64,
        "tick_lineage_hash": "d" * 64,
        "market_evidence_class": "operational_contract_trace",
    }
    common = {
        "symbol": "BTCUSD",
        "client_order_id": "client-1",
        "quantity": Decimal("0.01"),
        "limit_price": Decimal(80000),
        "stamps": stamps,
        "state_hash": "e" * 64,
        "identity": identity,
        "account": {"balance": "10000", "equity": "10000"},
    }
    left = _strip_collection_only(_evidence(route="sim", order_id="sim-1", **common))
    right = _strip_collection_only(_evidence(route="demo", order_id="demo-1", **common))
    result = compare_parity_evidence(left, right, get_parity_envelope("v2"))
    assert result["passed"] is True, result["failures"]
