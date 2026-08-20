"""Business-neutral shared infrastructure for HaruQuantAI domains."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.utils.contracts import (
        build_event_envelope,
        create_audit_event,
        create_auth_context,
        find_sequence_gap,
        get_audit_event_type,
        get_auth_context_type,
        is_duplicate_event,
        parse_event_envelope,
    )
    from app.utils.errors import (
        build_health_state,
        create_validation_error,
        get_common_error_catalog,
        get_error_metadata,
        map_exception,
        normalize_error_code,
        parse_health_state,
        require_error_definition,
        route_error_event,
        validate_error_catalog,
    )
    from app.utils.idempotency import (
        build_reservation,
        derive_idempotency_key,
        evaluate_reservation,
        get_key_owner,
        is_reservation_expired,
        parse_idempotency_key,
    )
    from app.utils.identity import derive_stable_id, generate_id, validate_id
    from app.utils.logging import (
        configure_logging,
        flush_logging,
        get_logger,
        get_logger_handler_count,
        get_logger_name,
        log_info,
        route_audit_event,
        shutdown_logging,
    )
    from app.utils.notifications import (
        build_desktop_notification_config,
        build_email_notification_config,
        build_notification_manager_config,
        build_sms_notification_config,
        build_telegram_notification_config,
        close_notification_manager,
        create_notification_manager,
        get_notification_manager_status,
        get_notification_template_names,
        register_notification_template,
        render_notification_template,
        send_notification,
    )
    from app.utils.progress import (
        create_progress_snapshot,
        make_progress_callback,
    )
    from app.utils.random_streams import (
        derive_random_stream,
        get_stream_identity,
        next_choice,
        next_int,
        next_uniform,
    )
    from app.utils.responses import (
        build_response_metadata,
        error_response,
        exception_response,
        get_execution_ms,
        get_standard_response_type,
        success_response,
    )
    from app.utils.security import (
        get_default_redaction_policy,
        is_sensitive_key,
        redact_contract_mapping,
        redact_mapping_value,
        redact_text_value,
    )
    from app.utils.serialization import canonical_digest, canonical_json, to_json_safe
    from app.utils.settings import (
        build_profile_ref,
        build_version_ref,
        get_app_settings_model_config,
        get_app_settings_sources,
        load_broker_provider_settings,
        load_profile_document,
        load_settings,
        parse_profile_ref,
        parse_version_ref,
    )
    from app.utils.state_machine import (
        attempt_transition,
        build_transition_record,
        build_transition_table,
        is_terminal_state,
    )
    from app.utils.time import (
        age_seconds,
        build_time_stamp,
        compare_time_stamps,
        format_utc_timestamp,
        from_venue_local,
        is_fresh,
        next_sequence,
        parse_time_stamp,
        parse_utc_timestamp,
        to_venue_local,
        utc_now,
    )
    from app.utils.units import (
        add_exact,
        build_exact_unit,
        compare_exact,
        get_max_decimal_places,
        get_supported_unit_kinds,
        parse_exact_unit,
        quantize_exact,
        scale_exact,
        subtract_exact,
        unit_kind_requires_currency,
    )
    from app.utils.validation import (
        build_validation_outcome,
        combine_validation_outcomes,
        get_severity_rank,
        parse_validation_outcome,
        validate_reason_code,
    )

_EXPORTS: dict[str, tuple[str, str]] = {
    # contracts
    "build_event_envelope": ("app.utils.contracts", "build_event_envelope"),
    "create_audit_event": ("app.utils.contracts", "create_audit_event"),
    "create_auth_context": ("app.utils.contracts", "create_auth_context"),
    "find_sequence_gap": ("app.utils.contracts", "find_sequence_gap"),
    "get_audit_event_type": ("app.utils.contracts", "get_audit_event_type"),
    "get_auth_context_type": ("app.utils.contracts", "get_auth_context_type"),
    "is_duplicate_event": ("app.utils.contracts", "is_duplicate_event"),
    "parse_event_envelope": ("app.utils.contracts", "parse_event_envelope"),
    # errors
    "build_health_state": ("app.utils.errors", "build_health_state"),
    "create_validation_error": ("app.utils.errors", "create_validation_error"),
    "get_common_error_catalog": ("app.utils.errors", "get_common_error_catalog"),
    "get_error_metadata": ("app.utils.errors", "get_error_metadata"),
    "map_exception": ("app.utils.errors", "map_exception"),
    "normalize_error_code": ("app.utils.errors", "normalize_error_code"),
    "parse_health_state": ("app.utils.errors", "parse_health_state"),
    "require_error_definition": ("app.utils.errors", "require_error_definition"),
    "route_error_event": ("app.utils.errors", "route_error_event"),
    "validate_error_catalog": ("app.utils.errors", "validate_error_catalog"),
    # idempotency
    "build_reservation": ("app.utils.idempotency", "build_reservation"),
    "derive_idempotency_key": ("app.utils.idempotency", "derive_idempotency_key"),
    "evaluate_reservation": ("app.utils.idempotency", "evaluate_reservation"),
    "get_key_owner": ("app.utils.idempotency", "get_key_owner"),
    "is_reservation_expired": ("app.utils.idempotency", "is_reservation_expired"),
    "parse_idempotency_key": ("app.utils.idempotency", "parse_idempotency_key"),
    # identity
    "derive_stable_id": ("app.utils.identity", "derive_stable_id"),
    "generate_id": ("app.utils.identity", "generate_id"),
    "validate_id": ("app.utils.identity", "validate_id"),
    # logging
    "configure_logging": ("app.utils.logging", "configure_logging"),
    "flush_logging": ("app.utils.logging", "flush_logging"),
    "get_logger": ("app.utils.logging", "get_logger"),
    "get_logger_handler_count": ("app.utils.logging", "get_logger_handler_count"),
    "get_logger_name": ("app.utils.logging", "get_logger_name"),
    "log_info": ("app.utils.logging", "log_info"),
    "route_audit_event": ("app.utils.logging", "route_audit_event"),
    "shutdown_logging": ("app.utils.logging", "shutdown_logging"),
    # notifications
    "build_desktop_notification_config": (
        "app.utils.notifications",
        "build_desktop_notification_config",
    ),
    "build_email_notification_config": (
        "app.utils.notifications",
        "build_email_notification_config",
    ),
    "build_notification_manager_config": (
        "app.utils.notifications",
        "build_notification_manager_config",
    ),
    "build_sms_notification_config": (
        "app.utils.notifications",
        "build_sms_notification_config",
    ),
    "build_telegram_notification_config": (
        "app.utils.notifications",
        "build_telegram_notification_config",
    ),
    "close_notification_manager": (
        "app.utils.notifications",
        "close_notification_manager",
    ),
    "create_notification_manager": (
        "app.utils.notifications",
        "create_notification_manager",
    ),
    "get_notification_manager_status": (
        "app.utils.notifications",
        "get_notification_manager_status",
    ),
    "get_notification_template_names": (
        "app.utils.notifications",
        "get_notification_template_names",
    ),
    "register_notification_template": (
        "app.utils.notifications",
        "register_notification_template",
    ),
    "render_notification_template": (
        "app.utils.notifications",
        "render_notification_template",
    ),
    "send_notification": ("app.utils.notifications", "send_notification"),
    # progress
    "create_progress_snapshot": ("app.utils.progress", "create_progress_snapshot"),
    "make_progress_callback": ("app.utils.progress", "make_progress_callback"),
    # random_streams
    "derive_random_stream": ("app.utils.random_streams", "derive_random_stream"),
    "get_stream_identity": ("app.utils.random_streams", "get_stream_identity"),
    "next_choice": ("app.utils.random_streams", "next_choice"),
    "next_int": ("app.utils.random_streams", "next_int"),
    "next_uniform": ("app.utils.random_streams", "next_uniform"),
    # responses
    "build_response_metadata": ("app.utils.responses", "build_response_metadata"),
    "error_response": ("app.utils.responses", "error_response"),
    "exception_response": ("app.utils.responses", "exception_response"),
    "get_execution_ms": ("app.utils.responses", "get_execution_ms"),
    "get_standard_response_type": (
        "app.utils.responses",
        "get_standard_response_type",
    ),
    "success_response": ("app.utils.responses", "success_response"),
    # security
    "get_default_redaction_policy": (
        "app.utils.security",
        "get_default_redaction_policy",
    ),
    "is_sensitive_key": ("app.utils.security", "is_sensitive_key"),
    "redact_contract_mapping": (
        "app.utils.security",
        "redact_contract_mapping",
    ),
    "redact_mapping_value": ("app.utils.security", "redact_mapping_value"),
    "redact_text_value": ("app.utils.security", "redact_text_value"),
    # serialization
    "canonical_digest": ("app.utils.serialization", "canonical_digest"),
    "canonical_json": ("app.utils.serialization", "canonical_json"),
    "to_json_safe": ("app.utils.serialization", "to_json_safe"),
    # settings
    "build_profile_ref": ("app.utils.settings", "build_profile_ref"),
    "build_version_ref": ("app.utils.settings", "build_version_ref"),
    "get_app_settings_model_config": (
        "app.utils.settings",
        "get_app_settings_model_config",
    ),
    "get_app_settings_sources": ("app.utils.settings", "get_app_settings_sources"),
    "load_broker_provider_settings": (
        "app.utils.settings",
        "load_broker_provider_settings",
    ),
    "load_profile_document": ("app.utils.settings", "load_profile_document"),
    "load_settings": ("app.utils.settings", "load_settings"),
    "parse_profile_ref": ("app.utils.settings", "parse_profile_ref"),
    "parse_version_ref": ("app.utils.settings", "parse_version_ref"),
    # state_machine
    "attempt_transition": ("app.utils.state_machine", "attempt_transition"),
    "build_transition_record": ("app.utils.state_machine", "build_transition_record"),
    "build_transition_table": ("app.utils.state_machine", "build_transition_table"),
    "is_terminal_state": ("app.utils.state_machine", "is_terminal_state"),
    # time
    "age_seconds": ("app.utils.time", "age_seconds"),
    "build_time_stamp": ("app.utils.time", "build_time_stamp"),
    "compare_time_stamps": ("app.utils.time", "compare_time_stamps"),
    "format_utc_timestamp": ("app.utils.time", "format_utc_timestamp"),
    "from_venue_local": ("app.utils.time", "from_venue_local"),
    "is_fresh": ("app.utils.time", "is_fresh"),
    "next_sequence": ("app.utils.time", "next_sequence"),
    "parse_time_stamp": ("app.utils.time", "parse_time_stamp"),
    "parse_utc_timestamp": ("app.utils.time", "parse_utc_timestamp"),
    "to_venue_local": ("app.utils.time", "to_venue_local"),
    "utc_now": ("app.utils.time", "utc_now"),
    # units
    "add_exact": ("app.utils.units", "add_exact"),
    "build_exact_unit": ("app.utils.units", "build_exact_unit"),
    "compare_exact": ("app.utils.units", "compare_exact"),
    "get_max_decimal_places": ("app.utils.units", "get_max_decimal_places"),
    "get_supported_unit_kinds": ("app.utils.units", "get_supported_unit_kinds"),
    "parse_exact_unit": ("app.utils.units", "parse_exact_unit"),
    "quantize_exact": ("app.utils.units", "quantize_exact"),
    "scale_exact": ("app.utils.units", "scale_exact"),
    "subtract_exact": ("app.utils.units", "subtract_exact"),
    "unit_kind_requires_currency": (
        "app.utils.units",
        "unit_kind_requires_currency",
    ),
    # validation
    "build_validation_outcome": ("app.utils.validation", "build_validation_outcome"),
    "combine_validation_outcomes": (
        "app.utils.validation",
        "combine_validation_outcomes",
    ),
    "get_severity_rank": ("app.utils.validation", "get_severity_rank"),
    "parse_validation_outcome": ("app.utils.validation", "parse_validation_outcome"),
    "validate_reason_code": ("app.utils.validation", "validate_reason_code"),
}


def __getattr__(name: str) -> object:
    """Resolve public exports lazily.

    Args:
        name: Public export name.

    Returns:
        The resolved public symbol.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = (
    "add_exact",
    "age_seconds",
    "attempt_transition",
    "build_desktop_notification_config",
    "build_email_notification_config",
    "build_event_envelope",
    "build_exact_unit",
    "build_health_state",
    "build_notification_manager_config",
    "build_profile_ref",
    "build_reservation",
    "build_response_metadata",
    "build_sms_notification_config",
    "build_telegram_notification_config",
    "build_time_stamp",
    "build_transition_record",
    "build_transition_table",
    "build_validation_outcome",
    "build_version_ref",
    "canonical_digest",
    "canonical_json",
    "close_notification_manager",
    "combine_validation_outcomes",
    "compare_exact",
    "compare_time_stamps",
    "configure_logging",
    "create_audit_event",
    "create_auth_context",
    "create_notification_manager",
    "create_progress_snapshot",
    "create_validation_error",
    "derive_idempotency_key",
    "derive_random_stream",
    "derive_stable_id",
    "error_response",
    "evaluate_reservation",
    "exception_response",
    "find_sequence_gap",
    "flush_logging",
    "format_utc_timestamp",
    "from_venue_local",
    "generate_id",
    "get_app_settings_model_config",
    "get_app_settings_sources",
    "get_audit_event_type",
    "get_auth_context_type",
    "get_common_error_catalog",
    "get_default_redaction_policy",
    "get_error_metadata",
    "get_execution_ms",
    "get_key_owner",
    "get_logger",
    "get_logger_handler_count",
    "get_logger_name",
    "get_max_decimal_places",
    "get_notification_manager_status",
    "get_notification_template_names",
    "get_severity_rank",
    "get_standard_response_type",
    "get_stream_identity",
    "get_supported_unit_kinds",
    "is_duplicate_event",
    "is_fresh",
    "is_reservation_expired",
    "is_sensitive_key",
    "is_terminal_state",
    "load_broker_provider_settings",
    "load_profile_document",
    "load_settings",
    "log_info",
    "make_progress_callback",
    "map_exception",
    "next_choice",
    "next_int",
    "next_sequence",
    "next_uniform",
    "normalize_error_code",
    "parse_event_envelope",
    "parse_exact_unit",
    "parse_health_state",
    "parse_idempotency_key",
    "parse_profile_ref",
    "parse_time_stamp",
    "parse_utc_timestamp",
    "parse_validation_outcome",
    "parse_version_ref",
    "quantize_exact",
    "redact_contract_mapping",
    "redact_mapping_value",
    "redact_text_value",
    "register_notification_template",
    "render_notification_template",
    "require_error_definition",
    "route_audit_event",
    "route_error_event",
    "scale_exact",
    "send_notification",
    "shutdown_logging",
    "subtract_exact",
    "success_response",
    "to_json_safe",
    "to_venue_local",
    "unit_kind_requires_currency",
    "utc_now",
    "validate_error_catalog",
    "validate_id",
    "validate_reason_code",
)
