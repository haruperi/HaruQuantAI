"""Validated client-side shell mediation and confined text-file exchange.

open_link and copy_text validate values that the browser or CLI client acts on;
this module does not open a browser or write the system clipboard. ExchangeFiles
provides bounded UTF-8 file operations under its injected root, resolving paths
before containment checks. Bootstrap supplies data/exchange by default.

HTTP adapters translate CommandError into a generic 422 COMMAND_REJECTED
envelope. These file operations do not interpret strategies or access domain
storage. Path validation is not a security sandbox against concurrent hostile
filesystem changes; callers must control the exchange directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib.parse import urlsplit

from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_TEXT_BYTES = 8 * 1024
MAX_LIST_ENTRIES = 4096
MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_LINK_SCHEMES = ("http", "https")


class CommandError(Exception):
    """Signal rejected command input or a wrapped exchange-file failure.

    The HTTP guard emits a generic COMMAND_REJECTED response rather than exposing
    raw filesystem exception text. Direct callers may inspect the exception but
    must avoid forwarding sensitive path details into public diagnostics.
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
        """Resolve an exchange-relative path and enforce current containment.

        Resolution follows file links before confinement checks. This does not reserve
        the path against concurrent replacement by another filesystem actor.

        Args:
            relative: Relative path without a drive, colon, or parent traversal
                component.

        Returns:
            Resolved path inside the configured root; existence is not required.

        Raises:
            CommandError: The path is absolute, contains forbidden components, or
                resolves outside root.
        """
        candidate = Path(relative)
        if (
            candidate.is_absolute()
            or candidate.drive
            or ":" in relative
            or ".." in candidate.parts
        ):
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
        with NamedTemporaryFile(
            mode="w", dir=target.parent, encoding="utf-8", delete=False
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(content)
        try:
            temp_path.replace(target)
        finally:
            temp_path.unlink(missing_ok=True)
        logger.info("Exchange file written")
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
        """List regular files beneath an exchange-relative directory.

        Args:
            prefix: Jail-relative directory path (empty for root); files are not
                prefix-matched.

        Returns:
            List of dicts with ``path`` (relative), ``size_bytes``,
            and ``modified_at`` (UTC ISO 8601 string). A missing or non-directory
            prefix returns an empty list; enumeration order is not guaranteed.

        Raises:
            CommandError: If ``prefix`` escapes the jail or the listing exceeds
                MAX_LIST_ENTRIES.
            OSError: Filesystem enumeration or metadata access fails.
        """
        target_dir = self._resolve(prefix) if prefix else self.root.resolve()
        if not target_dir.is_dir():
            return []
        results: list[dict[str, Any]] = []
        root_resolved = self.root.resolve()
        for path in target_dir.rglob("*", recurse_symlinks=False):
            if len(results) >= MAX_LIST_ENTRIES:
                raise CommandError("File listing exceeds limit")
            if path.is_file() and path.resolve().is_relative_to(root_resolved):
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
            logger.info("Exchange file deleted")
            return True
        except OSError as err:
            raise CommandError(f"Cannot delete file: {err}") from err
