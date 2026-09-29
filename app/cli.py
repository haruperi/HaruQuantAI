"""Synchronous terminal client for the same host lifecycle used by the UI.

Client logs in over HTTP, authenticates the updates WebSocket in its first frame,
fetches initial state, and acknowledges readiness before commands. Credentials
remain in memory; progress goes to the caller's stream. main renders command
results to stdout and uses stderr for boot progress. No connection opens on import.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, TextIO
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from pydantic import ValidationError
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

from app.host.contracts import BootSnapshot
from app.host.logging import get_logger
from app.host.security import is_loopback

logger = get_logger(__name__)
MAX_RESPONSE_BYTES = 1048576
BOOT_SCHEMA_VERSION = 2


class ClientError(ValueError):
    """A typed host error or malformed response stopped client initialization."""


class Client:
    """Own a validated host URL and an in-memory bearer token.

    Requests are synchronous and bounded by response-size and network timeouts.
    The client shares backend authorization and readiness rules with the browser;
    it does not implement research algorithms or discover local providers.
    """

    def __init__(self, url: str) -> None:
        """Validate transport policy without making a network request.

        Plain HTTP is allowed for literal loopback hosts and localhost. Trailing
        slashes are removed and the initial token is empty.

        Args:
            url: HTTP(S) host base URL without embedded credentials.

        Raises:
            ClientError: URL is malformed or remote transport does not use HTTPS.
        """
        parts = urlsplit(url)
        if (
            parts.scheme not in ("http", "https")
            or not parts.hostname
            or parts.username
            or parts.password
        ):
            raise ClientError("Invalid host URL")
        if parts.scheme != "https" and not (
            is_loopback(parts.hostname) or parts.hostname == "localhost"
        ):
            raise ClientError("Remote clients require HTTPS")
        self.url = url.rstrip("/")
        self.token = ""

    def request(self, route: str, data: dict[str, Any] | None = None) -> Any:
        """Call a versioned host route and unwrap its success envelope.

        Uses a ten-second HTTP timeout. HTTP error bodies are read through the same
        size and envelope checks. Adds Authorization only when a token is present.

        Args:
            route: Route suffix beginning with / beneath /api/v1.
            data: JSON object for a POST, or None for GET.

        Returns:
            The envelope data value.

        Raises:
            ClientError: Response exceeds 1 MiB or is not a successful envelope.
            ValueError: Response JSON cannot be decoded.
            OSError: Transport I/O fails.
        """
        encoded = None if data is None else json.dumps(data).encode()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.url + "/api/v1" + route, data=encoded, headers=headers)  # noqa: S310 -- scheme validated at construction.
        try:
            with urlopen(request, timeout=10) as result:  # noqa: S310 -- only validated HTTP(S) hosts.
                raw = result.read(1048577)
        except HTTPError as error:
            raw = error.read(1048577)
            error.close()
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ClientError("Host response exceeds limit")
        payload = json.loads(raw)
        if (
            not isinstance(payload, dict)
            or payload.get("status") != "success"
            or "data" not in payload
        ):
            raise ClientError("Host rejected operation")
        return payload["data"]

    def initialize(
        self, username: str, password: str | None, *, output: TextIO
    ) -> dict[str, Any]:
        """Authenticate, validate host readiness and acknowledge this client.

        Credentials stay in memory and the first WebSocket frame. The connection
        has bounded timeouts and closes on failure or completion. Initial settings
        and catalog are returned; no restoration work is scheduled by the client.
        """
        payload: dict[str, Any] = {"username": username}
        if password is not None:
            payload["password"] = password
        self.token = self.request("/auth/login", payload)["token"]
        ws_url = (
            ("wss" if self.url.startswith("https:") else "ws")
            + self.url[self.url.index(":") :]
            + "/ws/updates"
        )
        with connect(
            ws_url, open_timeout=10, close_timeout=2, max_size=1048576, proxy=None
        ) as socket:
            socket.send(json.dumps({"token": self.token, "topics": ["boot.progress"]}))
            snapshot = json.loads(socket.recv(timeout=10))
            if snapshot.get("type") != "snapshot":
                raise ClientError("Host handshake rejected")
            self._boot(snapshot.get("boot"))
            initial: dict[str, Any] = self.request("/init-data")
            self._boot(initial.get("boot"))
            output.writelines(
                json.dumps(stage) + "\n" for stage in initial["boot"]["stages"]
            )
            self.request("/app-loaded", {})
            current = self._boot(self.request("/status").get("boot"))
            if current.state not in ("SERVER_READY", "DEGRADED"):
                raise ClientError("Host is not ready")
            return initial

    @staticmethod
    def _boot(value: Any) -> BootSnapshot:
        """Validate the versioned boot document before interpreting readiness."""
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != BOOT_SCHEMA_VERSION
        ):
            raise ClientError("Incompatible host boot schema; version 2 required")
        try:
            return BootSnapshot.model_validate(value)
        except ValidationError:
            raise ClientError("Invalid host boot snapshot") from None


def main(argv: list[str] | None = None) -> int:
    """Initialize the CLI and dispatch only an available workspace command.

    Password may come from HARU_CLIENT_PASSWORD. Login-only mode reports readiness;
    other pages require exactly one available catalog match. Results use stdout,
    progress uses stderr, and errors omit credential details. Argparse handles help
    and malformed command syntax with SystemExit.

    Args:
        argv: Arguments without program name; None reads process arguments.

    Returns:
        Zero on completion, one on handled transport/configuration failures.
    """
    parser = argparse.ArgumentParser(description="HaruQuantAI host client")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--page", default="login")
    parser.add_argument("--username", default="operator")
    parser.add_argument(
        "--password", help="Prefer HARU_CLIENT_PASSWORD to avoid shell history"
    )
    parser.add_argument("--action", default="")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args(argv)
    try:
        client = Client(args.url)
        initial = client.initialize(
            args.username,
            args.password or os.environ.get("HARU_CLIENT_PASSWORD"),
            output=sys.stderr,
        )
        if args.page != "login":
            candidates = [
                entry
                for entry in initial["catalog"]["domains"]
                if entry.get("route_base", "").rsplit("/", 1)[-1] == args.page
                and entry.get("available")
            ]
            if len(candidates) != 1:
                raise ClientError("Requested workspace provider is unavailable")
            payload = (
                json.loads(args.config.read_text(encoding="utf-8"))
                if args.config
                else {}
            )
            result = client.request("/commands/" + args.action, payload)
        else:
            result = {"ready": True, "catalog": initial["catalog"]}
        sys.stdout.write(
            json.dumps(result) + "\n"
            if not args.table
            else "\n".join(
                f"{key}\t{json.dumps(value)}" for key, value in result.items()
            )
            + "\n"
        )
    except OSError, ValueError, TimeoutError, WebSocketException:
        logger.error("CLI initialization or command failed")  # noqa: TRY400 -- credentials must not enter diagnostics.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
