"""Bounded Network Retrieval for Declared Historical-Data Origins.

Description:
    This module provides secure, rate-limited, and origin-bounded network retrieval
    for historical market data feeds. It exists to prevent Server-Side Request
    Forgery (SSRF), redirect poisoning, credential leakage, and unbounded memory
    consumption from external endpoints. Externally, it participates in data
    acquisition workflows: `Composition` initializes `HistoricalNetwork` and injects
    it into data source plugins (such as `plugin.data_manager.dukascopy`) via the
    `NetworkAccess` capability facade. Data plugins invoke `get()` to download
    historical tick chunks, M1 bar data, and broker symbol specifications.
    Internally, `HistoricalNetwork` verifies URLs against frozen origin and scheme
    allowlists (`ALLOWED_ORIGIN_SCHEMES`), disables HTTP redirects, caps response
    payloads to 16 MB, injects standard desktop browser User-Agent headers, and applies
    a 3-attempt exponential backoff retry policy for 429/500/502/503/504 and
    transport errors. Exhausted transport has a typed NetworkUnavailableError;
    the provider decides whether to fall back or retain partial acquisition.

Purpose:
    FEAT-HOST-NETWORK: Bounded Allowlisted Historical Market Data Retrieval.
    Provides allowlisted domain and scheme validation, bounded response streaming,
    desktop user-agent injection, and exponential backoff retry policies for external
    historical market data providers.

Key Capabilities:
    - FR-HOST-NETWORK-ORIGIN-ALLOWLIST: Strict Origin and Scheme Verification
      Associated: `HistoricalNetwork.get()`
      Logging: Rejects non-allowlisted domains, schemes, credentials, or custom ports
      with explicit ValueError validation.
    - FR-HOST-NETWORK-BOUNDED-STREAMING: Size-Bounded Multi-Chunk Response Streaming
      Associated: `HistoricalNetwork.get()`, `NetworkResult`
      Logging: Emits info log on successful retrieval with byte length and
      raises ValueError when response exceeds the 16MB buffer bound.
    - FR-HOST-NETWORK-EXPONENTIAL-RETRY: Resilient Transient Error Retry Policy
      Associated: `HistoricalNetwork.get()`
      Logging: Emits warning log on rate limits (429), service unavailability
      (500/502/503/504), or transport errors before exponential sleep retry.

Python API Usage:
    ```python
    from app.host.network import HistoricalNetwork, NetworkResult

    # 1. Instantiate historical network client
    network = HistoricalNetwork()

    # 2. Fetch allowlisted market data file
    url = "https://datafeed.dukascopy.com/datafeed/EURUSD/2026/01/01/00h_ticks.bi5"
    result: NetworkResult = await network.get(url)

    if result.status == 200:
        raw_bytes = result.body
    ```

CLI Usage:
    Network retrieval capabilities are exercised through data manager CLI and
    plugin verification tests:
    ```bash
    # Test network retrieval and origin isolation
    uv run pytest tests/plugin/DataSource/test_dukascopy.py

    # Verify historical data acquisition offline runner
    uv run python tests/examples/dukascopy_offline.py
    ```
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import zipfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from tempfile import SpooledTemporaryFile
from typing import Any, BinaryIO, Literal, cast, override
from urllib.parse import urljoin, urlsplit

import httpx
from pydantic import Field, SecretStr

from app.host.contracts import Document
from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_SOURCE_REQUEST_SECONDS = 120
MAX_ARCHIVE_BYTES = 4 * 1024 * 1024 * 1024
MAX_ARCHIVE_MEMBER_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100000
LAST_ATTEMPT = 2
HTTP_OK = 200
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
ALLOWED_ORIGIN_SCHEMES: dict[str, tuple[str, ...]] = {
    "datafeed.dukascopy.com": ("http", "https"),
    "cdn.strategyquantcdn.com": ("https",),
    "cdn005.strategyquantcdn.com": ("https",),
}
ALLOWED_ORIGINS = frozenset(ALLOWED_ORIGIN_SCHEMES.keys())


class NetworkUnavailableError(ValueError):
    """A bounded public-data request exhausted its transport attempts."""


@dataclass(frozen=True)
class NetworkResult:
    """Bounded provider response without request credentials or raw diagnostics."""

    status: int
    body: bytes
    retry_after: str | None = None

    def json(self) -> Any:
        """Decode the bounded response body without exposing transport state."""
        return json.loads(self.body)


@dataclass(frozen=True)
class NetworkArchive:
    """Read-only ZIP member access without a filesystem destination."""

    _zip: zipfile.ZipFile

    def members(self) -> tuple[str, ...]:
        """Enumerate bounded archive names without extracting any paths."""
        entries = self._zip.infolist()
        if len(entries) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("Archive member count exceeds limit")
        return tuple(entry.filename for entry in entries if not entry.is_dir())

    def read(self, name: str) -> bytes:
        """Read one bounded member, verifying its ZIP checksum."""
        info = self._zip.getinfo(name)
        if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise ValueError("Archive member exceeds expanded size limit")
        with self._zip.open(info) as stream:
            result = stream.read(MAX_ARCHIVE_MEMBER_BYTES + 1)
        if len(result) > MAX_ARCHIVE_MEMBER_BYTES:
            raise ValueError("Archive member exceeds expanded size limit")
        logger.info("Historical archive member read: bytes=%d", len(result))
        return result


class SourceNetwork:
    """An owner-local cookie session restricted to explicitly declared origins."""

    def __init__(
        self, origins: tuple[str, ...], *, client: httpx.AsyncClient | None = None
    ) -> None:
        if not origins or any(
            not re.fullmatch(r"https://[a-z0-9.-]+", origin) for origin in origins
        ):
            raise ValueError("Historical source requires explicit HTTPS origins")
        self.origins = origins
        self.client = client
        self._auth: dict[str, httpx.BasicAuth] = {}
        self._redaction = SourceRequestRedaction()
        logging.getLogger("httpx").addFilter(self._redaction)

    def configure_basic_auth(self, origin: str, username: str, password: str) -> None:
        """Keep credentials in this session, scoped to one exact declared origin."""
        if origin not in self.origins or not username or not password:
            raise ValueError("Invalid source credential configuration")
        self._auth[origin] = httpx.BasicAuth(username, password)
        logger.info("Source authentication configured: origin=%s", origin)

    @property
    def authentication_configured(self) -> bool:
        """Expose presence only, without credential values or account identifiers."""
        return bool(self._auth)

    async def head(self, url: str) -> NetworkResult:
        """Probe source availability without downloading its archive body."""
        return await self._get(url, method="HEAD")

    def _validate(self, url: str) -> None:
        """Check every redirect before sending a request or forwarding cookies."""
        parsed = urlsplit(url)
        if (
            f"{parsed.scheme}://{parsed.netloc}" not in self.origins
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise ValueError("Source URL is outside its declared origins")

    async def get(
        self,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        request_seconds: float = 30,
    ) -> NetworkResult:
        """Retrieve bounded bytes; provider code owns its finite retry policy."""
        return await self._get(
            url, params=params, headers=headers, request_seconds=request_seconds
        )

    @asynccontextmanager
    async def archive(
        self, url: str, *, headers: dict[str, str] | None = None
    ) -> AsyncIterator[NetworkArchive]:
        """Spool a bounded archive under host custody and always dispose it."""
        with SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as stream:
            response = await self._get(
                url,
                headers=headers,
                request_seconds=120,
                sink=cast("BinaryIO", stream),
                max_bytes=MAX_ARCHIVE_BYTES,
            )
            if response.status != HTTP_OK:
                raise ValueError(f"Archive request failed: HTTP {response.status}")
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                result = NetworkArchive(archive)
                result.members()
                yield result

    async def _get(
        self,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
        request_seconds: float = 30,
        sink: BinaryIO | None = None,
        max_bytes: int = MAX_RESPONSE_BYTES,
        method: str = "GET",
    ) -> NetworkResult:
        """Validate transport boundaries before reading into host-owned storage."""
        if not 0 < request_seconds <= MAX_SOURCE_REQUEST_SECONDS:
            raise ValueError("Invalid source request timeout")
        self._validate(url)
        if self.client is None:
            self.client = httpx.AsyncClient(
                follow_redirects=False,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            )
        target = str(httpx.URL(url, params=params)) if params else url
        initial_origin = urlsplit(target).netloc
        for _ in range(6):
            self._validate(target)
            parsed = urlsplit(target)
            outgoing = dict(headers or {})
            if parsed.netloc != initial_origin:
                outgoing = {
                    key: value
                    for key, value in outgoing.items()
                    if key.lower()
                    not in ("authorization", "cookie", "proxy-authorization")
                }
            async with self.client.stream(
                method,
                target,
                headers=outgoing,
                auth=self._auth.get(f"{parsed.scheme}://{parsed.netloc}"),
                timeout=request_seconds,
                follow_redirects=False,
            ) as response:
                if response.is_redirect:
                    target = urljoin(target, response.headers.get("location", ""))
                    self._validate(target)
                    continue
                blocks: list[bytes] = []
                size = 0
                async for block in response.aiter_bytes():
                    size += len(block)
                    if size > max_bytes:
                        raise ValueError("Source response exceeds limit")
                    if sink is None:
                        blocks.append(block)
                    else:
                        sink.write(block)
                # Deliberately omit query strings, cookies and response content.
                logger.info(
                    "Historical source response: origin=%s status=%d bytes=%d",
                    urlsplit(target).hostname,
                    response.status_code,
                    size,
                )
                return NetworkResult(
                    response.status_code,
                    b"".join(blocks),
                    response.headers.get("retry-after"),
                )
        raise ValueError("Source redirect limit exceeded")

    async def close(self) -> None:
        """Dispose this owner's cookie and connection state."""
        self._auth.clear()
        if self.client is not None:
            await self.client.aclose()
            self.client = None
        logging.getLogger("httpx").removeFilter(self._redaction)


class SourceRequestRedaction(logging.Filter):
    """Strip HTTP query strings before third-party request records reach handlers.

    The host transport installs this filter for each source session's lifecycle.
    It adds no handlers and changes no logging levels.
    """

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        """Remove query credentials without retaining their raw formatted message."""
        record.msg = re.sub(
            r"(https?://[^\s?]+)\?[^\s]+", r"\1?[redacted]", record.getMessage()
        )
        record.args = ()
        return True


def _validate_origin_url(url: str) -> None:
    """Verify that URL matches allowlisted origin, scheme, port, and structure."""
    parsed = urlsplit(url)
    allowed_schemes = ALLOWED_ORIGIN_SCHEMES.get(parsed.hostname or "")
    if (
        allowed_schemes is None
        or parsed.scheme not in allowed_schemes
        or (parsed.scheme == "http" and parsed.port not in (None, 80))
        or (parsed.scheme == "https" and parsed.port not in (None, 443))
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Historical data URL is not allowlisted")


def _validate_redirect_url(url: str) -> None:
    """Verify that redirect destination URL matches allowlisted origin and scheme."""
    parsed = urlsplit(url)
    allowed_schemes = ALLOWED_ORIGIN_SCHEMES.get(parsed.hostname or "")
    if allowed_schemes is None or parsed.scheme not in allowed_schemes:
        raise ValueError("Historical data redirect URL is not allowlisted")


class SourceCredentials(Document):
    """Explicit owner/origin credentials supplied at host startup, never persisted."""

    owner: str
    origin: str = Field(pattern=r"^https://[a-z0-9.-]+$")
    username: SecretStr = Field(exclude=True, repr=False)
    password: SecretStr = Field(exclude=True, repr=False)


class HistoricalNetwork:
    """Fetch allowlisted public data with finite retry and body limits."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        credentials: tuple[SourceCredentials, ...] = (),
    ) -> None:
        self._client = client
        self._credentials = credentials
        self._sources: list[SourceNetwork] = []

    def source_session(
        self, origins: tuple[str, ...], *, owner: str = ""
    ) -> SourceNetwork:
        """Allocate a declared provider session, with host shutdown ownership."""
        session = SourceNetwork(origins)
        for credential in self._credentials:
            if credential.owner == owner and credential.origin in origins:
                session.configure_basic_auth(
                    credential.origin,
                    credential.username.get_secret_value(),
                    credential.password.get_secret_value(),
                )
        self._sources.append(session)
        return session

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(connect=10, read=30, write=10, pool=10)
            headers = {"User-Agent": DEFAULT_USER_AGENT}
            limits = httpx.Limits(max_connections=16, max_keepalive_connections=8)
            inst = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                limits=limits,
                headers=headers,
            )
            self._client = await inst.__aenter__()
        return self._client

    async def aclose(self) -> None:
        """Release underlying HTTP connection pool and resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        for source in self._sources:
            await source.close()
        self._sources.clear()
        self._credentials = ()

    @asynccontextmanager
    async def _stream_object(
        self,
        client: httpx.AsyncClient,
        url: str,
        method: Literal["GET", "HEAD"] = "GET",
    ) -> AsyncIterator[httpx.Response]:
        """Validate every redirect before contacting the next historical origin."""
        current = url
        for _ in range(7):
            async with client.stream(
                method, current, follow_redirects=False
            ) as response:
                if response.status_code not in (301, 302, 303, 307, 308):
                    yield response
                    return
                location = response.headers.get("location")
                if not location:
                    raise ValueError("Historical redirect lacks a destination")
                destination = urljoin(current, location)
                _validate_redirect_url(destination)
                current = destination
        raise ValueError("Historical redirect limit exceeded")

    async def get(self, url: str) -> NetworkResult:
        """Fetch a single provider object, following allowlisted origin redirects."""
        return await self._request(url)

    async def head(self, url: str) -> NetworkResult:
        """Probe an allowlisted source without downloading its body."""
        return await self._request(url, "HEAD")

    async def _request(
        self, url: str, method: Literal["GET", "HEAD"] = "GET"
    ) -> NetworkResult:
        _validate_origin_url(url)
        client = await self._ensure_client()
        for attempt in range(3):
            current_url = url
            try:
                async with self._stream_object(client, current_url, method) as response:
                    if response.history:
                        _validate_redirect_url(str(response.url))
                    if (
                        response.status_code in (429, 500, 502, 503, 504)
                        and attempt < LAST_ATTEMPT
                    ):
                        logger.warning(
                            "Historical network status %d from %s; "
                            "retrying in %ds (attempt %d/3)",
                            response.status_code,
                            url,
                            1 << attempt,
                            attempt + 1,
                        )
                        await asyncio.sleep(1 << attempt)
                        continue
                    if response.status_code != HTTP_OK:
                        logger.info(
                            "Historical network status %d from %s",
                            response.status_code,
                            url,
                        )
                        return NetworkResult(response.status_code, b"")
                    if method == "HEAD":
                        logger.info("Historical network probed %s", url)
                        return NetworkResult(response.status_code, b"")
                    blocks: list[bytes] = []
                    size = 0
                    async for block in response.aiter_bytes():
                        size += len(block)
                        if size > MAX_RESPONSE_BYTES:
                            raise ValueError("Historical data response exceeds limit")
                        blocks.append(block)
                    payload = b"".join(blocks)
                    logger.info(
                        "Historical network retrieved %s (%d bytes)",
                        url,
                        len(payload),
                    )
                    return NetworkResult(HTTP_OK, payload)
            except httpx.TransportError as error:
                logger.warning(
                    "Historical network transport error for %s on attempt %d/3: %s",
                    url,
                    attempt + 1,
                    type(error).__name__,
                )
                if attempt == LAST_ATTEMPT:
                    raise NetworkUnavailableError(
                        "Historical data transport unavailable"
                    ) from None
                await asyncio.sleep(1 << attempt)
        raise ValueError("Historical data retry limit exceeded")
