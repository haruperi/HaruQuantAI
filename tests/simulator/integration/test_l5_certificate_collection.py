"""Offline safety tests for the genuine L5 certificate collector."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.simulator import compare_parity_evidence, get_parity_envelope
from pydantic import SecretStr

from tests.simulator.integration.l5_certificate_collection import (
    _evidence,
    _has_sensitive_key,
    _items,
    _required_secret_text,
    _strip_collection_only,
    build_application_identity,
    build_authority_watermark,
    build_certificate_manifest,
    build_collection_command,
    build_collector_provider_settings,
    build_history_windows,
    build_mt5_credential_mapping,
    collect_complete_authority_history,
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
        observed_transaction_count=0,
    )
    with pytest.raises(RuntimeError, match="reconcile"):
        validate_authority_interval(
            initial=state,
            final={**state, "orders": [{"order_id": "own-order"}]},
            created_order_id="own-order",
            observed_order_ids={"own-order"},
            observed_deal_count=0,
            observed_transaction_count=0,
        )
    with pytest.raises(RuntimeError, match="foreign/manual"):
        validate_authority_interval(
            initial=state,
            final=state,
            created_order_id="own-order",
            observed_order_ids={"own-order", "foreign-order"},
            observed_deal_count=0,
            observed_transaction_count=0,
        )
    with pytest.raises(RuntimeError, match="foreign/manual"):
        validate_authority_interval(
            initial=state,
            final=state,
            created_order_id="own-order",
            observed_order_ids={"own-order"},
            observed_deal_count=0,
            observed_transaction_count=1,
        )


def test_application_identity_binds_source_and_config_but_not_docs(
    tmp_path: Path,
) -> None:
    """Runtime identity changes for source bytes, not publication prose."""
    app = tmp_path / "app"
    app.mkdir()
    source = app / "runtime.py"
    source.write_text('VALUE = "first"\n', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (tmp_path / "uv.lock").write_text("fixture-lock\n", encoding="utf-8")
    collector = tmp_path / "tests" / "simulator" / "integration"
    collector.mkdir(parents=True)
    (collector / "l5_certificate_collection.py").write_text(
        'COLLECTOR_VERSION = "fixture"\n', encoding="utf-8"
    )
    first = build_application_identity(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("publication only\n", encoding="utf-8")
    assert build_application_identity(tmp_path) == first
    source.write_text('VALUE = "second"\n', encoding="utf-8")
    assert build_application_identity(tmp_path) != first


def test_authority_watermark_covers_all_histories_without_raw_ids() -> None:
    """Orders, deals, and non-trade transactions bind their latest authority."""
    earlier = datetime(2026, 8, 15, tzinfo=UTC)
    later = earlier + timedelta(seconds=1)
    watermark = build_authority_watermark(
        orders=(
            SimpleNamespace(order_id="order-1", provider_timestamp=earlier),
            SimpleNamespace(order_id="order-2", provider_timestamp=later),
        ),
        deals=(SimpleNamespace(deal_id="deal-1", provider_timestamp=earlier),),
        transactions=(
            SimpleNamespace(transaction_id="balance-1", provider_timestamp=earlier),
        ),
    )
    assert watermark["orders"]["count"] == 2  # type: ignore[index]
    assert watermark["orders"]["latest"]["provider_timestamp"] == (  # type: ignore[index]
        later.isoformat()
    )
    assert "order-2" not in json.dumps(watermark, sort_keys=True)


def test_truncated_authority_history_fails_closed() -> None:
    """A page that cannot prove complete history is never a watermark input."""
    response = SimpleNamespace(
        status="success", data=SimpleNamespace(items=(), truncated=True)
    )
    with pytest.raises(RuntimeError, match="truncated"):
        _items(response)


def test_history_windows_cover_the_exact_interval_without_overlap() -> None:
    """Calendar windows cover every instant exactly once."""
    start = datetime(2024, 6, 1, tzinfo=UTC)
    end = datetime(2026, 8, 16, tzinfo=UTC)
    windows = build_history_windows(start, end)
    assert windows[0][0] == start
    assert windows[-1][1] == end
    assert all(
        right_start == left_end + timedelta(microseconds=1)
        for (_, left_end), (right_start, _) in pairwise(windows)
    )


def test_complete_authority_history_aggregates_bounded_windows() -> None:
    """Every complete page contributes to the pre-mutation watermark input."""
    calls: list[tuple[datetime, datetime, int]] = []
    progress: list[tuple[str, datetime, datetime, str]] = []

    async def reader(start: datetime, end: datetime, limit: int) -> object:
        calls.append((start, end, limit))
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(items=(start.year,), truncated=False),
        )

    values = asyncio.run(
        collect_complete_authority_history(
            kind="orders",
            start=datetime(2024, 6, 1, tzinfo=UTC),
            end=datetime(2026, 8, 16, tzinfo=UTC),
            reader=reader,
            progress=lambda *event: progress.append(event),
        )
    )
    assert values == (2024, 2025, 2026)
    assert len(calls) == 3
    assert all(call[2] == 1_000 for call in calls)
    assert [event[3] for event in progress] == [
        "started",
        "completed",
        "started",
        "completed",
        "started",
        "completed",
    ]


def test_truncated_history_windows_split_until_complete() -> None:
    """A truncated provider page is subdivided without dropping an instant."""
    calls: list[tuple[datetime, datetime]] = []

    async def reader(start: datetime, end: datetime, limit: int) -> object:
        del limit
        calls.append((start, end))
        if len(calls) == 1:
            return SimpleNamespace(
                status="success",
                data=SimpleNamespace(items=(), truncated=True),
            )
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(items=((start, end),), truncated=False),
        )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(seconds=4)
    values = asyncio.run(
        collect_complete_authority_history(
            kind="deals",
            start=start,
            end=end,
            reader=reader,
            progress=lambda *_: None,
        )
    )
    assert len(values) == 2
    assert values[0][0] == start
    assert values[1][1] == end
    assert values[1][0] == values[0][1] + timedelta(microseconds=1)


def test_minimum_truncated_history_window_fails_closed() -> None:
    """Completeness uncertainty at the minimum interval blocks collection."""

    async def reader(start: datetime, end: datetime, limit: int) -> object:
        del start, end, limit
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(items=(), truncated=True),
        )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(RuntimeError, match="minimum window"):
        asyncio.run(
            collect_complete_authority_history(
                kind="transactions",
                start=start,
                end=start + timedelta(seconds=1),
                reader=reader,
                progress=lambda *_: None,
            )
        )


def test_history_progress_exposes_only_scope_and_time(capsys) -> None:
    """Default progress output contains no provider authority identifier."""

    async def reader(start: datetime, end: datetime, limit: int) -> object:
        del start, end, limit
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(
                items=(SimpleNamespace(order_id="private-order"),),
                truncated=False,
            ),
        )

    start = datetime(2026, 1, 1, tzinfo=UTC)
    asyncio.run(
        collect_complete_authority_history(
            kind="orders",
            start=start,
            end=start + timedelta(seconds=2),
            reader=reader,
        )
    )
    output = capsys.readouterr().out
    assert "certificate_authority_history" in output
    assert "private-order" not in output


def test_collection_command_is_relative_and_reproducible() -> None:
    """Command evidence contains no workstation-specific absolute path."""
    relative = Path("artifacts/sim_live_parity/mt5-operational/v2/cert-1")
    command = build_collection_command(
        certificate_id="cert-1", symbol="BTCUSD", output=relative
    )
    assert command.endswith(f"--output {relative.as_posix()}")
    with pytest.raises(RuntimeError, match="repository-relative"):
        build_collection_command(
            certificate_id="cert-1",
            symbol="BTCUSD",
            output=Path("C:/private/workspace/cert-1"),
        )


def test_bundle_writer_is_deterministic_and_secret_free(tmp_path: Path) -> None:
    """The collector writes the exact validated bundle from bounded evidence."""
    left, right = paired_evidence()
    bundle = tmp_path / "bundle"
    environment = {
        "environment": "dev",
        "provider": "mt5",
        "route": "demo",
        "provider_build": "offline-fixture",
        "server_digest": "a" * 64,
        "subject_digest": "b" * 64,
        "secret_free": True,
    }
    interval_end = datetime.fromisoformat(str(left["evaluation_time"]))
    manifest = build_certificate_manifest(
        certificate_id="offline-collector-fixture",
        symbol="EURUSD",
        specification={"provider_symbol": "EURUSD", "revision": "fixture-v1"},
        interval_start=interval_end - timedelta(seconds=3),
        interval_end=interval_end,
        left=left,
        right=right,
        environment=environment,
        application_build={
            "version": "2.2.11",
            "source_file_count": 3,
            "source_config_digest": "c" * 64,
        },
        provider_build="offline-fixture",
        authority_watermark={
            "orders": {"count": 0, "latest": None},
            "deals": {"count": 0, "latest": None},
            "transactions": {"count": 0, "latest": None},
        },
        account_modes={
            "trade_mode": "demo",
            "margin_mode": "netting",
            "margin_so_mode": "percent",
        },
        issued_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    manifest["test_fixture_only"] = True
    write_certificate_bundle(
        bundle,
        manifest=manifest,
        left=left,
        right=right,
        environment=environment,
        command=build_collection_command(
            certificate_id="offline-collector-fixture",
            symbol="EURUSD",
            output=Path(
                "artifacts/sim_live_parity/mt5-operational/v2/offline-collector-fixture"
            ),
        ),
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
