"""Golden package-root API coverage for the Data domain."""

from __future__ import annotations

from importlib import import_module

from app.services import data

_PUBLIC_MODULES = (
    "app.services.data.audit",
    "app.services.data.audit.contracts",
    "app.services.data.contracts",
    "app.services.data.data_jobs",
    "app.services.data.data_jobs.contracts",
    "app.services.data.economic_calendar",
    "app.services.data.evidence",
    "app.services.data.evidence.account_contracts",
    "app.services.data.evidence.fx_contracts",
    "app.services.data.evidence.market_context_contracts",
    "app.services.data.local_datasets",
    "app.services.data.market_data",
    "app.services.data.persistence",
    "app.services.data.persistence.contracts",
    "app.services.data.quality",
    "app.services.data.realtime_feeds",
    "app.services.data.realtime_feeds.contracts",
    "app.services.data.sources",
    "app.services.data.sources.contracts",
    "app.services.data.sources.local_adapter",
    "app.services.data.sources.read_only",
    "app.services.data.synthetic_data",
    "app.services.data.tick_derivation",
    "app.services.data.time_sessions",
    "app.services.data.transformation",
)
_APPROVED_INFRASTRUCTURE_EXPORTS = {"DataSettings", "data_settings_context"}
_APPROVED_FACADE_EXPORTS = {
    "CALENDAR_SITES",
    "create_data_update_job",
    "get_data_update_job_status",
    "get_feed_status",
    "start_data_update_job",
    "stop_data_update_job",
}
_OMITTED_PRIVATE_NAMES = {
    "CACHE_CLEAR_MAX_ENTRIES",
    "CACHE_TTL_MAX_SECONDS",
    "CURRENCY_CODE_LENGTH",
    "ERROR_SAFE_DETAILS_MAX_BYTES",
    "ERROR_SAFE_DETAILS_MAX_ITEMS",
    "IMPORT_DIALECTS",
    "_OHLC_COLUMN_COUNT",
}


def _expected_api() -> set[str]:
    """Build the approved root surface from registered feature-module exports."""
    names = _APPROVED_INFRASTRUCTURE_EXPORTS | _APPROVED_FACADE_EXPORTS
    for module_name in _PUBLIC_MODULES:
        module = import_module(module_name)
        names.update(getattr(module, "__all__", ()))
    return names - _OMITTED_PRIVATE_NAMES


def test_package_root_exports_exact_approved_surface() -> None:
    """Every registered feature export crosses only the package root."""
    expected = _expected_api()

    assert set(data.__all__) == expected
    assert len(data.__all__) == len(expected)
    assert {name for name in expected if hasattr(data, name)} == expected
    assert all(not name.startswith("_") for name in data.__all__)
