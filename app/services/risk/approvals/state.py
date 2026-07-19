"""Private durable state contract for Risk approval tokens."""

# Private protocols are intentionally implemented by receiver-owned adapters.
# ruff: noqa: PYI046

from abc import abstractmethod
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

from app.services.risk.contracts import RiskApprovalToken
from app.utils import logger


class _TokenStateStore(Protocol):  # pragma: no cover
    """Own atomic durable issuance, consumption, and revocation state."""

    @abstractmethod
    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
        """Durably save one exact newly issued token.

        Args:
            token: Exact signed token to persist.
            timeout_seconds: Configured bounded state timeout.

        Returns:
            Atomic persistence outcome.
        """
        logger.debug("Persisting one issued Risk approval token")
        raise NotImplementedError

    @abstractmethod
    def consume_if_active(
        self,
        token_id: str,
        *,
        expected_signature: str,
        reservation_id: str,
        workflow_id: str,
        action: str,
        scope: Mapping[str, str],
        now: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal[
        "consumed",
        "missing",
        "expired",
        "revoked",
        "already_consumed",
        "conflict",
    ]:
        """Atomically reserve and consume one active exact token.

        Args:
            token_id: Durable token identity.
            expected_signature: Signature that must match durable state.
            reservation_id: Unique reservation identity.
            workflow_id: Bound workflow identity.
            action: Bound action name.
            scope: Exact action scope.
            now: Checked UTC consumption time.
            timeout_seconds: Configured bounded state timeout.

        Returns:
            Atomic token-state outcome.
        """
        logger.debug("Atomically consuming one active Risk approval token")
        raise NotImplementedError

    @abstractmethod
    def revoke_intersecting(
        self,
        scope: Mapping[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        """Revoke every unconsumed token intersecting a Risk scope.

        Args:
            scope: Global or exact scoped revocation selector.
            reason: Material revocation reason.
            revoked_at: Checked UTC revocation time.
            timeout_seconds: Configured bounded state timeout.

        Returns:
            Number of newly revoked tokens.
        """
        logger.debug("Revoking Risk approval tokens intersecting a scope")
        raise NotImplementedError


__all__: list[str] = []
