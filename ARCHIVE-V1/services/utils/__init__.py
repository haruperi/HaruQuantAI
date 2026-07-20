"""Public registry for approved HaruQuant utility APIs.

The registry intentionally exposes only stable, cross-domain utilities and
approved agent-facing validation tools. Heavier implementation modules are
loaded lazily so importing ``app.services.utils`` remains lightweight and side-effect
free.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, str] = {
    # logger.py
    "logger": "app.services.utils.logger",
    "get_logger": "app.services.utils.logger",
    "get_child_logger": "app.services.utils.logger",
    "configure_logging": "app.services.utils.logger",
    # standard.py
    "ToolStandardSpec": "app.services.utils.standard",
    "standard_tool_response": "app.services.utils.standard",
    "standardize_tool_callable": "app.services.utils.standard",
    "standardize_domain_exports": "app.services.utils.standard",
    "validate_tool_response_envelope": "app.services.utils.standard",
    "validate_tool_response_schema": "app.services.utils.standard",
    "validate_standard_response": "app.services.utils.standard",
    "circuit_open_response": "app.services.utils.standard",
    "build_metadata": "app.services.utils.standard",
    "error_response": "app.services.utils.standard",
    "response_from_exception": "app.services.utils.standard",
    "stable_identifier": "app.services.utils.standard",
    "success_response": "app.services.utils.standard",
    "is_official_tool_allowed": "app.services.utils.standard",
    # errors.py
    "HaruError": "app.services.utils.errors",
    "DomainError": "app.services.utils.errors",
    "InfrastructureError": "app.services.utils.errors",
    "PolicyError": "app.services.utils.errors",
    "BrokerError": "app.services.utils.errors",
    "ValidationError": "app.services.utils.errors",
    "SecurityError": "app.services.utils.errors",
    "ConfigurationError": "app.services.utils.errors",
    "DataError": "app.services.utils.errors",
    "ExternalServiceError": "app.services.utils.errors",
    "ErrorContext": "app.services.utils.errors",
    "ErrorDescriptor": "app.services.utils.errors",
    "ErrorEnvelope": "app.services.utils.errors",
    "ErrorRouteResult": "app.services.utils.errors",
    "code_for_exception": "app.services.utils.errors",
    "details_for_exception": "app.services.utils.errors",
    "error_name": "app.services.utils.errors",
    "exception_to_error_payload": "app.services.utils.errors",
    "message_for": "app.services.utils.errors",
    "normalize_error_code": "app.services.utils.errors",
    "raise_for_invalid_code": "app.services.utils.errors",
    "route_error": "app.services.utils.errors",
    # identity.py
    "generate_id": "app.services.utils.identity",
    "generate_prefixed_id": "app.services.utils.identity",
    "generate_request_id": "app.services.utils.identity",
    "generate_workflow_id": "app.services.utils.identity",
    "generate_correlation_id": "app.services.utils.identity",
    "generate_causation_id": "app.services.utils.identity",
    "generate_event_id": "app.services.utils.identity",
    "generate_idempotency_id": "app.services.utils.identity",
    "validate_id": "app.services.utils.identity",
    "validate_request_id": "app.services.utils.identity",
    "validate_workflow_id": "app.services.utils.identity",
    "ensure_version": "app.services.utils.identity",
    "ensure_version_value": "app.services.utils.identity",
    "apply_version_update": "app.services.utils.identity",
    "StaleVersionError": "app.services.utils.identity",
    # normalization.py
    "normalize_path": "app.services.utils.normalization",
    "parse_datetime": "app.services.utils.normalization",
    "to_utc": "app.services.utils.normalization",
    "to_utc_datetime": "app.services.utils.normalization",
    "to_naive_utc": "app.services.utils.normalization",
    "utc_now": "app.services.utils.normalization",
    "format_timestamp_z": "app.services.utils.normalization",
    "format_utc_timestamp": "app.services.utils.normalization",
    "normalize_timestamp": "app.services.utils.normalization",
    "normalize_timezone_for_series": "app.services.utils.normalization",
    "evaluate_freshness": "app.services.utils.normalization",
    "is_stale": "app.services.utils.normalization",
    # paths.py
    "normalize_path_value": "app.services.utils.paths",
    "ensure_dir_value": "app.services.utils.paths",
    "ensure_parent_dir_value": "app.services.utils.paths",
    "ensure_dir": "app.services.utils.paths",
    "ensure_parent_dir": "app.services.utils.paths",
    "safe_join": "app.services.utils.paths",
    "validate_path_within_root": "app.services.utils.paths",
    # common.py
    "Param": "app.services.utils.common",
    "canonical_json": "app.services.utils.common",
    "chunked": "app.services.utils.common",
    "combine_params": "app.services.utils.common",
    "merge": "app.services.utils.common",
    "concat": "app.services.utils.common",
    "rolling_mean": "app.services.utils.common",
    "clear_dataframe_cache": "app.services.utils.common",
    "get_cached_dataframe": "app.services.utils.common",
    "tool_result_envelope": "app.services.utils.common",
    # dataframe_tools.py
    "serialize_dataframe_records": "app.services.utils.dataframe_tools",
    "bars_to_records": "app.services.utils.dataframe_tools",
    "bar_to_record": "app.services.utils.dataframe_tools",
    "align_dataframes_by_datetime": "app.services.utils.dataframe_tools",
    "align_dataframe_datetime": "app.services.utils.dataframe_tools",
    "compare_dataframes": "app.services.utils.dataframe_tools",
    "compare_ohlc": "app.services.utils.dataframe_tools",
    "compare_ohlcv": "app.services.utils.dataframe_tools",
    "dataframe_columns": "app.services.utils.dataframe_tools",
    "dataframe_tools": "app.services.utils.dataframe_tools",
    "iter_dataframe_records": "app.services.utils.dataframe_tools",
    "parameter_combinations": "app.services.utils.dataframe_tools",
    "chunk_sequence": "app.services.utils.dataframe_tools",
    # validators.py
    "prepare_ohlcv_data": "app.services.utils.validators",
    "validate_environment_mode": "app.services.utils.validators",
    "validate_artifact_reference": "app.services.utils.validators",
    "DataQualityReport": "app.services.utils.validators",
    "validate_find_column": "app.services.utils.validators",
    "validate_find_columns": "app.services.utils.validators",
    "validate_get_time_series": "app.services.utils.validators",
    "validate_high_low": "app.services.utils.validators",
    "validate_price_in_range": "app.services.utils.validators",
    "validate_negative_prices": "app.services.utils.validators",
    "validate_zero_prices": "app.services.utils.validators",
    "validate_price_sanity": "app.services.utils.validators",
    "validate_gaps": "app.services.utils.validators",
    "validate_market_calendar_gaps": "app.services.utils.validators",
    "validate_numeric_integrity": "app.services.utils.validators",
    "validate_timezone_awareness": "app.services.utils.validators",
    "validate_duplicate_ohlc_rows": "app.services.utils.validators",
    "validate_flatlines": "app.services.utils.validators",
    "validate_spikes": "app.services.utils.validators",
    "validate_missing_timestamps": "app.services.utils.validators",
    "validate_zero_volume": "app.services.utils.validators",
    "validate_duplicates": "app.services.utils.validators",
    "validate_monotonic_timestamps": "app.services.utils.validators",
    "validate_spread": "app.services.utils.validators",
    "validate_issue_severity": "app.services.utils.validators",
    "validate_issue_remediation_action": "app.services.utils.validators",
    "validate_annotate_issues": "app.services.utils.validators",
    "validate_remediation_summary": "app.services.utils.validators",
    "DataSource": "app.services.utils.validators",
    "OHLCVSchema": "app.services.utils.validators",
    "get_session_ranges": "app.services.utils.validators",
    "compute_session_stats": "app.services.utils.validators",
    # data_quality.py
    "validate_ohlcv_quality": "app.services.utils.data_quality",
    "inspect_ohlcv_quality": "app.services.utils.data_quality",
    "data_quality": "app.services.utils.data_quality",
    # schema_validation.py
    "validate_required_fields": "app.services.utils.schema_validation",
    "validate_input_schema": "app.services.utils.schema_validation",
    "validate_output_schema": "app.services.utils.schema_validation",
    "validate_handoff_payload": "app.services.utils.schema_validation",
    "validate_evidence_pack": "app.services.utils.schema_validation",
    "validate_approval_packet": "app.services.utils.schema_validation",
    "validate_registry_entry": "app.services.utils.schema_validation",
    "validate_blocked_actions": "app.services.utils.schema_validation",
    "validate_data_freshness": "app.services.utils.schema_validation",
    "validate_numeric_range": "app.services.utils.schema_validation",
    # security.py
    "is_sensitive_key": "app.services.utils.security",
    "SENSITIVE_KEY_PATTERN": "app.services.utils.security",
    "classify_secret_key": "app.services.utils.security",
    "redact_scalar": "app.services.utils.security",
    "redact_text": "app.services.utils.security",
    "redact_text_tool": "app.services.utils.security",
    "redact_text_value": "app.services.utils.security",
    "redact_mapping": "app.services.utils.security",
    "redact_mapping_tool": "app.services.utils.security",
    "redact_mapping_value": "app.services.utils.security",
    "redact_payload": "app.services.utils.security",
    "encrypt_text": "app.services.utils.security",
    "decrypt_text": "app.services.utils.security",
    "encrypt_data": "app.services.utils.security",
    "decrypt_data": "app.services.utils.security",
    "generate_encryption_key": "app.services.utils.security",
    "load_encryption_key": "app.services.utils.security",
    "select_active_secret_version": "app.services.utils.security",
    "hash_password": "app.services.utils.security",
    "verify_password": "app.services.utils.security",
    # settings.py
    "Settings": "app.services.utils.settings",
    "settings": "app.services.utils.settings",
    "RuntimeSettings": "app.services.utils.settings",
    "load_runtime_settings": "app.services.utils.settings",
    "load_runtime_settings_from_mapping": "app.services.utils.settings",
    "inject_runtime_settings": "app.services.utils.settings",
    "create_config": "app.services.utils.settings",
    "load_config": "app.services.utils.settings",
    "validate_config": "app.services.utils.settings",
    "get_settings": "app.services.utils.settings",
    "research_modeling_module": "app.services.utils.settings",
    # auth.py
    "AuthContext": "app.services.utils.auth",
    "AuthorizationResult": "app.services.utils.auth",
    "validate_auth_context": "app.services.utils.auth",
    "authorize_tool_call": "app.services.utils.auth",
    "authorize_action": "app.services.utils.auth",
    "build_auth_context": "app.services.utils.auth",
    "require_authorization": "app.services.utils.auth",
    # event_bus.py
    "EventEnvelope": "app.services.utils.event_bus",
    "InProcessEventBus": "app.services.utils.event_bus",
    "InMemoryEventBus": "app.services.utils.event_bus",
    "PublishResult": "app.services.utils.event_bus",
    "build_event_envelope": "app.services.utils.event_bus",
    "publish_event": "app.services.utils.event_bus",

    # observability.py
    "MetricRegistry": "app.services.utils.observability",
    "CircuitBreaker": "app.services.utils.observability",
    "HealthCheckResult": "app.services.utils.observability",
    "health_snapshot": "app.services.utils.observability",
    "build_health_snapshot": "app.services.utils.observability",
    "check_clock_drift_health": "app.services.utils.observability",
    "export_prometheus_metrics": "app.services.utils.observability",
    "record_metric": "app.services.utils.observability",
    "record_tool_call_metric": "app.services.utils.observability",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load approved utility exports on first access."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'app.services.utils' has no attribute {name!r}")
    module = import_module(module_name)
    if hasattr(module, name):
        value = getattr(module, name)
        globals()[name] = value
        return value
    globals()[name] = module
    return module
