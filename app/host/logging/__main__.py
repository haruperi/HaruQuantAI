"""Run `python -m app.host.logging --verify` after package migration."""

from __future__ import annotations

import sys

from .cli import TelemetryLoggerCLI

if __name__ == "__main__":
    raise SystemExit(TelemetryLoggerCLI.run_cli(sys.argv[1:]))
