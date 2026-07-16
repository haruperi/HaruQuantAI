import ast
import importlib
from pathlib import Path

import app.utils

_ROOT = Path(__file__).resolve().parents[3]


def test_utils_public_port_is_explicit_and_stage_scoped() -> None:
    expected = {
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
        "RuntimeSettings",
        "SecurityError",
        "StructuredFormatter",
        "SystemClock",
        "ValidationError",
        "age_seconds",
        "canonical_json",
        "configure_logging",
        "derive_stable_id",
        "flush_logging",
        "format_utc_timestamp",
        "generate_id",
        "get_error_metadata",
        "get_logger",
        "is_fresh",
        "logger",
        "map_exception",
        "normalize_error_code",
        "parse_utc_timestamp",
        "route_error_event",
        "shutdown_logging",
        "to_json_safe",
        "utc_now",
        "validate_id",
    }
    assert isinstance(app.utils.__all__, tuple)
    assert set(app.utils.__all__) == expected
    assert all(hasattr(app.utils, name) for name in expected)


def test_utils_contains_no_business_or_data_processing_dependencies() -> None:
    forbidden = {"pandas", "numpy", "MetaTrader5", "app.services"}
    for path in (_ROOT / "app" / "utils").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imported.update(
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert imported.isdisjoint(forbidden)


def test_every_feature_port_has_explicit_exports() -> None:
    for feature in (
        "contracts",
        "errors",
        "identity",
        "time",
        "serialization",
        "security",
        "settings",
        "logging",
    ):
        module = importlib.import_module(f"app.utils.{feature}")
        assert isinstance(module.__all__, tuple)
        assert len(module.__all__) == len(set(module.__all__))
