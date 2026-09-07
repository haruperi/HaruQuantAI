"""Governed, idempotent notification delivery coordination."""

from __future__ import annotations

import asyncio
import hashlib
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from app.contracts.orchestration.models import (
    NotificationChannelConfig,
    NotificationReceipt,
    NotificationTemplate,
)
from app.kernel.redaction import redact_mapping_value, redact_text_value

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject
    from app.contracts.notification.delivery.v1 import NotificationDeliveryCapabilityV1
    from app.services.orchestration.deliver_notifications._persistence import (
        NotificationStore,
    )

type NotificationStatus = Literal[
    "PENDING",
    "DELIVERED",
    "FAILED",
    "UNKNOWN",
    "SUPPRESSED_RATE_LIMIT",
    "DISABLED",
]

_RATE_PATTERN = re.compile(r"^(?P<count>[1-9]\d*)/(?P<unit>second|minute|hour)$")
_WINDOWS = {
    "second": timedelta(seconds=1),
    "minute": timedelta(minutes=1),
    "hour": timedelta(hours=1),
}


def _format_utc(value: datetime) -> str:
    """Render one aware timestamp in the canonical UTC wire form.

    Returns:
        Canonical UTC timestamp string.
    """
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class _StrictVariables(dict[str, object]):
    def __missing__(self, key: str) -> object:
        message = f"NOTIFICATION_TEMPLATE_VARIABLE_MISSING:{key}"
        raise ValueError(message)


class DeliverNotificationsService:
    """Apply policy once and retain a durable receipt for every request."""

    def __init__(
        self,
        store: NotificationStore,
        provider: NotificationDeliveryCapabilityV1 | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize a delivery coordinator.

        Args:
            store: Feature-owned durable receipt store.
            provider: Optional selected delivery transport.
            clock: Injectable aware UTC clock.
        """
        self._store = store
        self._provider = provider
        self._clock = clock or (lambda: datetime.now(UTC))
        self._closed = False

    async def deliver(  # noqa: PLR0911 - policy exits map to distinct receipts.
        self,
        *,
        delivery_id: str,
        channel: NotificationChannelConfig,
        template: NotificationTemplate,
        variables: JsonObject | None = None,
        title: str = "HaruQuantAI",
        master_enabled: bool = False,
    ) -> NotificationReceipt:
        """Apply enablement, rate, redaction, idempotency, and delivery policy.

        Args:
            delivery_id: Caller-supplied logical idempotency identity.
            channel: Validated channel configuration.
            template: Versioned notification template.
            variables: JSON-safe template substitutions.
            title: Transport-visible title.
            master_enabled: Explicit application-wide delivery switch.

        Returns:
            Durable terminal or uncertain receipt.

        Raises:
            RuntimeError: If the service is closed.
            TypeError: If redacted variables are not a mapping.
            ValueError: If the rate expression or template is invalid, or an
                idempotency identity is reused for different rendered content.
        """
        self._ensure_open()
        now = self._clock()
        safe_variables = redact_mapping_value(dict(variables or {})).value
        if not isinstance(safe_variables, dict):
            raise TypeError("NOTIFICATION_VARIABLES_INVALID")
        rendered = template.body_template.format_map(_StrictVariables(safe_variables))
        safe_rendered = str(redact_text_value(rendered).value)
        safe_title = str(redact_text_value(title).value)
        rendered_identity = "\0".join(
            (
                channel.channel_id,
                template.template_id,
                str(template.version),
                safe_title,
                safe_rendered,
            )
        )
        rendered_hash = hashlib.sha256(rendered_identity.encode("utf-8")).hexdigest()

        existing = self._store.get(delivery_id)
        if existing is not None:
            if existing.rendered_hash != rendered_hash:
                raise ValueError("NOTIFICATION_IDEMPOTENCY_KEY_REUSED")
            if existing.status == "PENDING":
                return self._save(
                    existing,
                    status="UNKNOWN",
                    now=now,
                    error="DELIVERY_OUTCOME_UNKNOWN",
                )
            return existing

        if not master_enabled or not channel.is_enabled:
            return self._new_receipt(
                delivery_id,
                channel,
                rendered_hash,
                status="DISABLED",
                now=now,
            )

        rate_count, rate_window = self._parse_rate(channel.rate_limit)
        since = _format_utc(now - rate_window)
        if self._store.count_attempts(channel.channel_id, since) >= rate_count:
            return self._new_receipt(
                delivery_id,
                channel,
                rendered_hash,
                status="SUPPRESSED_RATE_LIMIT",
                now=now,
            )

        pending = self._new_receipt(
            delivery_id,
            channel,
            rendered_hash,
            status="PENDING",
            now=now,
        )
        if self._provider is None or not self._provider.active:
            return self._save(
                pending,
                status="FAILED",
                now=now,
                error="DELIVERY_PROVIDER_UNAVAILABLE",
            )
        try:
            result = await asyncio.to_thread(
                self._provider.send,
                safe_title,
                safe_rendered,
                safe_rendered if template.content_kind == "HTML" else None,
            )
        except Exception:  # noqa: BLE001 - provider outcome may be uncertain.
            return self._save(
                pending,
                status="UNKNOWN",
                now=now,
                error="DELIVERY_OUTCOME_UNKNOWN",
            )
        if result.status.lower() not in {"accepted", "delivered", "success"}:
            return self._save(
                pending,
                status="FAILED",
                now=now,
                error="DELIVERY_PROVIDER_REJECTED",
            )
        return self._save(pending, status="DELIVERED", now=now)

    def close(self) -> None:
        """Close feature-owned persistence exactly once."""
        if self._closed:
            return
        self._closed = True
        self._store.close()

    @staticmethod
    def _parse_rate(value: str) -> tuple[int, timedelta]:
        """Parse a bounded fixed-window rate expression.

        Returns:
            Maximum attempt count and fixed window duration.

        Raises:
            ValueError: If the expression does not use ``count/unit`` syntax.
        """
        match = _RATE_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("NOTIFICATION_RATE_LIMIT_INVALID")
        unit = match.group("unit")
        return int(match.group("count")), _WINDOWS[unit]

    def _new_receipt(
        self,
        delivery_id: str,
        channel: NotificationChannelConfig,
        rendered_hash: str,
        *,
        status: NotificationStatus,
        now: datetime,
    ) -> NotificationReceipt:
        """Create and persist a new receipt.

        Returns:
            Newly persisted receipt.
        """
        receipt = NotificationReceipt(
            receipt_id=str(uuid.uuid7()),
            delivery_id=delivery_id,
            channel_id=channel.channel_id,
            status=status,
            rendered_hash=rendered_hash,
        )
        self._store.save(receipt, _format_utc(now))
        return receipt

    def _save(
        self,
        receipt: NotificationReceipt,
        *,
        status: NotificationStatus,
        now: datetime,
        error: str | None = None,
    ) -> NotificationReceipt:
        """Persist a status update without changing receipt identity.

        Returns:
            Updated durable receipt.
        """
        updated = receipt.model_copy(
            update={
                "status": status,
                "sent_at": _format_utc(now) if status == "DELIVERED" else None,
                "error": error,
            }
        )
        self._store.save(updated, _format_utc(now))
        return updated

    def _ensure_open(self) -> None:
        """Reject work after lifecycle shutdown.

        Raises:
            RuntimeError: If this service is closed.
        """
        if self._closed:
            raise RuntimeError("deliver-notifications service is closed")
