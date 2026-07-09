"""Import-safe execution coordination helpers.

This module contains only broker-independent packaging behavior for the first
trading runtime unit. It performs no broker calls and imports no provider SDKs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.contracts import JsonObject, TradingRequestEnvelope


class ExecutionCoordinator:
    """Broker-independent request packaging coordinator."""

    def build_broker_dispatch_payload(
        self,
        request: TradingRequestEnvelope,
    ) -> JsonObject:
        """Build a JSON-safe broker dispatch payload.

        Args:
            request: Trading request envelope.

        Returns:
            JsonObject: Dispatch payload with regulatory tags propagated.
        """
        logger.info("Building broker dispatch payload for {}.", request.request_id)
        return request.to_broker_dispatch_payload()
