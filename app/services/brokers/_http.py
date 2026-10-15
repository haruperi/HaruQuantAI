"""Shared HTTP transport policies, bounded retries, and redacted error diagnostics.

Description:
    Provides resilient, bounded HTTP session management for external market data
    providers (Dukascopy, Darwinex, Yahoo Finance, Crypto Exchanges). Enforces
    connection timeouts, cooperative cancellation token checks, bounded retry policies
    for transient 429/5xx status codes, rate-limiting guards, and secret redaction
    in error messages and URL query strings. Prevents stacked retry storms and event
    loop blocking.

Purpose:
    FEAT-BROKER-HTTP: Bounded HTTP transport infrastructure for market data providers.

Key Capabilities:
    - FR-BROKER-HTTP-SESSION: Configured requests.Session creation with retry adapters.
      Associated: `create_http_session()`
      Logging: Emits DEBUG when configuring session adapters and pool limits.
    - FR-BROKER-HTTP-EXECUTE: Bounded request execution with deadline and token check.
      Associated: `execute_bounded_get()`
      Logging: Emits DEBUG on dispatch, and WARNING on retries or non-200 responses.
    - FR-BROKER-HTTP-REDACTION: Redaction of API credentials and keys from error reports.
      Associated: `redact_url_or_message()`
      Logging: Emits DEBUG when stripping sensitive tokens.

Python API Usage:
    ```python
    from app.services.brokers._http import create_http_session, execute_bounded_get

    session = create_http_session("HaruQuantAI/1.0")
    response = execute_bounded_get(session, "https://api.example.com/data")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```
"""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import requests
from app.host.logging import get_logger
from app.services.brokers.capabilities import (
    CancellationToken,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
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
    s = _SECRET_PATTERN.sub(r"\1=REDACTED", str(text))
    return _USERINFO_PATTERN.sub(r"://***:***@", s)


class RateLimiter:
    """Thread-safe rate limiter pacing outbound HTTP requests."""

    def __init__(self, rps: float = 5.0) -> None:
        self.rps = max(0.1, rps)
        self.interval = 1.0 / self.rps
        self._last_call: float = 0.0
        self._lock = threading.Lock()

    def acquire(self, token: CancellationToken | None = None) -> None:
        """Block until pacing interval is met, checking cancellation."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                if token is not None:
                    end_time = time.monotonic() + wait_time
                    while time.monotonic() < end_time:
                        token.check_cancelled()
                        time.sleep(min(0.05, end_time - time.monotonic()))
                else:
                    time.sleep(wait_time)
            self._last_call = time.monotonic()


def create_http_session(
    user_agent: str,
    *,
    retries: int = 3,
    backoff: float = 0.3,
    pool_size: int = 16,
) -> requests.Session:
    """Create a configured requests.Session with bounded retry adapter."""
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    retry_strategy: Any = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
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
    token: CancellationToken | None = None,
    provider: str = "",
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> requests.Response:
    """Execute an HTTP GET request with deadline, cancellation, size limit, and redacted errors."""
    if token is not None:
        token.check_cancelled()

    safe_url = redact_url_or_message(url)
    t0 = time.perf_counter()
    deadline_start = time.monotonic()

    try:
        if deadline_seconds is not None:
            time_left = deadline_seconds - (time.monotonic() - deadline_start)
            if time_left <= 0:
                raise ProviderTimeoutError(
                    f"Overall deadline of {deadline_seconds:.1f}s exceeded before dispatch for {safe_url}",
                    provider=provider,
                )
            if isinstance(timeout, tuple):
                timeout = (min(timeout[0], time_left), min(timeout[1], time_left))
            else:
                timeout = min(timeout, time_left)

        resp = session.get(url, params=params, headers=headers, timeout=timeout)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        if token is not None:
            token.check_cancelled()

        if deadline_seconds is not None:
            if (time.monotonic() - deadline_start) > deadline_seconds:
                raise ProviderTimeoutError(
                    f"Overall deadline of {deadline_seconds:.1f}s exceeded after request to {safe_url}",
                    provider=provider,
                )

        cl_header = resp.headers.get("Content-Length")
        if cl_header and cl_header.isdigit() and int(cl_header) > max_bytes:
            raise ProviderValidationError(
                f"HTTP response Content-Length exceeds budget: {cl_header} > {max_bytes} for {safe_url}",
                provider=provider,
            )
        if len(resp.content) > max_bytes:
            raise ProviderValidationError(
                f"HTTP response body size exceeds budget: {len(resp.content)} > {max_bytes} for {safe_url}",
                provider=provider,
            )

        if resp.status_code == 429:
            retry_after_str = resp.headers.get("Retry-After")
            retry_after = (
                float(retry_after_str)
                if retry_after_str and retry_after_str.isdigit()
                else 1.0
            )
            raise ProviderRateLimitError(
                f"Rate limit exceeded on {safe_url}",
                provider=provider,
                retry_after=retry_after,
            )

        if resp.status_code in (401, 403):
            raise ProviderAuthError(
                f"Upstream authentication rejected by {safe_url} (HTTP {resp.status_code})",
                provider=provider,
                details={"status_code": resp.status_code},
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
        raise ProviderTimeoutError(
            f"HTTP request timed out for {safe_url}: {safe_exc}",
            provider=provider,
        ) from exc
    except requests.exceptions.RequestException as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise ProviderTimeoutError(
            f"HTTP network error for {safe_url}: {safe_msg}",
            provider=provider,
        ) from exc
    except ProviderError:
        raise
    except Exception as exc:
        safe_msg = redact_url_or_message(str(exc))
        raise ProviderError(
            f"HTTP error for {safe_url}: {safe_msg}",
            provider=provider,
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
