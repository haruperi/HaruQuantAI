"""Resilient HTTP transport adapter, rate limiting, and credential redaction.

Description:
    Provides session configuration with retry backoff, bounded request execution,
    proactive rate limiting, and automated credential redaction for HTTP/CDN-based
    market data providers. Prevents leaking secrets or hanging network operations.

Purpose:
    FEAT-BROKER-HTTP: Hardened HTTP client infrastructure for external data vendors.

Key Capabilities:
    - FR-BROKER-HTTP-SESSION: Configure connection pooling and exponential retry backoff.
      Associated: `create_http_session()`.
      Logging: DEBUG session creation with retry policy metadata.
    - FR-BROKER-HTTP-EXECUTE: Bounded GET execution with timeout and size enforcement.
      Associated: `execute_bounded_get()`, `RateLimiter.acquire()`.
      Logging: DEBUG request latency and response code metrics.
    - FR-BROKER-HTTP-REDACTION: Sanitization of API keys and credentials in URLs and logs.
      Associated: `redact_url_or_message()`.
      Logging: Sanitized strings across all transport log events.

Python API Usage:
    ```python
    from app.services.brokers._http import create_http_session, execute_bounded_get

    session = create_http_session("MyApp/1.0")
    resp = execute_bounded_get(session, "https://example.com/data")
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers._http
    ```
"""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import requests
from app.host.logging import get_logger
from app.services.brokers.base import BridgeError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__name__)

SESSION_FR = "FR-BROKER-HTTP-SESSION"
EXECUTE_FR = "FR-BROKER-HTTP-EXECUTE"
REDACTION_FR = "FR-BROKER-HTTP-REDACTION"

MAX_RESPONSE_BYTES = 50 * 1024 * 1024  # 50 MB

__all__ = [
    "MAX_RESPONSE_BYTES",
    "RateLimiter",
    "create_http_session",
    "execute_bounded_get",
    "main",
    "redact_url_or_message",
]

_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|auth)=([^& \t\r\n]+)"
)
_USERINFO_PATTERN = re.compile(r"://([^:/@]+):([^@]+)@")


def redact_url_or_message(text: str) -> str:
    """Redact sensitive query parameters, credentials, and tokens from URLs and errors."""
    if not text:
        return ""
    s = _SECRET_PATTERN.sub(r"\1=REDACTED", text)
    return _USERINFO_PATTERN.sub(r"://***:***@", s)


class RateLimiter:
    """Thread-safe rate limiter pacing outbound HTTP requests."""

    def __init__(self, rps: float = 5.0) -> None:
        self.rps = max(0.1, rps)
        self.interval = 1.0 / self.rps
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until pacing interval is met."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self._last_call = time.monotonic()


def create_http_session(
    user_agent: str,
    *,
    retries: int = 3,
    backoff: float = 0.3,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
    pool_size: int = 10,
) -> requests.Session:
    """Create a hardened requests.Session configured with standard retries and timeouts."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
        }
    )

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logger.debug(
        "%s: Created requests.Session (retries=%d, backoff=%.2f, pool=%d)",
        SESSION_FR,
        retries,
        backoff,
        pool_size,
        extra={"fr_id": SESSION_FR, "retries": retries},
    )
    return session


def execute_bounded_get(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | tuple[float, float] = (5.0, 20.0),
    deadline_seconds: float | None = None,
    provider: str = "",
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> requests.Response:
    """Execute an HTTP GET request with deadline, size limit, and redacted errors."""
    del provider
    safe_url = redact_url_or_message(url)
    t0 = time.perf_counter()
    deadline_start = time.monotonic()

    try:
        if deadline_seconds is not None:
            time_left = deadline_seconds - (time.monotonic() - deadline_start)
            if time_left <= 0:
                raise BridgeError(
                    f"Overall deadline of {deadline_seconds:.1f}s exceeded before dispatch for {safe_url}",
                    code="TIMEOUT",
                )
            if isinstance(timeout, tuple):
                timeout = (min(timeout[0], time_left), min(timeout[1], time_left))
            else:
                timeout = min(timeout, time_left)

        resp = session.get(url, params=params, headers=headers, timeout=timeout)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if deadline_seconds is not None:
            if (time.monotonic() - deadline_start) > deadline_seconds:
                raise BridgeError(
                    f"Overall deadline of {deadline_seconds:.1f}s exceeded after request to {safe_url}",
                    code="TIMEOUT",
                )

        cl_header = resp.headers.get("Content-Length")
        if cl_header and cl_header.isdigit() and int(cl_header) > max_bytes:
            raise BridgeError(
                f"HTTP response Content-Length exceeds budget: {cl_header} > {max_bytes} for {safe_url}",
                code="DATA_LIMIT_EXCEEDED",
            )
        if len(resp.content) > max_bytes:
            raise BridgeError(
                f"HTTP response body size exceeds budget: {len(resp.content)} > {max_bytes} for {safe_url}",
                code="DATA_LIMIT_EXCEEDED",
            )

        if resp.status_code == 429:
            raise BridgeError(
                f"Rate limit exceeded on {safe_url}",
                code="RATE_LIMIT",
            )

        if resp.status_code in (401, 403):
            raise BridgeError(
                f"Upstream authentication rejected by {safe_url} (HTTP {resp.status_code})",
                code="AUTHENTICATION",
            )

        logger.debug(
            "%s: GET %s -> %d in %.1f ms",
            EXECUTE_FR,
            safe_url,
            resp.status_code,
            elapsed_ms,
            extra={
                "fr_id": EXECUTE_FR,
                "url": safe_url,
                "status_code": resp.status_code,
                "latency_ms": elapsed_ms,
            },
        )
        return resp
    except requests.exceptions.Timeout as exc:
        safe_exc = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP request timed out for {safe_url}: {safe_exc}",
            code="TIMEOUT",
        ) from exc
    except requests.exceptions.RequestException as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP network error for {safe_url}: {safe_msg}",
            code="TIMEOUT",
        ) from exc
    except BridgeError:
        raise
    except Exception as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise BridgeError(
            f"HTTP error for {safe_url}: {safe_msg}",
            code="BRIDGE_ERROR",
        ) from exc


def main() -> None:
    """CLI demonstration of bounded HTTP session and credential redaction."""
    print("=== HaruQuantAI Bounded HTTP Transport Demonstration ===")
    demo_url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&apiKey=dummy_demo_token_12345"
    redacted = redact_url_or_message(demo_url)
    print(f"Redaction demonstration:\n  Original: {demo_url}\n  Redacted: {redacted}")
    session = create_http_session("HaruQuantAI/1.0", retries=1)
    limiter = RateLimiter(rps=10.0)
    limiter.acquire()
    print("RateLimiter acquire succeeded.")
    session.close()
    print("HTTP transport validation passed.")


if __name__ == "__main__":
    main()
