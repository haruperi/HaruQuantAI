"""Validated client-side OS mediation and sandboxed file exchange.

SQX's backend owns the desktop, so its shell can open browsers and dialogs
itself (ledger SQX144-EV-000007). Our UI is a web satellite, so the host
instead *validates and audits* while the client *acts*: ``open-link``
accepts only http/https URLs (blocking ``javascript:``/``file:`` schemes),
``copy`` carries length-capped text, and file exchange is jailed to one
root (``data/exchange`` by default) with fail-closed traversal checks and
size caps — the future import/export lane between host and UI.

Rejected inputs return ``422 COMMAND_REJECTED`` envelopes carrying a
structured issue; nothing here executes OS actions server-side.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.host.envelope import (
    ValidationIssue,
    error_payload,
    success_payload,
)
from app.host.http import envelope_response, read_json_body, request_id_of

MAX_TEXT_BYTES = 8 * 1024
MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_LINK_SCHEMES = ("http", "https")


class CommandError(Exception):
    """Raised when a command input fails validation.

    Endpoints convert this into a ``422 COMMAND_REJECTED`` envelope with the
    message as a structured issue.
    """


def open_link(url: str) -> str:
    """Validate ``url`` as an openable http/https link and return it.

    Args:
        url: Candidate URL supplied by the client.

    Returns:
        The same URL when it carries an allowed scheme and a host.

    Raises:
        CommandError: When the scheme is not http/https or the host is
            empty.
    """
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_LINK_SCHEMES or not parts.netloc:
        raise CommandError("Only http/https URLs with a host can be opened")
    return url


def copy_text(text: str) -> str:
    """Validate length-capped copy text and return it.

    Args:
        text: Text the client intends to place on its clipboard.

    Returns:
        The same text when within the byte cap.

    Raises:
        CommandError: When the UTF-8 encoded text exceeds
            ``MAX_TEXT_BYTES``.
    """
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise CommandError(f"Copy text exceeds {MAX_TEXT_BYTES} bytes")
    return text


@dataclass(frozen=True)
class ExchangeFiles:
    """Read/write file access jailed to one root directory.

    The jail is enforced by construction: every path is resolved against
    ``root`` and must land inside it (checked after resolution, so symlinks
    and ``..`` segments cannot smuggle paths out). Subdirectories are
    created on write; reads of missing files fail closed.
    """

    root: Path

    def _resolve(self, relative: str) -> Path:
        """Resolve ``relative`` inside the jail or raise ``CommandError``."""
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise CommandError(
                "Path must be relative and stay inside the exchange root"
            )
        resolved = (self.root / candidate).resolve()
        root_resolved = self.root.resolve()
        if resolved != root_resolved and root_resolved not in resolved.parents:
            raise CommandError("Path escapes the exchange root")
        return resolved

    def read(self, relative: str) -> str:
        """Read a UTF-8 text file inside the jail.

        Args:
            relative: Jail-relative path of the file.

        Returns:
            The file's text content.

        Raises:
            CommandError: If the path escapes the jail, the file is missing,
                it exceeds ``MAX_FILE_BYTES``, or it cannot be decoded.
        """
        target = self._resolve(relative)
        if not target.is_file():
            raise CommandError("File does not exist in the exchange root")
        if target.stat().st_size > MAX_FILE_BYTES:
            raise CommandError(f"File exceeds {MAX_FILE_BYTES} bytes")
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            raise CommandError(f"Cannot read file: {err}") from err

    def write(self, relative: str, content: str) -> int:
        """Atomically write a UTF-8 text file inside the jail.

        Args:
            relative: Jail-relative destination path (parents created).
            content: Text to write.

        Returns:
            The number of UTF-8 bytes written.

        Raises:
            CommandError: If the content exceeds ``MAX_FILE_BYTES`` or the
                path escapes the jail.
        """
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise CommandError(f"Content exceeds {MAX_FILE_BYTES} bytes")
        target = self._resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target.with_suffix(target.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        Path(temp_path).replace(target)
        return len(content.encode("utf-8"))

    def exists(self, relative: str) -> dict[str, Any]:
        """Check whether a file exists inside the jail.

        Args:
            relative: Jail-relative candidate path.

        Returns:
            Dict with ``exists`` (bool) and ``size_bytes`` (int | None).

        Raises:
            CommandError: If the path escapes the exchange jail.
        """
        target = self._resolve(relative)
        if target.is_file():
            return {"exists": True, "size_bytes": target.stat().st_size}
        return {"exists": False, "size_bytes": None}

    def list_files(self, prefix: str = "") -> list[dict[str, Any]]:
        """List files inside the jail matching or under ``prefix``.

        Args:
            prefix: Jail-relative directory or prefix path (empty for root).

        Returns:
            List of dicts with ``path`` (relative), ``size_bytes``,
            and ``modified_at`` (ISO 8601 string).

        Raises:
            CommandError: If ``prefix`` escapes the jail.
        """
        target_dir = self._resolve(prefix) if prefix else self.root.resolve()
        if not target_dir.is_dir():
            return []
        results: list[dict[str, Any]] = []
        root_resolved = self.root.resolve()
        for path in sorted(target_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root_resolved).as_posix()
                st = path.stat()
                results.append(
                    {
                        "path": rel,
                        "size_bytes": st.st_size,
                        "modified_at": datetime.fromtimestamp(
                            st.st_mtime, tz=UTC
                        ).isoformat(),
                    }
                )
        return results

    def delete(self, relative: str) -> bool:
        """Delete a file inside the jail if present (idempotent).

        Args:
            relative: Jail-relative path.

        Returns:
            ``True`` if the file existed and was removed, ``False`` if
            missing.

        Raises:
            CommandError: If the path escapes the jail or deletion fails.
        """
        target = self._resolve(relative)
        if not target.exists():
            return False
        if not target.is_file():
            raise CommandError("Path is not a regular file")
        try:
            target.unlink()
            return True
        except OSError as err:
            raise CommandError(f"Cannot delete file: {err}") from err


def _command_error_response(request_id: str, err: CommandError) -> JSONResponse:
    issue = ValidationIssue(path="body", code="invalid", message=str(err))
    return envelope_response(
        request_id,
        error_payload(request_id, "COMMAND_REJECTED", str(err), [issue]),
        status_code=422,
    )


async def open_link_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/commands/open-link`` {url}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    url = body.get("url")
    if not isinstance(url, str):
        return _command_error_response(
            request_id, CommandError("Body must carry a string 'url'")
        )
    try:
        validated = open_link(url)
    except CommandError as err:
        return _command_error_response(request_id, err)
    logger = request.app.state.logger
    logger.info("Open-link requested (request %s): %s", request_id, validated)
    return envelope_response(
        request_id, success_payload(request_id, {"url": validated})
    )


async def copy_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/commands/copy`` {text}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    text = body.get("text")
    if not isinstance(text, str):
        return _command_error_response(
            request_id, CommandError("Body must carry a string 'text'")
        )
    try:
        validated = copy_text(text)
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id, success_payload(request_id, {"text": validated})
    )


async def files_read_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/files/read`` {path}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    path = body.get("path")
    if not isinstance(path, str):
        return _command_error_response(
            request_id, CommandError("Body must carry a string 'path'")
        )
    exchange: ExchangeFiles = request.app.state.services.exchange
    try:
        content = exchange.read(path)
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id, success_payload(request_id, {"path": path, "content": content})
    )


async def files_write_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/files/write`` {path, content}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    path = body.get("path")
    content = body.get("content")
    if not isinstance(path, str) or not isinstance(content, str):
        return _command_error_response(
            request_id, CommandError("Body must carry string 'path' and 'content'")
        )
    exchange: ExchangeFiles = request.app.state.services.exchange
    try:
        written = exchange.write(path, content)
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id,
        success_payload(request_id, {"path": path, "written": True, "bytes": written}),
    )


async def files_exists_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/files/exists`` {path}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    path = body.get("path")
    if not isinstance(path, str):
        return _command_error_response(
            request_id, CommandError("Body must carry a string 'path'")
        )
    exchange: ExchangeFiles = request.app.state.services.exchange
    try:
        res = exchange.exists(path)
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id, success_payload(request_id, {"path": path, **res})
    )


async def files_list_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/files/list`` {prefix?}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    prefix = body.get("prefix", "")
    if prefix is not None and not isinstance(prefix, str):
        return _command_error_response(
            request_id, CommandError("Optional 'prefix' must be a string")
        )
    exchange: ExchangeFiles = request.app.state.services.exchange
    try:
        files = exchange.list_files(prefix or "")
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id, success_payload(request_id, {"files": files, "count": len(files)})
    )


async def files_delete_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/files/delete`` {path}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    path = body.get("path")
    if not isinstance(path, str):
        return _command_error_response(
            request_id, CommandError("Body must carry a string 'path'")
        )
    exchange: ExchangeFiles = request.app.state.services.exchange
    try:
        deleted = exchange.delete(path)
    except CommandError as err:
        return _command_error_response(request_id, err)
    return envelope_response(
        request_id, success_payload(request_id, {"path": path, "deleted": deleted})
    )
