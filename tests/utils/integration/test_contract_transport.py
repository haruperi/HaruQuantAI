"""Producer-side compatibility tests for Utils v1 mappings."""

import inspect

import app.utils
import pytest
from app.utils.errors.exceptions import ValidationError


def test_package_exports_only_functions() -> None:
    """Every package-root export remains a standalone function."""
    assert all(
        inspect.isfunction(getattr(app.utils, name)) for name in app.utils.__all__
    )


def test_reference_versions_fail_closed() -> None:
    """Unknown reference versions are rejected rather than defaulted."""
    value = app.utils.build_version_ref(
        artifact_kind="scenario",
        artifact_id="scn-1",
        version="1",
        content_hash="a" * 64,
    )
    value["contract_version"] = "v2"
    with pytest.raises(ValidationError):
        app.utils.parse_version_ref(value)
