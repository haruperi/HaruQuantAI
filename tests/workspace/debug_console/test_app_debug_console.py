"""Unit tests for the Debug Console workspace service, models, and events.

Description:
    Tests DebugConsoleService, DebugEventPublisher ring buffer, plugin descriptors,
    case-sensitive filtering, and non-silent requirement logging.

Purpose:
    FEAT-DEBUG-CONSOLE: Verify backend service, events, and model parity.
"""

import logging

import pytest
from app.workspace.debug_console.app_debug_console import DebugConsoleService
from app.workspace.debug_console.app_debug_console_models import (
    DebugConsolePluginDescriptor,
    DebugFilterModel,
    DebugLogEntryModel,
)
from app.workspace.debug_console.events import DebugEventPublisher


def test_debug_console_plugin_descriptor(caplog: pytest.LogCaptureFixture) -> None:
    """Verify plugin descriptor metadata matches donor specification."""
    with caplog.at_level(logging.INFO):
        service = DebugConsoleService()
        descriptor = service.get_plugin_descriptor()

    assert descriptor.name == "DebugConsole"
    assert descriptor.app_code == "DEBUGCONSOLE"
    assert descriptor.category == "App"
    assert descriptor.product == "SQUANT"
    assert descriptor.preferred_position == 1
    assert descriptor.context_path == "/debugconsole"
    assert descriptor.tooltip == "DebugConsole"
    assert descriptor.hidden is False
    assert descriptor.only_in_pro is True
    assert "FR-DEBUG-CONSOLE-PLUGIN-REGISTRATION" in caplog.text


def test_debug_event_publisher_ring_buffer(caplog: pytest.LogCaptureFixture) -> None:
    """Verify ring buffer bounds and FIFO eviction behavior."""
    publisher = DebugEventPublisher(max_entries=3)

    with caplog.at_level(logging.INFO):
        e1 = publisher.emit("System", "Message 1", "10:00:00")
        e2 = publisher.emit("Engine", "Message 2", "10:00:01")
        e3 = publisher.emit("Jobs", "Message 3", "10:00:02")

    assert publisher.size() == 3
    assert e1.category == "System"
    assert e2.category == "Engine"
    assert e3.category == "Jobs"
    assert "FR-DEBUG-CONSOLE-EVENTS" in caplog.text

    # Default time generation branch coverage
    default_entry = publisher.emit("Clock", "Default time")
    assert len(default_entry.time) > 0

    # Emit 4th entry to trigger eviction of 1st
    publisher.emit("Network", "Message 4", "10:00:03")
    assert publisher.size() == 3
    entries = publisher.get_entries()
    assert [e.category for e in entries] == ["Jobs", "Clock", "Network"]

    # Test limit parameter
    assert len(publisher.get_entries(limit=2)) == 2
    assert [e.category for e in publisher.get_entries(limit=2)] == ["Clock", "Network"]


def test_debug_event_publisher_filtering() -> None:
    """Verify case-sensitive text matching and exact category filtering."""
    publisher = DebugEventPublisher()
    publisher.emit("Engine", "Order dispatched successfully", "12:00:00")
    publisher.emit("Engine", "order failed validation", "12:00:01")
    publisher.emit("Jobs", "Order queued", "12:00:02")

    # Case-sensitive text filtering
    f1 = publisher.filter_entries(DebugFilterModel(category="all", text="Order"))
    assert len(f1) == 2
    assert [e.message for e in f1] == [
        "Order dispatched successfully",
        "Order queued",
    ]

    f2 = publisher.filter_entries(DebugFilterModel(category="all", text="order"))
    assert len(f2) == 1
    assert f2[0].message == "order failed validation"

    # Category filtering
    f3 = publisher.filter_entries(DebugFilterModel(category="Jobs", text=""))
    assert len(f3) == 1
    assert f3[0].category == "Jobs"

    # Combined category and text filtering
    f4 = publisher.filter_entries(DebugFilterModel(category="Engine", text="Order"))
    assert len(f4) == 1
    assert f4[0].category == "Engine"

    # Clear buffer
    publisher.clear()
    assert publisher.size() == 0


def test_debug_console_service_methods(caplog: pytest.LogCaptureFixture) -> None:
    """Verify service delegation to publisher and non-silent logging."""
    service = DebugConsoleService()

    with caplog.at_level(logging.INFO):
        service.log("App", "User signed in", "08:00:00")
        batch = service.get_events()
        assert batch.total_count == 1
        assert batch.events[0].message == "User signed in"

        filtered = service.filter_events(DebugFilterModel(category="App", text="User"))
        assert filtered.total_count == 1

        service.clear()
        assert service.get_events().total_count == 0

    assert "FR-DEBUG-CONSOLE-SERVICE" in caplog.text


def test_debug_console_models_validation() -> None:
    """Verify model instantiation and default fields."""
    entry = DebugLogEntryModel(time="12:00:00", category="Core", message="Ready")
    assert entry.time == "12:00:00"
    assert entry.category == "Core"
    assert entry.message == "Ready"

    filter_def = DebugFilterModel()
    assert filter_def.category == "all"
    assert filter_def.text == ""

    custom_desc = DebugConsolePluginDescriptor(name="CustomDebug")
    assert custom_desc.name == "CustomDebug"
    assert custom_desc.app_code == "DEBUGCONSOLE"
