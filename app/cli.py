"""Synchronous CLI Host Client, Protocol Handshake, and Command Dispatcher.

Description:
    Provides a synchronous terminal client for communicating with a running
    HaruQuantAI universal backend host server, adhering to the same boot
    protocol, authentication workflow, and readiness milestones used by the web
    frontend.

    External relations and workflows:
    - Host transport: Connects to HTTP `/api/v1` routes (`/auth/login`,
      `/init-data`, `/app-loaded`, `/status`, `/commands/*`) and WebSocket
      `/ws/updates` provided by `app.host.transport`.
    - Host contracts: Validates incoming `BootSnapshot` payloads against
      `app.host.contracts.BootSnapshot` to ensure version compatibility and
      server operational readiness.
    - Operator CLI: Enables scriptable interactions, headless execution, CI
      smoke tests, and workspace command dispatch without requiring a browser.

    Internal coordination:
    - ClientError: Specific domain exception stopping client execution on
      transport, validation, or protocol failures.
    - Client: Encapsulates target host URL validation (enforcing HTTPS for
      remote endpoints), synchronous HTTP POST/GET methods with size limits,
      and WebSocket boot progress subscription.
    - _boot: Validates incoming boot snapshot dictionaries against schema version
      rules.
    - main: Parses command-line arguments, authenticates credentials, verifies
      server readiness, executes targeted workspace actions, and renders
      structured JSON or tabular output.

Purpose:
    FEAT-CLI-CLIENT: Synchronous terminal client for server authentication,
    boot progression validation, and remote workspace command mediation.

Key Capabilities:
    - FR-CLI-CLIENT-CONNECT: Enforces valid URL schemes, loopback policies, and
      authenticated HTTP request exchanges via Client.__init__() and
      Client.request().
      * Verified via: logger.info("CLI client authenticated for user: %s")
    - FR-CLI-CLIENT-HANDSHAKE: Connects to WebSocket /ws/updates, tracks boot
      progress snapshots, and signals client readiness via Client.initialize().
      * Verified via: logger.info("CLI client handshake completed successfully")
    - FR-CLI-CLIENT-COMMAND: Dispatches workspace commands and outputs JSON or
      tab-separated formatting to stdout via main().
      * Verified via: logger.info("CLI client command executed: action=%s")

Python API Usage:
    ```python
    from io import StringIO

    from app.cli import Client

    client = Client("http://127.0.0.1:8000")
    data = client.initialize("operator", "secret", output=StringIO())
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli --url http://127.0.0.1:8000 --page login
    ```
"""

import argparse
import json
import os
import sys
from collections.abc import Iterable
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
from app.host.sessions import is_loopback

logger = get_logger(__name__)
MAX_RESPONSE_BYTES = 1048576
BOOT_SCHEMA_VERSION = 2


def write_table_output(path: Path, frames: Iterable[Any]) -> int:  # noqa: C901, PLR0912 -- atomic multi-format export.
    """Export client-owned tabular results atomically, without host store access."""
    from tempfile import NamedTemporaryFile

    import pyarrow as pa  # type: ignore[import-untyped]
    import pyarrow.parquet as pq  # type: ignore[import-untyped]

    suffix = path.suffix.lower()
    if suffix not in (".csv", ".parquet", ".feather"):
        raise ClientError("Choose .csv, .parquet or .feather output")
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, suffix=suffix, delete=False) as stream:
        staged = Path(stream.name)
    writer = None
    count = 0
    feather: list[Any] = []
    feather_bytes = 0
    try:
        for frame in frames:
            if frame.empty:
                continue
            table = pa.Table.from_pandas(frame, preserve_index=False)
            if suffix == ".csv":
                frame.to_csv(staged, mode="a", index=False, header=count == 0)
            elif suffix == ".parquet":
                if writer is None:
                    writer = pq.ParquetWriter(staged, table.schema, compression="zstd")
                writer.write_table(table)
            else:
                feather_bytes += table.nbytes
                if feather_bytes > 128 * 1024 * 1024:
                    raise ClientError("Feather export exceeds client memory bounds")
                feather.append(table)
            count += len(frame)
        if writer is not None:
            writer.close()
            writer = None
        if not count:
            raise ClientError("No rows available for output")
        if suffix == ".feather":
            import pyarrow.feather as feather_io  # type: ignore[import-untyped]

            feather_io.write_feather(pa.concat_tables(feather), staged)
        staged.replace(path)
        logger.info("CLI exported rows=%d format=%s", count, suffix)
        return count
    finally:
        if writer is not None:
            writer.close()
        staged.unlink(missing_ok=True)


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
        logger.info("CLI client authenticated for user: %s", username)
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
            logger.info("CLI client handshake completed successfully")
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
            logger.info("CLI client command executed: action=%s", args.action)
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
