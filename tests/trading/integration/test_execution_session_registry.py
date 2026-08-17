"""Integration evidence for the durable execution-session registry."""

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.trading import (
    archive_execution_session,
    complete_simulation_session_configuration,
    create_execution_session,
    get_execution_session_events,
    list_execution_sessions,
    run_trading_migrations,
    set_default_execution_session,
    start_execution_session,
    stop_execution_session,
)
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated registry persistence settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///execution-sessions.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def test_registry_persists_defaults_lifecycle_and_history(tmp_path: Path) -> None:
    """A session survives reconstruction and retains ordered lifecycle evidence."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_trading_migrations(request_id=request_id),
            operation="tests.trading.session_registry.migrate",
            request_id=request_id,
        )
        created = cast(
            "Any",
            create_execution_session(
                principal_id="principal-one",
                environment_id="environment-one",
                name="Long-lived SIM",
                mode="sim",
                provider="simulation",
                request_id=generate_id("req"),
                dataset_ref="dataset-one",
                dataset_revision="revision-one",
                dataset_hash="a" * 64,
                sim_initial_balance="100000",
                sim_leverage=100,
                sim_account_currency="USD",
            ),
        )
        defaulted = cast(
            "Any",
            set_default_execution_session(
                created.session_id,
                expected_version=created.version,
                request_id=generate_id("req"),
            ),
        )

        async def verify(_: object) -> dict[str, object]:
            return {"verified": True, "mode": "sim", "simulation_runtime_ref": "sim-1"}

        started = cast(
            "Any",
            asyncio.run(
                start_execution_session(
                    created.session_id,
                    expected_version=defaulted.version,
                    authority_start=verify,
                    request_id=generate_id("req"),
                )
            ),
        )
        assert started.is_active is True

        async def reconcile(_: object) -> dict[str, object]:
            return {"safe_to_stop": True}

        stopped = cast(
            "Any",
            asyncio.run(
                stop_execution_session(
                    created.session_id,
                    expected_version=started.version,
                    authority_stop=reconcile,
                    request_id=generate_id("req"),
                )
            ),
        )
        assert stopped.lifecycle_state == "stopped"
        persisted = cast(
            "Any",
            list_execution_sessions(
                principal_id="principal-one", environment_id="environment-one"
            )[0],
        )
        assert persisted.simulation_runtime_ref == "sim-1"
        assert str(persisted.sim_initial_balance) == "100000"
        assert persisted.sim_leverage == 100
        assert persisted.sim_account_currency == "USD"
        assert [
            event["event_type"]
            for event in get_execution_session_events(created.session_id)
        ] == ["stopped", "started", "default_selected", "created"]

        with pytest.raises(ValueError, match="default"):
            archive_execution_session(
                created.session_id,
                expected_version=stopped.version,
                request_id=generate_id("req"),
            )


def test_registry_requires_local_values_only_for_sim(tmp_path: Path) -> None:
    """SIM configuration is mandatory and provider-authored modes reject it."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_trading_migrations(request_id=request_id),
            operation="tests.trading.session_registry.migrate",
            request_id=request_id,
        )
        with pytest.raises(ValueError, match="require initial balance and leverage"):
            create_execution_session(
                principal_id="principal-one",
                environment_id="environment-one",
                name="Unconfigured SIM",
                mode="sim",
                provider="simulation",
                request_id=generate_id("req"),
            )
        with pytest.raises(ValueError, match="provider-authored"):
            create_execution_session(
                principal_id="principal-one",
                environment_id="environment-one",
                name="Broker demo",
                mode="demo",
                provider="mt5",
                request_id=generate_id("req"),
                sim_initial_balance="100000",
                sim_leverage=100,
            )


def test_simulation_identity_is_username_scoped_and_monotonic(tmp_path: Path) -> None:
    """SIM logical identities use the authenticated username and never reuse a number."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_trading_migrations(request_id=request_id),
            operation="tests.trading.session_registry.migrate",
            request_id=request_id,
        )
        created = []
        for name in ("First", "Second"):
            created.append(
                cast(
                    "Any",
                    create_execution_session(
                        principal_id="principal-one",
                        environment_id="environment-one",
                        name=name,
                        mode="sim",
                        provider="simulation",
                        request_id=generate_id("req"),
                        simulation_username="Rufaro Haruperi",
                        dataset_ref="dataset-one",
                        dataset_revision="revision-one",
                        dataset_hash="a" * 64,
                        sim_initial_balance="100000",
                        sim_leverage=100,
                        sim_account_currency="USD",
                    ),
                )
            )

        assert [item.simulation_session_id for item in created] == [
            "Rufaro_Haruperi_1",
            "Rufaro_Haruperi_2",
        ]
        assert [item.provider_account_ref for item in created] == [
            "Rufaro_Haruperi",
            "Rufaro_Haruperi",
        ]
        assert [item.sim_sequence for item in created] == [1, 2]


def test_stopped_legacy_sim_configuration_is_completed_atomically(
    tmp_path: Path,
) -> None:
    """A stopped legacy SIM receives identity, account name, lineage, and one event."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_trading_migrations(request_id=request_id),
            operation="tests.trading.session_registry.migrate",
            request_id=request_id,
        )
        legacy = cast(
            "Any",
            create_execution_session(
                principal_id="usr_haruquantai",
                environment_id="dev",
                name="Test 2",
                mode="sim",
                provider="simulation",
                request_id=generate_id("req"),
                dataset_ref="old-dataset",
                dataset_revision="old-revision",
                dataset_hash="b" * 64,
                sim_initial_balance="100000",
                sim_leverage=100,
                sim_account_currency="USD",
            ),
        )
        configured = cast(
            "Any",
            complete_simulation_session_configuration(
                legacy.session_id,
                expected_version=legacy.version,
                username="haruquantai",
                account_name="haruquantai",
                dataset_ref="verified-dataset",
                dataset_revision="verified-revision",
                dataset_hash="a" * 64,
                request_id=generate_id("req"),
            ),
        )

        assert configured.provider_account_ref == "haruquantai"
        assert configured.simulation_session_id == "haruquantai_1"
        assert configured.dataset_ref == "verified-dataset"
        assert (
            get_execution_session_events(legacy.session_id)[0]["event_type"]
            == "configuration_completed"
        )
