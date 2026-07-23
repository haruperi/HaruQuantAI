import ast
import inspect
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
    "StructuredFormatter",
    "SystemClock",
    "ValidationError",
    "age_seconds",
    "canonical_digest",
    "canonical_json",
    "configure_logging",
    "derive_stable_id",
    "flush_logging",
    "format_utc_timestamp",
    "generate_id",
    "get_error_metadata",
    "get_logger",
    "is_fresh",
    "is_sensitive_key",
    "load_settings",
    "logger",
    "map_exception",
    "normalize_error_code",
    "parse_utc_timestamp",
    "redact_mapping_value",
    "redact_text_value",
    "route_error_event",
    "shutdown_logging",
    "to_json_safe",
    "utc_now",
    "validate_id",
}
_FORBIDDEN_IMPORT_ROOTS = {
    "app.services",
    "pandas",
    "sqlite3",
}
_EXPECTED_USAGE_CALLS = {
    "01_contracts.py": {"AuditEvent", "AuthContext"},
    "02_errors.py": {
        "get_error_metadata",
        "map_exception",
        "normalize_error_code",
        "route_error_event",
    },
    "03_identity.py": {"derive_stable_id", "generate_id", "validate_id"},
    "04_time.py": {
        "age_seconds",
        "format_utc_timestamp",
        "is_fresh",
        "parse_utc_timestamp",
        "utc_now",
    },
    "05_serialization.py": {"canonical_digest", "canonical_json", "to_json_safe"},
    "06_security.py": {
        "is_sensitive_key",
        "redact_mapping_value",
        "redact_text_value",
    },
    "07_settings.py": {"load_settings"},
    "08_logging.py": {
        "configure_logging",
        "flush_logging",
        "get_logger",
        "shutdown_logging",
    },
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


def test_no_consumer_imports_or_mutates_utils_internals() -> None:
    """Keep every consumer on the documented package and feature exports."""
    source_root = Path(app.utils.__file__).parent
    repository_root = source_root.parents[1]
    offenders: list[str] = []
    for scope in ("app", "tests"):
        for source_file in (repository_root / scope).rglob("*.py"):
            if source_root in source_file.parents or source_file == source_root:
                continue
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            relative = source_file.relative_to(repository_root).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    offenders.extend(
                        f"{relative}:{node.lineno} imports {alias.name}"
                        for alias in node.names
                        if alias.name.count(".") > 2
                        and alias.name.startswith("app.utils.")
                    )
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and node.module.count(".") > 2
                    and node.module.startswith("app.utils.")
                ):
                    offenders.append(
                        f"{relative}:{node.lineno} imports from {node.module}"
                    )
                elif isinstance(node, ast.Assign):
                    offenders.extend(
                        f"{relative}:{node.lineno} assigns {target.attr}"
                        for target in node.targets
                        if isinstance(target, ast.Attribute)
                        and target.attr.startswith("_")
                        and "app.utils" in ast.unparse(target.value)
                    )
    assert not offenders, "\n" + "\n".join(offenders)


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
        *(f"{number:03d}" for number in range(1, 25)),
        *(f"{number:03d}" for number in range(26, 36)),
        *(f"{number:03d}" for number in range(39, 42)),
    }
    for line in requirement_lines:
        assert "**Usage:**" in line
        assert "**Unit:**" in line
        for relative_path in re.findall(r"`(tests/utils/[^`:]+\.py)::", line):
            assert (repository_root / relative_path).is_file()


def test_features_register_contains_every_public_function() -> None:
    """Require the Utils register to name every public exported function."""
    source_root = Path(app.utils.__file__).parent
    register_path = source_root.parents[1] / "docs" / "CHANGELOG.md"
    content = register_path.read_text(encoding="utf-8")
    utils_part = content.split("# Utils", 1)[1] if "# Utils" in content else ""
    utils_section = utils_part.split("\n# ", 1)[0]
    registered = set(re.findall(r"\| `([a-z][a-z0-9_]*)\(", utils_section))
    public_functions = {
        name
        for name in app.utils.__all__
        if inspect.isfunction(getattr(app.utils, name))
    }
    assert registered == public_functions


def test_each_feature_has_one_standalone_usage_program_covering_public_calls() -> None:
    """Require one non-pytest program that calls every operation in each feature."""
    source_root = Path(app.utils.__file__).parent
    usage_root = source_root.parents[1] / "tests" / "utils" / "usage"
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
