import ast
import inspect
import re
from decimal import getcontext
from pathlib import Path

import app.utils

_EXPECTED_EXPORTS = {
    "age_seconds",
    "build_response_metadata",
    "canonical_digest",
    "canonical_json",
    "configure_logging",
    "create_audit_event",
    "create_auth_context",
    "create_validation_error",
    "derive_stable_id",
    "error_response",
    "exception_response",
    "flush_logging",
    "format_utc_timestamp",
    "generate_id",
    "get_app_settings_model_config",
    "get_app_settings_sources",
    "get_common_error_catalog",
    "get_audit_event_type",
    "get_auth_context_type",
    "get_default_redaction_policy",
    "get_error_metadata",
    "get_execution_ms",
    "get_logger",
    "get_logger_handler_count",
    "get_logger_name",
    "get_standard_response_type",
    "is_fresh",
    "is_sensitive_key",
    "load_broker_provider_settings",
    "load_settings",
    "log_info",
    "map_exception",
    "normalize_error_code",
    "parse_utc_timestamp",
    "redact_mapping_value",
    "redact_text_value",
    "require_error_definition",
    "route_error_event",
    "shutdown_logging",
    "success_response",
    "to_json_safe",
    "utc_now",
    "validate_error_catalog",
    "validate_id",
}
_EXPECTED_EXPORTS.update(
    {
        "add_exact",
        "attempt_transition",
        "build_event_envelope",
        "build_exact_unit",
        "build_health_state",
        "build_profile_ref",
        "build_reservation",
        "build_time_stamp",
        "build_transition_record",
        "build_transition_table",
        "build_validation_outcome",
        "build_version_ref",
        "combine_validation_outcomes",
        "compare_exact",
        "compare_time_stamps",
        "derive_idempotency_key",
        "derive_random_stream",
        "evaluate_reservation",
        "find_sequence_gap",
        "from_venue_local",
        "get_key_owner",
        "get_max_decimal_places",
        "get_severity_rank",
        "get_stream_identity",
        "get_supported_unit_kinds",
        "is_duplicate_event",
        "is_reservation_expired",
        "is_terminal_state",
        "load_profile_document",
        "next_choice",
        "next_int",
        "next_sequence",
        "next_uniform",
        "parse_event_envelope",
        "parse_exact_unit",
        "parse_health_state",
        "parse_idempotency_key",
        "parse_profile_ref",
        "parse_time_stamp",
        "parse_validation_outcome",
        "parse_version_ref",
        "quantize_exact",
        "redact_contract_mapping",
        "route_audit_event",
        "scale_exact",
        "subtract_exact",
        "to_venue_local",
        "unit_kind_requires_currency",
        "validate_reason_code",
    }
)
_FORBIDDEN_IMPORT_ROOTS = {
    "app.services",
    "pandas",
    "sqlite3",
}
_EXPECTED_USAGE_CALLS = {
    "01_contracts.py": {
        "build_event_envelope",
        "create_audit_event",
        "create_auth_context",
        "find_sequence_gap",
        "get_audit_event_type",
        "get_auth_context_type",
        "is_duplicate_event",
        "parse_event_envelope",
    },
    "02_errors.py": {
        "build_health_state",
        "create_validation_error",
        "get_common_error_catalog",
        "get_error_metadata",
        "map_exception",
        "normalize_error_code",
        "parse_health_state",
        "require_error_definition",
        "route_error_event",
        "validate_error_catalog",
    },
    "03_identity.py": {"derive_stable_id", "generate_id", "validate_id"},
    "04_time.py": {
        "age_seconds",
        "build_time_stamp",
        "compare_time_stamps",
        "format_utc_timestamp",
        "from_venue_local",
        "is_fresh",
        "next_sequence",
        "parse_time_stamp",
        "parse_utc_timestamp",
        "to_venue_local",
        "utc_now",
    },
    "05_serialization.py": {"canonical_digest", "canonical_json", "to_json_safe"},
    "06_security.py": {
        "get_default_redaction_policy",
        "is_sensitive_key",
        "redact_contract_mapping",
        "redact_mapping_value",
        "redact_text_value",
    },
    "07_settings.py": {
        "build_profile_ref",
        "build_version_ref",
        "get_app_settings_model_config",
        "get_app_settings_sources",
        "load_profile_document",
        "load_broker_provider_settings",
        "load_settings",
        "parse_profile_ref",
        "parse_version_ref",
    },
    "08_logging.py": {
        "configure_logging",
        "flush_logging",
        "get_logger",
        "get_logger_handler_count",
        "get_logger_name",
        "log_info",
        "route_audit_event",
        "shutdown_logging",
    },
    "09_standard_responses.py": {
        "build_response_metadata",
        "error_response",
        "exception_response",
        "get_execution_ms",
        "get_standard_response_type",
        "success_response",
    },
    "10_units.py": {
        "add_exact",
        "build_exact_unit",
        "compare_exact",
        "get_max_decimal_places",
        "get_supported_unit_kinds",
        "parse_exact_unit",
        "quantize_exact",
        "scale_exact",
        "subtract_exact",
        "unit_kind_requires_currency",
    },
    "11_state_machine.py": {
        "attempt_transition",
        "build_transition_record",
        "build_transition_table",
        "is_terminal_state",
    },
    "12_validation.py": {
        "build_validation_outcome",
        "combine_validation_outcomes",
        "get_severity_rank",
        "parse_validation_outcome",
        "validate_reason_code",
    },
    "13_idempotency.py": {
        "derive_idempotency_key",
        "build_reservation",
        "evaluate_reservation",
        "get_key_owner",
        "is_reservation_expired",
        "parse_idempotency_key",
    },
    "14_random_streams.py": {
        "derive_random_stream",
        "get_stream_identity",
        "next_uniform",
        "next_int",
        "next_choice",
    },
}


def test_public_surface_contains_only_documented_exports() -> None:
    assert set(app.utils.__all__) == _EXPECTED_EXPORTS
    assert all(
        inspect.isfunction(getattr(app.utils, name)) for name in app.utils.__all__
    )


def test_audit_runtime_type_is_available_through_root_getter() -> None:
    """Receiver-side validation can resolve the opaque audit event type."""
    audit_type = app.utils.get_audit_event_type()

    assert audit_type.__name__ == "AuditEvent"
    assert audit_type.__module__ == "app.utils.contracts.audit"


def test_feature_roots_declare_only_function_exports() -> None:
    """Ensure Utils feature roots do not declare classes as public."""
    from app.utils import (
        contracts,
        errors,
        logging,
        responses,
        security,
        settings,
        time,
    )

    feature_roots = (contracts, errors, logging, responses, security, settings, time)
    for feature_root in feature_roots:
        assert all(
            inspect.isfunction(getattr(feature_root, name))
            for name in feature_root.__all__
        )


def test_utils_has_no_domain_or_persistence_dependencies() -> None:
    source_root = Path(app.utils.__file__).parent
    imported_modules: set[str] = set()
    for source_file in source_root.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
    assert not any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for module in imported_modules
        for forbidden in _FORBIDDEN_IMPORT_ROOTS
    )


def test_utils_does_not_mutate_decimal_context() -> None:
    assert getcontext().prec >= 28


def test_utils_has_no_print_calls_or_import_time_log_emission() -> None:
    """Keep library output explicit and package imports silent."""
    source_root = Path(app.utils.__file__).parent
    for source_file in source_root.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            for node in ast.walk(tree)
        )
        assert not any(
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "logger"
            for node in tree.body
        )


def test_every_functional_requirement_has_test_and_usage_traceability() -> None:
    source_root = Path(app.utils.__file__).parent
    repository_root = source_root.parents[1]
    readme = (source_root / "README.md").read_text(encoding="utf-8")
    requirement_lines = [
        line
        for line in readme.splitlines()
        if line.startswith("| Completed | `FR-UTL-")
    ]
    completed = {
        match.group(1)
        for line in requirement_lines
        if (match := re.search(r"FR-UTL-(\d{3})", line)) is not None
    }
    assert completed == {
        f"{number:03d}" for number in range(1, 89) if number not in {25, 37, 38}
    }
    for line in requirement_lines:
        assert "**Usage:**" in line
        assert "**Unit:**" in line
        for relative_path in re.findall(r"`(tests/utils/[^`:]+\.py)::", line):
            assert (repository_root / relative_path).is_file()


def test_features_register_contains_every_public_function() -> None:
    """Require the Utils register to name every public exported function."""
    source_root = Path(app.utils.__file__).parent
    register_path = source_root / "README.md"
    content = register_path.read_text(encoding="utf-8")
    registered = set(re.findall(r"`([a-z][a-z0-9_]*)`", content))
    public_functions = {
        name
        for name in app.utils.__all__
        if inspect.isfunction(getattr(app.utils, name))
    }
    assert public_functions <= registered


def test_each_feature_has_one_standalone_usage_program_covering_public_calls() -> None:
    """Require one non-pytest program that calls every operation in each feature."""
    source_root = Path(app.utils.__file__).parent
    usage_root = source_root.parents[1] / "tests" / "utils" / "usage" / "features"
    usage_files = {
        path.name: path for path in usage_root.glob("[0-9][0-9]_*.py") if path.is_file()
    }
    assert set(usage_files) == set(_EXPECTED_USAGE_CALLS)
    for filename, expected_calls in _EXPECTED_USAGE_CALLS.items():
        tree = ast.parse(usage_files[filename].read_text(encoding="utf-8"))
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert expected_calls <= called_names
        assert not any(
            isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            for node in tree.body
        )
        assert any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in tree.body
        )
