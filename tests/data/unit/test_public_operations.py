"""Focused coverage for Data package-root getters and opaque helpers."""

from app.services import data


def test_public_getters_return_defensive_domain_metadata() -> None:
    """Package-root getters expose useful copies without leaking constants."""
    assert data.get_data_error_manifest()
    assert data.get_market_dataset_schema()
    assert data.get_normalization_version()
    assert data.get_precision_policies()
    assert data.get_quality_sample_limit() > 0
    assert data.get_workflow_contexts()
    assert data.get_operation_traits()
    assert data.get_calendar_sites()
    assert data.get_default_minimum_impact()
    assert data.get_symbol_event_profiles()
    assert data.get_read_only_broker_methods()
    assert data.get_timeframe_manifest()
    assert data.get_forex_named_sessions()
    assert data.get_audit_query_hard_max_limit() > 0
    assert data.get_data_migration_steps()
    assert data.get_account_snapshot_schema()
    assert data.get_fx_conversion_evidence_schema()
    assert data.get_market_context_schema()


def test_public_error_helpers_are_opaque() -> None:
    """Opaque helpers identify Data errors without exporting their class."""
    error = data.build_data_error("INVALID_INPUT")

    assert data.is_data_error(error)
    assert not data.is_data_error(ValueError("outside Data"))
