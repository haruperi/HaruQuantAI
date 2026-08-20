"""Unit tests for stateful provider manifest validation, retention policies, and schema constraints.

Traces to: P8-T01, Gate G8
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.kernel.errors import ManifestValidationError
from app.kernel.manifests import (
    DowngradePolicy,
    load_manifest,
)


def _write_manifest(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "manifest.toml"
    p.write_text(content.strip(), encoding="utf-8")
    return p


_VALID_STATEFUL_MANIFEST = """
[provider]
id = "trading.order_execution.default"
version = "2.1.0"
entry_point = "app.services.trading.order_execution.plugin:create_provider"

[[provides]]
capability_id = "trading.order_execution.v2"
contract_version = "2.1.0"
cardinality = "one_of_several"

[runtime]
profiles = ["live"]
scopes = ["tenant"]
effect_classes = ["durable_compensatable", "irreversible_external"]
lifecycle = "scoped"
reload = "process_restart"

[state]
schema_id = "trading_orders"
schema_version = "2.0.0"
migration_manifest = "schema:trading.orders.v2"
compatible_prior_majors = [1, 2]
downgrade_policy = "reject"
uninstall_retention = "retain"
purge_requires_authorization = true
"""


def test_valid_stateful_manifest_parsed_correctly(tmp_path: Path) -> None:
    """Verify happy-path loading of a compliant stateful provider manifest."""
    manifest_path = _write_manifest(tmp_path, _VALID_STATEFUL_MANIFEST)
    manifest = load_manifest(manifest_path)

    assert manifest.state_schema_id == "trading_orders"
    assert str(manifest.state_schema_version) == "2.0.0"
    assert manifest.migration_manifest == "schema:trading.orders.v2"
    assert manifest.compatible_state_majors == (1, 2)
    assert manifest.downgrade_policy == DowngradePolicy.REJECT
    assert manifest.uninstall_retention == "retain"
    assert manifest.purge_requires_authorization is True


def test_stateful_manifest_missing_required_key_fails_closed(tmp_path: Path) -> None:
    """Verify state table missing any required field raises ManifestValidationError."""
    content = """
[provider]
id = "trading.orders.default"
version = "1.0.0"
entry_point = "mod:factory"

[runtime]
profiles = ["live"]
scopes = ["tenant"]
effect_classes = ["durable_compensatable"]
lifecycle = "scoped"
reload = "process_restart"

[state]
schema_id = "trading_orders"
schema_version = "1.0.0"
# missing migration_manifest, compatible_prior_majors, etc.
"""
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match="state fields must be all present or all absent"
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_invalid_schema_id_fails_closed(tmp_path: Path) -> None:
    """Verify non-conforming schema_id syntax raises ManifestValidationError."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        'schema_id = "trading_orders"', 'schema_id = "123_invalid_start"'
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match=r"invalid schema_id '123_invalid_start'"
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_schema_id_starting_with_app_fails_closed(
    tmp_path: Path,
) -> None:
    """Verify schema_id starting with 'app.' is rejected."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        'schema_id = "trading_orders"', 'schema_id = "app.orders"'
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match=r"invalid schema_id 'app.orders'"
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_migration_manifest_as_python_class_path_fails_closed(
    tmp_path: Path,
) -> None:
    """Verify migration_manifest referencing a Python class path fails closed."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        'migration_manifest = "schema:trading.orders.v2"',
        'migration_manifest = "app.services.trading.migrations:orders_v2"',
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"migration_manifest cannot be a Python class path",
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_invalid_downgrade_policy_fails_closed(
    tmp_path: Path,
) -> None:
    """Verify unsupported downgrade_policy value raises ManifestValidationError."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        'downgrade_policy = "reject"', 'downgrade_policy = "auto_migrate"'
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError, match=r"invalid downgrade_policy 'auto_migrate'"
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_drop_retention_fails_closed(tmp_path: Path) -> None:
    """Verify uninstall_retention = 'drop' fails closed with explicit message."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        'uninstall_retention = "retain"', 'uninstall_retention = "drop"'
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"stateful provider must retain data and require purge authorization",
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_purge_authorization_false_fails_closed(
    tmp_path: Path,
) -> None:
    """Verify purge_requires_authorization = false fails closed with explicit message."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        "purge_requires_authorization = true", "purge_requires_authorization = false"
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"stateful provider must retain data and require purge authorization",
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_non_positive_prior_majors_fails_closed(
    tmp_path: Path,
) -> None:
    """Verify non-positive compatible prior major versions raise ManifestValidationError."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        "compatible_prior_majors = [1, 2]", "compatible_prior_majors = [0, 1]"
    )
    manifest_path = _write_manifest(tmp_path, content)
    with pytest.raises(
        ManifestValidationError,
        match=r"compatible_prior_majors must contain positive integers",
    ):
        load_manifest(manifest_path)


def test_stateful_manifest_prior_majors_normalized_and_sorted(tmp_path: Path) -> None:
    """Verify prior major integers are deduplicated and sorted ascending."""
    content = _VALID_STATEFUL_MANIFEST.replace(
        "compatible_prior_majors = [1, 2]", "compatible_prior_majors = [3, 1, 2, 1]"
    )
    manifest_path = _write_manifest(tmp_path, content)
    manifest = load_manifest(manifest_path)
    assert manifest.compatible_state_majors == (1, 2, 3)
