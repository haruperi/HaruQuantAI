"""Bounded read-only application release-feed capability.

Description:
    Validates a configured HTTPS release feed, performs one bounded read with
    deterministic client teardown and caches safe results for sixty seconds.
Purpose:
    FEAT-HOME-DASHBOARD: Application-owned release metadata retrieval.
Key Capabilities:
    - FR-HOME-UPDATES: ReleaseFeed.check() validates normal, unsupported and
      unavailable outcomes; Home.check_updates() verifies structured INFO logs.
      Provider failures emit WARNING without URLs, response bodies or secrets.
Python API Usage:
    from app.workspace.home._releases import ReleaseFeed
    result = ReleaseFeed(None).check("1.0.0")
CLI Usage:
    uv run python -m app.cli updates --json
"""

from __future__ import annotations

import asyncio
import re
import threading
import time
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx
from app.host.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = get_logger(__name__)
_MAX_BYTES = 256 * 1024
_BUDGET = 5.0
_INTERVAL = 60.0
_SPACE_CODEPOINT = 32


class ReleaseSource(Protocol):
    """Typed read-only provider consumed by Home."""

    def check(self, current_version: str) -> dict[str, Any]:
        """Return a safe release result for the host-reported version."""
        ...


class _Release(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    latest_version: str = Field(max_length=80)
    published_at: str = Field(max_length=80)
    changelog: str = Field(max_length=200_000)
    release_url: str = Field(max_length=2048)


def _https_url(value: str) -> str:
    """Require a credential-free HTTPS address without opaque query data."""
    url = urlsplit(value)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or any(ord(char) <= _SPACE_CODEPOINT for char in value)
    ):
        raise ValueError("Unsupported release address")
    _ = url.port
    return value


def _version(value: str) -> tuple[int, ...]:
    """Compare only the approved stable three-integer version contract."""
    if (
        re.fullmatch(
            r"(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})",
            value,
        )
        is None
    ):
        raise ValueError("Unsupported version format")
    return tuple(int(part) for part in value.split("."))


class ReleaseFeed:
    """Read-only release source with bounded admission and client ownership."""

    def __init__(
        self,
        url: str | None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url, self._transport, self._clock = url, transport, clock
        self._lock = threading.Lock()
        self._cached: dict[str, Any] | None = None
        self._next_check = 0.0

    def check(self, current_version: str) -> dict[str, Any]:
        """Return validated release data, or an explicit bounded failure state."""
        with self._lock:
            if self._cached is not None and self._clock() < self._next_check:
                return deepcopy(self._cached)
            result: dict[str, Any] = {
                "state": "unavailable",
                "reason": "No release feed configured.",
                "current_version": current_version,
                "latest_version": None,
                "update_available": None,
                "changelog": None,
                "release_url": None,
                "published_at": None,
                "checked_at": datetime.now(UTC).isoformat(),
            }
            if self._url is not None:
                self._populate(result, current_version)
            self._cached = result
            self._next_check = self._clock() + _INTERVAL
            return deepcopy(result)

    def _populate(self, result: dict[str, Any], current: str) -> None:
        try:
            current_parts = _version(current)
            url = _https_url(self._url or "")
            release = asyncio.run(self._fetch(url))
            _https_url(release.release_url)
            published = datetime.fromisoformat(release.published_at)
            if published.tzinfo is None:
                result.update(
                    state="unsupported", reason="Missing publication timezone."
                )
                return
            try:
                latest = _version(release.latest_version)
            except ValueError:
                result.update(
                    state="unsupported", reason="Unsupported release version format."
                )
                return
            result.update(release.model_dump())
            result.update(
                state="available",
                reason="Release feed checked.",
                update_available=latest > current_parts,
            )
        except ValueError:
            result.update(
                state="unsupported",
                reason="Unsupported release configuration or payload.",
            )
            logger.warning(
                "Unsupported release contract", extra={"fr_id": "FR-HOME-UPDATES"}
            )
        except httpx.HTTPError, TimeoutError, OSError:
            result.update(
                state="error",
                reason="Release provider could not be reached within its limits.",
            )
            logger.warning("Release request failed", extra={"fr_id": "FR-HOME-UPDATES"})

    async def _fetch(self, url: str) -> _Release:
        async with (
            asyncio.timeout(_BUDGET),
            httpx.AsyncClient(
                transport=self._transport,
                timeout=_BUDGET,
                follow_redirects=False,
                trust_env=False,
            ) as client,
            client.stream(
                "GET", url, headers={"Accept": "application/json"}
            ) as response,
        ):
            response.raise_for_status()
            body = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=8192):
                if len(body) + len(chunk) > _MAX_BYTES:
                    raise ValueError("Oversized release response")
                body.extend(chunk)
            try:
                return _Release.model_validate_json(body)
            except ValidationError as exc:
                raise ValueError("Invalid release response") from exc
