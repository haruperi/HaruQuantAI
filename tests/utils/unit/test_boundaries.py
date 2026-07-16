import ast
import re
from decimal import getcontext
from pathlib import Path

import app.utils

_EXPECTED_EXPORTS = {
    "AppSettings",
    "AuditEvent",
    "AuthContext",
    "BoundLogger",
    "Clock",
    "ConfigurationError",
    "ErrorMetadata",
    "ErrorSink",
    "ExternalServiceError",
    "HaruQuantError",
    "LoggingSettings",
    "RedactingFilter",
    "RedactionPolicy",
    "RedactionResult",
    "RuntimeSettings",
    "SecurityError",
    "SecretVersion",
    "StructuredFormatter",
    "SystemClock",
    "ValidationError",
    "age_seconds",
    "canonical_json",
    "configure_logging",
    "derive_stable_id",
    "decrypt_text",
    "encrypt_text",
    "flush_logging",
    "format_utc_timestamp",
    "generate_id",
    "generate_fernet_key",
    "get_error_metadata",
    "get_logger",
    "hash_password",
    "is_fresh",
    "is_sensitive_key",
    "load_settings",
    "logger",
    "map_exception",
    "normalize_error_code",
    "parse_utc_timestamp",
    "redact_mapping_value",
    "redact_text_value",
    "resolve_secret_reference",
    "route_error_event",
    "select_active_secret_version",
    "shutdown_logging",
    "to_json_safe",
    "utc_now",
    "validate_id",
    "verify_password",
}
_FORBIDDEN_IMPORT_ROOTS = {
    "app.services",
    "pandas",
    "sqlite3",
}


def test_public_surface_contains_only_documented_exports() -> None:
    assert set(app.utils.__all__) == _EXPECTED_EXPORTS


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
    assert completed == {f"{number:03d}" for number in range(1, 42)}
    for line in requirement_lines:
        assert "**Usage:**" in line
        assert "**Unit:**" in line
        for relative_path in re.findall(r"`(tests/utils/[^`:]+\.py)::", line):
            assert (repository_root / relative_path).is_file()
