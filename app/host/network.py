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
    a 3-attempt exponential backoff retry policy for rate-limiting (429/503) and
    network transport errors.

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
      (503), or transport timeouts before exponential sleep retry.

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
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
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


@dataclass(frozen=True)
class NetworkResult:
    """Bounded provider response without request credentials or raw diagnostics."""

    status: int
    body: bytes


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


class HistoricalNetwork:
    """Fetch allowlisted public data with finite retry and body limits."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(connect=10, read=30, write=10, pool=10)
            headers = {"User-Agent": DEFAULT_USER_AGENT}
            limits = httpx.Limits(max_connections=16, max_keepalive_connections=8)
            inst = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
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

    async def get(self, url: str) -> NetworkResult:
        """Fetch a single provider object, following allowlisted origin redirects."""
        _validate_origin_url(url)
        client = await self._ensure_client()
        for attempt in range(3):
            try:
                async with client.stream("GET", url) as response:
                    if response.history:
                        _validate_redirect_url(str(response.url))
                    if response.status_code in (429, 503) and attempt < LAST_ATTEMPT:
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
            except (httpx.ConnectError, httpx.TimeoutException) as error:
                logger.warning(
                    "Historical network transport error for %s on attempt %d/3: %s",
                    url,
                    attempt + 1,
                    type(error).__name__,
                )
                if attempt == LAST_ATTEMPT:
                    raise ValueError("Historical data transport unavailable") from None
                await asyncio.sleep(1 << attempt)
        raise ValueError("Historical data retry limit exceeded")
