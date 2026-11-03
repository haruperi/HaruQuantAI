"""Tests for ProgramRegistry implementation matching donor Program.java."""

from __future__ import annotations

import logging

import pytest
from app.core.lib.errors import DomainError, JSONValue
from app.core.lib.programs import (
    ProgramRegistry,
    default_program_registry,
    get,
    is_registered,
    register,
)


class FakeProgram:
    """Fake program implementing the Program protocol for testing."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[tuple[str, tuple[JSONValue, ...]]] = []

    def call(self, operation: str, *args: JSONValue) -> JSONValue:
        self.calls.append((operation, args))
        return None


def test_first_registration_wins(caplog: pytest.LogCaptureFixture) -> None:
    registry = ProgramRegistry()
    first = FakeProgram("first")
    second = FakeProgram("second")

    with caplog.at_level(logging.DEBUG):
        r1 = registry.register("x", first)
        r2 = registry.register("x", second)

    assert r1 is True
    assert r2 is False
    assert registry.get("x") is first

    # Check debug log for registration and error log for duplicate
    messages = [r.getMessage() for r in caplog.records]
    assert "Program 'x' was registered." in messages
    assert (
        "Duplicate registered program with name 'x', skipping second registration!"
        in messages
    )


def test_case_sensitive_and_instance_local() -> None:
    registry1 = ProgramRegistry()
    prog = FakeProgram("p")
    assert registry1.register("A", prog) is True

    assert registry1.is_registered("A") is True
    assert registry1.is_registered("a") is False

    registry2 = ProgramRegistry()
    assert registry2.is_registered("A") is False


def test_missing_program() -> None:
    registry = ProgramRegistry()
    with pytest.raises(DomainError) as exc_info:
        registry.get("missing")

    err = exc_info.value
    assert err.code == "PROGRAM_NOT_FOUND"
    assert err.message == "Program 'missing' doesn't exist"
    assert err.details == {"name": "missing"}


def test_module_level_helpers() -> None:
    prog = FakeProgram("global_p")
    assert register("global_p", prog) is True
    assert is_registered("global_p") is True
    assert get("global_p") is prog
    assert default_program_registry.is_registered("global_p") is True
