"""Import-safety verification for the Simulation package root."""

import os
import subprocess
import sys
from pathlib import Path


def test_package_root_import_has_no_external_or_mutating_side_effects() -> None:
    """Import in isolation with network, process, and write operations trapped."""
    repository_root = Path(__file__).parents[3]
    program = """
import asyncio
import os
import pathlib
import socket
import subprocess

def blocked(*args, **kwargs):
    raise AssertionError("prohibited import-time side effect")

socket.create_connection = blocked
socket.socket.connect = blocked
subprocess.Popen = blocked
os.putenv = blocked
original_open = pathlib.Path.open

def guarded_open(path, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        blocked()
    return original_open(path, mode, *args, **kwargs)

pathlib.Path.open = guarded_open
import app.services.simulator
"""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source
        [sys.executable, "-c", program],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
