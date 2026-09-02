"""Unit tests for persistent state declarations and policies."""

import pytest
from app.kernel.feature import FeatureSpec
from app.kernel.state import (
    RetentionPolicy,
    StateDeclaration,
    attempt_transition,
    build_transition_table,
)


def test_state_declaration_valid() -> None:
    """Test valid StateDeclaration creation and defaults."""
    decl = StateDeclaration(
        namespace="test.retained-state",
        schema_version=2,
        retention_policy=RetentionPolicy.RETAIN,
        description="Test retained state",
    )
    assert decl.namespace == "test.retained-state"
    assert decl.schema_version == 2
    assert decl.retention_policy == RetentionPolicy.RETAIN
    assert decl.description == "Test retained state"


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


def test_transition_table_and_attempts() -> None:
    """Test transition table construction and attempt_transition execution."""
    transitions = [
        ("CREATED", "START", "RUNNING"),
        ("RUNNING", "PAUSE", "PAUSED"),
        ("PAUSED", "RESUME", "RUNNING"),
        ("RUNNING", "STOP", "STOPPED"),
    ]
    table = build_transition_table(transitions)
    assert table[("CREATED", "START")] == "RUNNING"

    # Successful transitions
    ok, next_state = attempt_transition("CREATED", "START", table)
    assert ok is True
    assert next_state == "RUNNING"

    ok, next_state = attempt_transition("RUNNING", "STOP", table)
    assert ok is True
    assert next_state == "STOPPED"

    # Invalid transitions stay in current state
    ok, next_state = attempt_transition("STOPPED", "RESUME", table)
    assert ok is False
    assert next_state == "STOPPED"
