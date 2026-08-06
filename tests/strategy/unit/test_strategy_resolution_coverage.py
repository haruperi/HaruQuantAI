"""Coverage expansion tests for strategy/registry/resolution.py."""

from unittest.mock import MagicMock, patch

import pytest
from app.services.data import build_data_error
from app.services.strategy import validate_strategy_ref
from app.services.strategy.contracts.enums import StrategyLifecycleStatus
from app.services.strategy.contracts.references import StrategyRef
from app.services.strategy.contracts.responses import StrategyOperationError
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.resolution import (
    _validate_record,
    _version_matches,
)
from app.utils import generate_id


def _ref(**overrides: object) -> StrategyRef:
    values: dict[str, object] = {
        "strategy_id": "str-123",
        "environment": "PAPER",
        "exact_version": "1.0.0",
        "request_id": generate_id("req"),
        "correlation_id": generate_id("cor"),
    }
    values.update(overrides)
    return StrategyRef(**values)  # type: ignore[arg-type]


def test_validate_strategy_ref_handles_data_error() -> None:
    """Verify validate_strategy_ref catches DataError and returns failure outcome."""
    ref = _ref()
    policy = MagicMock()

    with patch(
        "app.services.strategy.registry.resolution.read_strategy_versions",
        side_effect=build_data_error("DB_READ_FAILED"),
    ):
        res = validate_strategy_ref(ref, policy)
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == StrategyErrorCode.INTERNAL_ERROR.value


def test_version_matches_variations() -> None:
    """Verify _version_matches handles exact, wildcards, and equality constraints."""
    ref_exact = _ref(exact_version="1.0.0")
    assert _version_matches("1.0.0", ref_exact) is True
    assert _version_matches("2.0.0", ref_exact) is False

    ref_wildcard = _ref(exact_version=None, version_constraint="*")
    assert _version_matches("9.9.9", ref_wildcard) is True

    ref_eq = _ref(exact_version=None, version_constraint="==1.2.3")
    assert _version_matches("1.2.3", ref_eq) is True
    assert _version_matches("1.2.4", ref_eq) is False

    ref_plain = _ref(exact_version=None, version_constraint="1.2.3")
    assert _version_matches("1.2.3", ref_plain) is True


def test_validate_record_rejection_rules() -> None:
    """
    Verify _validate_record enforces lifecycle status, permitted environment, and module roots.
    """
    ref = _ref(environment="LIVE")
    policy = MagicMock(approved_module_roots=("app.strategies",))

    manifest = MagicMock()
    manifest.permitted_environments = ("PAPER",)  # 'LIVE' not permitted
    manifest.module_path = "app.strategies.my_strategy"

    # 1. Unapproved lifecycle
    with pytest.raises(StrategyOperationError) as lifecycle:
        _validate_record(manifest, StrategyLifecycleStatus.DRAFT, "hash", ref, policy)
    assert str(StrategyErrorCode.LIFECYCLE_NOT_APPROVED) in str(lifecycle.value)

    # 2. Environment not permitted
    with pytest.raises(StrategyOperationError) as environment:
        _validate_record(
            manifest, StrategyLifecycleStatus.APPROVED, "hash", ref, policy
        )
    assert str(StrategyErrorCode.ENVIRONMENT_NOT_PERMITTED) in str(environment.value)

    # 3. Unapproved module
    manifest.permitted_environments = ("LIVE",)
    manifest.module_path = "unapproved.module.path"
    with pytest.raises(StrategyOperationError) as module:
        _validate_record(
            manifest, StrategyLifecycleStatus.APPROVED, "hash", ref, policy
        )
    assert str(StrategyErrorCode.UNAPPROVED_MODULE) in str(module.value)


def test_validate_strategy_ref_search_results() -> None:
    """Verify validate_strategy_ref search result handling."""
    ref = _ref(exact_version="1.0.0")
    policy = MagicMock(approved_module_roots=("app.strategies",))

    # Empty rows -> NOT_FOUND
    with patch(
        "app.services.strategy.registry.resolution.read_strategy_versions",
        return_value=(),
    ):
        res_empty = validate_strategy_ref(ref, policy)
        assert res_empty.status == "error"
        assert res_empty.error is not None
        assert res_empty.error.code == StrategyErrorCode.NOT_FOUND.value

    # Non-matching rows -> VERSION_CONSTRAINT_UNSATISFIABLE
    mock_manifest = MagicMock()
    mock_manifest.strategy_version = "2.0.0"
    mock_row = {"manifest_json": '{"strategy_version": "2.0.0"}'}
    err_code = StrategyErrorCode.VERSION_CONSTRAINT_UNSATISFIABLE.value
    with (
        patch(
            "app.services.strategy.registry.resolution.read_strategy_versions",
            return_value=(mock_row,),
        ),
        patch(
            "app.services.strategy.contracts.manifest.StrategyManifest.model_validate_json",
            return_value=mock_manifest,
        ),
    ):
        res_mismatch = validate_strategy_ref(ref, policy)
        assert res_mismatch.status == "error"
        assert res_mismatch.error is not None
        assert res_mismatch.error.code == err_code
