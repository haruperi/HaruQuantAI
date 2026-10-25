"""Headless HaruQuantAI commands; run `uv run python -m app.cli health`.

Commands use host services directly without importing the web entry point or
starting an HTTP server. Health emits a JSON StandardResponse on stdout and
returns exit code 0 when healthy, 1 on failure, or 2 for invalid CLI arguments.
Central logging writes operational messages separately from command output.
Use `login --username NAME` to prompt for a password and receive a token, then
set HARUQUANTAI_SESSION_TOKEN in the calling shell. Health validates and refreshes
that session when supplied; without a token it remains a public local probe.
Use `logout` to revoke the token. CLI sessions persist with peer_id="cli".
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import time
from collections.abc import Sequence
from typing import Any

from app.host.logging import get_logger, shutdown_logging
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.host.session import SessionManager
from app.host.settings import SettingsManager

logger = get_logger(__name__)
CLI_PEER_ID = "cli"
_TOKEN_ENV = "HARUQUANTAI_SESSION_TOKEN"  # noqa: S105 - environment variable name


def _result(
    operation: str,
    start: float,
    *,
    data: dict[str, Any] | None = None,
    error: ErrorCode | None = None,
) -> dict[str, Any]:
    metadata = ResponseMetadata(
        operation=operation, duration_ms=(time.perf_counter() - start) * 1000
    )
    if error is not None:
        message = (
            "Authentication required or credentials invalid"
            if error == ErrorCode.UNAUTHORIZED
            else "Session operation failed"
        )
        return StandardResponse.failure(
            message=message,
            error=StandardError(code=error, message=message),
            metadata=metadata,
        )
    return StandardResponse.success(
        message="Session operation completed", data=data, metadata=metadata
    )


def login(
    username: str, password: str, persistence: HostPersistence | None = None
) -> dict[str, Any]:
    """Verify configured credentials and issue a session bound to the CLI peer.

    The raw token is returned only at login. Retain it in the calling shell's
    HARUQUANTAI_SESSION_TOKEN environment variable for subsequent commands.
    """
    start = time.perf_counter()
    try:
        gateway = persistence if persistence is not None else HostPersistence()
        access = SettingsManager(gateway).get_scope("user_access")
        sessions = SessionManager(gateway)
        if not sessions.verify_credentials(
            username,
            password,
            expected_username=access["username"],
            password_hash=access["password_hash"],
        ):
            return _result("login", start, error=ErrorCode.UNAUTHORIZED)
        token = sessions.create_session(username, CLI_PEER_ID)
    except Exception:  # noqa: BLE001
        logger.error("CLI login failed")  # noqa: TRY400
        return _result("login", start, error=ErrorCode.UNAVAILABLE)
    logger.info("CLI login completed; peer_id=cli")
    return _result("login", start, data={"token": token, "peer_id": CLI_PEER_ID})


def logout(
    token: str | None, persistence: HostPersistence | None = None
) -> dict[str, Any]:
    """Revoke a CLI token without affecting UI sessions."""
    start = time.perf_counter()
    if token is None:
        return _result("logout", start, error=ErrorCode.UNAUTHORIZED)
    try:
        sessions = SessionManager(persistence)
        revoked = sessions.revoke_session(token, CLI_PEER_ID)
    except Exception:  # noqa: BLE001
        logger.error("CLI logout failed")  # noqa: TRY400
        return _result("logout", start, error=ErrorCode.UNAVAILABLE)
    if not revoked:
        return _result("logout", start, error=ErrorCode.UNAUTHORIZED)
    logger.info("CLI logout completed; peer_id=cli")
    return _result("logout", start, data={"revoked": True, "peer_id": CLI_PEER_ID})


def health(
    persistence: HostPersistence | None = None, *, token: str | None = None
) -> dict[str, Any]:
    """Check local settings and session storage without requiring a web server.

    Reading settings checks database availability and stored settings integrity.
    The session probe selects only session_id; no credentials or tokens are
    returned. This is a host readiness check, not a broker connectivity check.
    A supplied token must belong to the CLI peer and receives sliding expiry.
    """
    start = time.perf_counter()
    logger.info("Headless health check started")
    stage = "settings"
    try:
        gateway = persistence if persistence is not None else HostPersistence()
        SettingsManager(gateway).reload()
        stage = "session_storage"
        response = gateway.read_records("host_session", columns=["session_id"], limit=1)
        if not response["success"]:
            raise RuntimeError("Session storage is unavailable")  # noqa: TRY301
        if token is not None:
            stage = "session"
            if SessionManager(gateway).validate_session(token, CLI_PEER_ID) is None:
                return _result("health", start, error=ErrorCode.UNAUTHORIZED)
    except Exception:  # noqa: BLE001
        # This CLI boundary must report failed readiness without exposing secrets
        # in database errors, settings values, or exception tracebacks.
        logger.error("Headless health check failed; check=%s", stage)  # noqa: TRY400
        return StandardResponse.failure(
            message="Host health check failed",
            error=StandardError(
                code=ErrorCode.UNAVAILABLE,
                message="Host health check failed",
                details={"check": stage},
            ),
            metadata=ResponseMetadata(
                operation="health", duration_ms=(time.perf_counter() - start) * 1000
            ),
        )
    logger.info("Headless health check passed")
    return StandardResponse.success(
        message="Host is healthy",
        data={"status": "ok", "checks": {"settings": "ok", "session_storage": "ok"}},
        metadata=ResponseMetadata(
            operation="health", duration_ms=(time.perf_counter() - start) * 1000
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse headless commands, emit their result, and drain central logging."""
    try:
        parser = argparse.ArgumentParser(description="HaruQuantAI headless CLI")
        commands = parser.add_subparsers(dest="command", required=True)
        commands.add_parser("health", help="Check local host settings and storage")
        login_parser = commands.add_parser("login", help="Authenticate a CLI session")
        login_parser.add_argument("--username", required=True)
        commands.add_parser("logout", help="Revoke the current CLI session")
        arguments = parser.parse_args(argv)
        token = os.environ.get(_TOKEN_ENV)
        if arguments.command == "login":
            try:
                password = getpass.getpass("Password: ")
            except EOFError, KeyboardInterrupt:
                logger.warning("CLI login cancelled")
                return 1
            result = login(arguments.username, password)
        elif arguments.command == "logout":
            result = logout(token)
        else:
            result = health(token=token) if token is not None else health()
        print(json.dumps(result, allow_nan=False))
        return 0 if result["success"] else 1
    finally:
        shutdown_logging()


if __name__ == "__main__":
    raise SystemExit(main())
