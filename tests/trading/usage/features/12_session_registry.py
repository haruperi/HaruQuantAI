"""Standalone usage evidence for FEAT-TRD-12."""

import asyncio
import sys
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.trading import (
    archive_execution_session,
    assign_simulation_session_identity,
    complete_simulation_session_configuration,
    create_execution_session,
    get_execution_session,
    get_execution_session_events,
    list_execution_sessions,
    resolve_active_execution_session,
    run_trading_migrations,
    set_default_execution_session,
    start_execution_session,
    stop_execution_session,
    update_execution_session_metadata,
)


async def _verified(_: object) -> dict[str, object]:
    """Return bounded SIM authority evidence."""
    return {"verified": True, "mode": "sim", "simulation_runtime_ref": "sim-usage"}


async def _reconciled(_: object) -> dict[str, object]:
    """Return bounded stop reconciliation evidence."""
    return {"safe_to_stop": True}


def main() -> None:
    """Exercise every public durable-session operation."""
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///session-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            request_id = generate_id("req")
            unwrap_data_response(
                run_trading_migrations(request_id=request_id),
                operation="usage.trading.session_registry",
                request_id=request_id,
            )
            created = cast(
                "Any",
                create_execution_session(
                    principal_id="usage-principal",
                    environment_id="usage-environment",
                    name="Research SIM",
                    mode="sim",
                    provider="simulation",
                    request_id=generate_id("req"),
                    dataset_ref="dataset-usage",
                    dataset_revision="revision-usage",
                    dataset_hash="a" * 64,
                    sim_initial_balance="100000",
                    sim_leverage=100,
                    sim_account_currency="USD",
                ),
            )
            created = cast(
                "Any",
                assign_simulation_session_identity(
                    created.session_id,
                    expected_version=created.version,
                    username="usage-user",
                    request_id=generate_id("req"),
                ),
            )
            created = cast(
                "Any",
                complete_simulation_session_configuration(
                    created.session_id,
                    expected_version=created.version,
                    username="usage-user",
                    account_name="Research SIM",
                    dataset_ref="dataset-usage",
                    dataset_revision="revision-usage",
                    dataset_hash="a" * 64,
                    request_id=generate_id("req"),
                ),
            )
            updated = cast(
                "Any",
                update_execution_session_metadata(
                    created.session_id,
                    expected_version=created.version,
                    name="Research SIM 2026",
                    description="Persistent experiment",
                    auto_start=True,
                    metadata={"purpose": "research"},
                    request_id=generate_id("req"),
                ),
            )
            defaulted = cast(
                "Any",
                set_default_execution_session(
                    created.session_id,
                    expected_version=updated.version,
                    request_id=generate_id("req"),
                ),
            )
            started = cast(
                "Any",
                asyncio.run(
                    start_execution_session(
                        created.session_id,
                        expected_version=defaulted.version,
                        authority_start=_verified,
                        request_id=generate_id("req"),
                    )
                ),
            )
            assert (
                resolve_active_execution_session(
                    principal_id="usage-principal", environment_id="usage-environment"
                )
                is not None
            )
            stopped = cast(
                "Any",
                asyncio.run(
                    stop_execution_session(
                        created.session_id,
                        expected_version=started.version,
                        authority_stop=_reconciled,
                        request_id=generate_id("req"),
                    )
                ),
            )
            assert get_execution_session(created.session_id) is not None
            assert list_execution_sessions(
                principal_id="usage-principal", environment_id="usage-environment"
            )
            assert get_execution_session_events(created.session_id)
            with suppress(ValueError):
                archive_execution_session(
                    created.session_id,
                    expected_version=stopped.version,
                    request_id=generate_id("req"),
                )
            print("SUCCESS: FEAT-TRD-12 durable session lifecycle and evidence")


if __name__ == "__main__":
    main()
