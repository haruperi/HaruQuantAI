"""Bounded HTTPS Retrieval for Declared Historical-Data Origins.

Description:
    This module provides secure, rate-limited, and origin-bounded HTTPS retrieval
    for historical market data feeds. It exists to prevent Server-Side Request
    Forgery (SSRF), redirect poisoning, credential leakage, and unbounded memory
    consumption from external endpoints. Externally, it participates in data
    acquisition workflows: `Composition` initializes `HistoricalNetwork` and injects
    it into data source plugins (such as `plugin.data_manager.dukascopy`) via the
    `NetworkAccess` capability facade. Data plugins invoke `get()` to download
    historical tick chunks, M1 bar data, and broker symbol specifications.
    Internally, `HistoricalNetwork` verifies URLs against a frozen host allowlist
    (`ALLOWED_ORIGINS`), disables HTTP redirects, caps response payloads to 16 MB,
    and applies a 3-attempt exponential backoff retry policy for rate-limiting
    (429/503) and network socket timeouts.

Purpose:
    FEAT-HOST-NETWORK: Bounded Allowlisted Historical HTTPS Retrieval.
    Provides allowlisted domain validation, bounded response streaming, and
    exponential backoff retry policies for external historical market data providers.

Key Capabilities:
    - FR-HOST-NETWORK-ORIGIN-ALLOWLIST: Strict Origin Allowlist Verification
      Associated: `HistoricalNetwork.get()`
      Logging: Rejects non-allowlisted domains, credentials, or custom ports
      with explicit ValueError validation.
    - FR-HOST-NETWORK-BOUNDED-STREAMING: Size-Bounded Response Streaming
      Associated: `HistoricalNetwork.get()`, `NetworkResult`
      Logging: Emits debug log on successful retrieval with byte length and
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
ALLOWED_ORIGINS = frozenset(
    {
        "datafeed.dukascopy.com",
        "cdn.strategyquantcdn.com",
        "cdn005.strategyquantcdn.com",
    }
)


@dataclass(frozen=True)
class NetworkResult:
    """Bounded provider response without request credentials or raw diagnostics."""

    status: int
    body: bytes


class HistoricalNetwork:
    """Fetch allowlisted public data with finite retry and body limits."""

    async def get(self, url: str) -> NetworkResult:
        """Fetch a single provider object, rejecting redirects and unsafe origins."""
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in ALLOWED_ORIGINS
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Historical data URL is not allowlisted")
        timeout = httpx.Timeout(connect=5, read=15, write=5, pool=5)
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=3, max_keepalive_connections=1),
        ) as client:
            for attempt in range(3):
                try:
                    async with client.stream("GET", url) as response:
                        if (
                            response.status_code in (429, 503)
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
                        blocks: list[bytes] = []
                        size = 0
                        async for block in response.aiter_bytes():
                            size += len(block)
                            if size > MAX_RESPONSE_BYTES:
                                raise ValueError(
                                    "Historical data response exceeds limit"
                                )
                            blocks.append(block)
                            payload = b"".join(blocks)
                            logger.info(
                                "Historical network retrieved %s (%d bytes)",
                                url,
                                len(payload),
                            )
                            return NetworkResult(HTTP_OK, payload)
                except (httpx.ConnectError, httpx.ReadTimeout) as error:
                    logger.warning(
                        "Historical network transport error for %s on attempt %d/3: %s",
                        url,
                        attempt + 1,
                        type(error).__name__,
                    )
                    if attempt == LAST_ATTEMPT:
                        raise ValueError(
                            "Historical data transport unavailable"
                        ) from None
                    await asyncio.sleep(1 << attempt)
        raise ValueError("Historical data retry limit exceeded")
