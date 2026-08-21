"""Unit tests for persistent state declarations and policies."""

import pytest

from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration


def test_state_declaration_valid() -> None:
    """Test valid StateDeclaration creation and defaults."""
    decl = StateDeclaration(
        namespace="data.historical_bars",
        schema_version=2,
        retention_policy=RetentionPolicy.RETAIN,
        description="Historical bars DuckDB store",
    )
    assert decl.namespace == "data.historical_bars"
    assert decl.schema_version == 2
    assert decl.retention_policy == RetentionPolicy.RETAIN
    assert decl.description == "Historical bars DuckDB store"


def test_state_declaration_invalid_namespace() -> None:
    """Test that empty or whitespace namespace raises ValueError."""
    with pytest.raises(ValueError, match="State namespace must not be empty"):
        StateDeclaration(namespace="")

    with pytest.raises(ValueError, match="State namespace must not be empty"):
        StateDeclaration(namespace="   ")


def test_state_declaration_invalid_version() -> None:
    """Test that schema_version < 1 raises ValueError."""
    with pytest.raises(ValueError, match="schema_version must be >= 1"):
        StateDeclaration(namespace="test.ns", schema_version=0)


def test_feature_spec_with_state() -> None:
    """Test FeatureSpec accepts and validates state declaration."""
    state = StateDeclaration(
        namespace="risk.limits",
        schema_version=1,
    )
    spec = FeatureSpec(
        feature_id="FEAT-RISK-CHECK_LIMITS",
        domain="risk",
        provides=frozenset(),
        state=state,
    )
    spec.validate()
    assert spec.state is not None
    assert spec.state.namespace == "risk.limits"
