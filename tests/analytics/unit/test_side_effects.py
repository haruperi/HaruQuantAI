"""Read-only side-effect boundary evidence for Analytics."""

# ruff: noqa: INP001
import builtins
import os
import socket
import subprocess

import pytest
from app.utils import logger
from tests.analytics._support import _report


def _unexpected(*_args: object, **_kwargs: object) -> None:
    """Fail when a prohibited side-effect primitive is invoked."""
    raise AssertionError("Analytics invoked a prohibited side-effect primitive")


def test_report_build_has_no_external_or_persistent_side_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Canonical report building performs no external or persistent side effect."""
    logger.info("Testing Analytics read-only side-effect boundary")
    environment_before = dict(os.environ)
    monkeypatch.setattr(builtins, "open", _unexpected)
    monkeypatch.setattr(socket, "socket", _unexpected)
    monkeypatch.setattr(subprocess, "run", _unexpected)
    report, _ = _report()
    assert report.non_binding is True
    assert dict(os.environ) == environment_before
