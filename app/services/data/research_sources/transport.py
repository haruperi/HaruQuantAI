"""Bounded allowlisted transport for research providers."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.services.data.contracts.errors import DataError
from app.utils import get_logger, utc_now

logger = get_logger(__name__)
_ATTEMPTS: dict[str, deque[datetime]] = defaultdict(deque)
_FAILURES: dict[str, int] = defaultdict(int)
_CIRCUIT_UNTIL: dict[str, datetime] = {}
_CIRCUIT_FAILURE_THRESHOLD = 3


def retrieve_research_provider_payload(
    provider: str,
    source_url: str,
    *,
    allowed_hosts: tuple[str, ...],
    user_agent: str,
    headers: Mapping[str, str] | None = None,
    allowed_content_types: tuple[str, ...] = (
        "application/json",
        "application/xml",
        "application/rss+xml",
        "text/xml",
    ),
    timeout_seconds: float = 10.0,
    max_bytes: int = 1_048_576,
    rate_limit: int = 5,
    rate_window_seconds: float = 1.0,
    now: datetime | None = None,
) -> bytes:
    """Retrieve one bounded provider response under fail-closed governance.

    Args:
        provider: Stable provider identifier.
        source_url: HTTPS provider URL.
        allowed_hosts: Exact approved provider hosts.
        user_agent: Non-secret identifying user agent.
        headers: Optional request headers; values are never logged or persisted.
        allowed_content_types: Approved response MIME prefixes.
        timeout_seconds: Socket timeout.
        max_bytes: Maximum accepted response bytes.
        rate_limit: Maximum calls in the declared window.
        rate_window_seconds: Sliding rate-limit window.
        now: Testable current instant.

    Returns:
        Bounded response bytes.

    Raises:
        DataError: If policy, rate, circuit, transport, or size validation fails.
    """
    observed_at = now or utc_now()
    parsed = urlsplit(source_url)
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or host not in allowed_hosts
        or not provider.strip()
        or not user_agent.strip()
        or timeout_seconds <= 0
        or max_bytes <= 0
        or rate_limit <= 0
        or rate_window_seconds <= 0
        or not allowed_content_types
    ):
        raise DataError("INVALID_INPUT", safe_details={"field": "provider_transport"})
    circuit_until = _CIRCUIT_UNTIL.get(provider)
    if circuit_until is not None and observed_at < circuit_until:
        raise DataError("CIRCUIT_BREAKER_OPEN", safe_details={"source_id": provider})
    attempts = _ATTEMPTS[provider]
    threshold = observed_at - timedelta(seconds=rate_window_seconds)
    while attempts and attempts[0] <= threshold:
        attempts.popleft()
    if len(attempts) >= rate_limit:
        raise DataError("LIMIT_EXCEEDED", safe_details={"source_id": provider})
    attempts.append(observed_at)
    request_headers = {"User-Agent": user_agent, "Accept": "application/json"}
    request_headers.update(dict(headers or {}))
    request = Request(source_url, headers=request_headers, method="GET")  # noqa: S310
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            final_host = (urlsplit(response.geturl()).hostname or "").lower()
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if final_host not in allowed_hosts or not any(
                content_type.startswith(value) for value in allowed_content_types
            ):
                raise DataError(
                    "INVALID_INPUT",
                    safe_details={"field": "provider_response"},
                )
            payload = bytes(response.read(max_bytes + 1))
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        _FAILURES[provider] += 1
        if _FAILURES[provider] >= _CIRCUIT_FAILURE_THRESHOLD:
            _CIRCUIT_UNTIL[provider] = observed_at + timedelta(seconds=30)
        logger.warning("Research provider retrieval failed for source_id=%s", provider)
        raise DataError(
            "SOURCE_UNAVAILABLE", safe_details={"source_id": provider}
        ) from error
    _FAILURES[provider] = 0
    if len(payload) > max_bytes:
        raise DataError("LIMIT_EXCEEDED", safe_details={"field": "source_payload"})
    return payload


__all__ = ("retrieve_research_provider_payload",)
