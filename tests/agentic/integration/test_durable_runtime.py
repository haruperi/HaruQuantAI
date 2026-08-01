"""Integration evidence for durable Agentic public-API composition."""

from pathlib import Path

from app.agentic import (
    build_durable_agentic_dependencies,
    get_firm_run,
    submit_firm_request,
)
from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.utils import generate_id

from tests.agentic.fixtures import NOW
from tests.agentic.integration.test_public_api_boundary import (
    WORKFLOW_NAME,
    _dependencies,
    _Operator,
)


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///agentic-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _durable_dependencies() -> object:
    """Replace reference stores with the canonical durable bundle.

    Returns:
        Opaque Agentic dependency bundle.
    """
    reference = _dependencies()
    return build_durable_agentic_dependencies(
        reference.settings,
        reference.mandate,
        reference.registry,
        reference.definitions,
        reference.agent_policies,
        reference.tool_policies,
    )


def test_agentic_run_survives_dependency_reconstruction(tmp_path: Path) -> None:
    """A submitted run remains inspectable after all handles are rebuilt."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.agentic.runtime.migrations",
            request_id=request_id,
        )
        auth = _Operator()
        submitted = submit_firm_request(
            _durable_dependencies(),
            auth,
            WORKFLOW_NAME,
            "Assess EURUSD H1 trend evidence.",
            ("evidence-market-1",),
            "idem-durable-runtime",
            at_time=NOW,
        )
        inspected = get_firm_run(
            _durable_dependencies(), auth, str(submitted.payload["run_id"])
        )

    assert submitted.status == "ok"
    assert inspected.status == "ok"
    assert inspected.payload["run_id"] == submitted.payload["run_id"]
