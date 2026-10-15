"""Pytest fixtures and autouse network isolation guard for broker unit tests.

Description:
    Enforces the zero-unmocked-external-HTTP requirement by intercepting
    socket connections at test runtime. Any attempt to reach an external host
    outside of loopback (localhost/127.0.0.1) raises a RuntimeError.

Purpose:
    FEAT-TEST-GUARD: Hermetic unit test execution without external network leaks.
"""

from __future__ import annotations

import socket
from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def block_external_network() -> Generator[None]:
    """Guard against unmocked external network connections in broker tests."""
    orig_connect = socket.socket.connect

    def guarded_connect(self: socket.socket, address: tuple[str, int] | str) -> None:
        host = address[0] if isinstance(address, tuple) else str(address)
        if host in ("localhost", "127.0.0.1", "::1"):
            orig_connect(self, address)
            return
        raise RuntimeError(
            f"Blocked unmocked network connection attempt to {address} during unit tests."
        )

    with patch.object(socket.socket, "connect", guarded_connect):
        yield
