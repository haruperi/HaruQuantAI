"""Periodic liveness heartbeat emission to external watchdog nodes.

This module implements:
- Dead man's switch liveness heartbeat emission (TRD-FR-175)
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from app.services.trading.state.ports import Clock
from loguru import logger


class HeartbeatEmitter:
    """Emits periodic liveness heartbeats to an external watchdog URL."""

    def __init__(
        self,
        watchdog_url: str,
        clock: Clock,
        extra_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the heartbeat emitter.

        Args:
            watchdog_url: Target URL for POST requests.
            clock: Injected clock source.
            extra_metadata: Optional additional metadata fields.
        """
        self._watchdog_url = watchdog_url
        self._clock = clock
        self._extra_metadata = extra_metadata or {}
        self._last_heartbeat_time: datetime | None = None
        self._last_success = False

    def send_heartbeat(self, status: str = "HEALTHY") -> bool:
        """Send a liveness heartbeat payload to the external watchdog node.

        Payload contains timestamp, status, and metadata details.

        Args:
            status: Status indicator string.

        Returns:
            bool: True if heartbeat successfully sent, False otherwise.
        """
        now = self._clock.now_utc()
        payload = {
            "timestamp": now.isoformat(),
            "status": status,
            "metadata": self._extra_metadata,
        }

        logger.debug(
            "Emitting liveness heartbeat to {} with status: {}",
            self._watchdog_url,
            status,
        )

        if not (
            self._watchdog_url.startswith("http://")
            or self._watchdog_url.startswith("https://")
        ):
            logger.warning(
                "Invalid watchdog URL scheme: {}. Heartbeat not sent.",
                self._watchdog_url,
            )
            self._last_success = False
            return False

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(  # noqa: S310
                self._watchdog_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # Short timeout to avoid blocking execution threads
            with urllib.request.urlopen(req, timeout=2.0) as response:  # noqa: S310
                if response.status in (200, 201, 202, 204):
                    self._last_heartbeat_time = now
                    self._last_success = True
                    return True
                logger.warning(
                    "Watchdog responded with status code: {}",
                    response.status,
                )
                self._last_success = False
                return False
        except (urllib.error.URLError, Exception) as e:  # noqa: BLE001
            # We catch all exceptions so heartbeat emitter failures never
            # propagate and crash main trading runtime loop
            logger.warning(
                "Heartbeat emission failed for watchdog URL {}: {}",
                self._watchdog_url,
                e,
            )
            self._last_success = False
            return False

    @property
    def last_heartbeat_time(self) -> datetime | None:
        """Get last successful heartbeat time.

        Returns:
            datetime | None: Timestamp.
        """
        return self._last_heartbeat_time

    @property
    def last_success(self) -> bool:
        """Get last status of heartbeat send.

        Returns:
            bool: True if last send succeeded.
        """
        return self._last_success
