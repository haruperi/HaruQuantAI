"""B01 process entrypoint for the staged backend host boot sequence."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError

from app.host.config import (
    HostConfigurationError,
    HostSettings,
    load_host_settings,
)
from app.host.logging import get_logger

__all__ = [
    "HostConfigurationError",
    "LaunchOptions",
    "effective_settings",
    "main",
    "parse_launch_args",
]

logger = get_logger(__name__)

MAX_PORT = 65535


@dataclass(frozen=True, slots=True)
class LaunchOptions:
    """Validated process arguments for the later host boot stages."""

    host: str
    port: int
    data_dir: Path
    explicit_fields: frozenset[str] = field(default_factory=frozenset, compare=False)


def _host_value(value: str) -> str:
    """Reject an empty host while preserving a valid address or hostname."""
    host = value.strip()
    if not host:
        raise argparse.ArgumentTypeError("host must not be empty")
    return host


def _port_value(value: str) -> int:
    """Parse a TCP port in the valid 1-65535 range."""
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= MAX_PORT:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _data_dir_value(value: str) -> Path:
    """Reject a blank data directory without resolving or creating it."""
    if not value.strip():
        raise argparse.ArgumentTypeError("data directory must not be empty")
    return Path(value)


def parse_launch_args(argv: Sequence[str] | None = None) -> LaunchOptions:
    """Parse and validate B01 arguments without starting other boot stages."""
    parser = argparse.ArgumentParser(description="Start the HaruQuantAI backend host")
    parser.add_argument(
        "--host", type=_host_value, default=argparse.SUPPRESS, metavar="HOST"
    )
    parser.add_argument(
        "--port", type=_port_value, default=argparse.SUPPRESS, metavar="PORT"
    )
    parser.add_argument(
        "--data-dir", type=_data_dir_value, default=argparse.SUPPRESS, metavar="PATH"
    )
    parsed = vars(parser.parse_args(argv))
    return LaunchOptions(
        host=parsed.get("host", "127.0.0.1"),
        port=parsed.get("port", 8000),
        data_dir=parsed.get("data_dir", Path("data")),
        explicit_fields=frozenset(parsed),
    )


def effective_settings(options: LaunchOptions) -> HostSettings:
    """Resolve B02 settings from stored records and explicit CLI values.

    Precedence is model defaults, stored app.general fields, then explicit
    command-line values. A missing database is a fresh-install default
    case. Records come only from the database; the command line can never
    inject them.
    """
    if options.data_dir.exists() and not options.data_dir.is_dir():
        raise HostConfigurationError("Data directory path is not a directory")
    base = load_host_settings(data_dir=options.data_dir)
    if not options.explicit_fields:
        return base
    cli_overrides = {name: getattr(options, name) for name in options.explicit_fields}
    current_values = base.model_dump(mode="python")
    current_values.update(cli_overrides)
    try:
        return HostSettings.model_validate(current_values)
    except ValidationError:
        raise HostConfigurationError("Invalid host runtime settings") from None


def main(argv: Sequence[str] | None = None) -> NoReturn:
    """Run B01-B02, then fail until the remaining bootstrap is implemented."""
    options = parse_launch_args(argv)
    logger.info("B01 App booting initiated")
    try:
        settings = effective_settings(options)
    except HostConfigurationError as error:
        logger.error(  # noqa: TRY400 -- tracebacks can expose settings.
            "B02 Runtime configuration failed: %s", error
        )
        raise SystemExit(f"Host runtime configuration failed: {error}") from None
    except OSError:
        logger.error(  # noqa: TRY400 -- tracebacks can expose paths.
            "B02 Host logging initialization failed"
        )
        raise SystemExit("Host logging initialization failed") from None
    logger.info(
        "B02 Runtime configuration loaded: host=%s port=%d gpu_accelerated=%s",
        json.dumps(settings.host),
        settings.port,
        settings.gpu_accelerated,
    )
    raise SystemExit("Host bootstrap stages B03-B05 are not implemented yet")


if __name__ == "__main__":
    main()
