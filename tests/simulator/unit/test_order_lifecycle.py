"""Unit evidence for provider order expiration and fill policies."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.simulator.execution.lifecycle import (
    resolve_fill_remainder,
    resolve_order_expiration,
)

NOW = datetime(2026, 8, 17, 10, tzinfo=UTC)


def test_all_time_policies_use_exact_session_evidence() -> None:
    """GTC and specified policies retain exact expiration semantics."""
    close = NOW.replace(hour=17)
    assert (
        resolve_order_expiration(
            policy="GTC",
            submitted_at=NOW,
            specified_at=None,
            session_closes=(),
        )
        is None
    )
    assert (
        resolve_order_expiration(
            policy="DAY",
            submitted_at=NOW,
            specified_at=None,
            session_closes=(close,),
        )
        == close
    )
    specified = NOW + timedelta(hours=2)
    assert (
        resolve_order_expiration(
            policy="SPECIFIED",
            submitted_at=NOW,
            specified_at=specified,
            session_closes=(),
        )
        == specified
    )
    assert (
        resolve_order_expiration(
            policy="SPECIFIED_DAY",
            submitted_at=NOW,
            specified_at=specified,
            session_closes=(close,),
        )
        == close
    )
    with pytest.raises(ValueError, match="uncovered"):
        resolve_order_expiration(
            policy="DAY",
            submitted_at=NOW,
            specified_at=None,
            session_closes=(),
        )


def test_all_fill_policies_preserve_evidenced_remainder() -> None:
    """FOK/IOC/RETURN/BOC resolve exact fill and residual quantities."""
    expected = {
        "FOK": (Decimal(0), Decimal(2), Decimal(0)),
        "IOC": (Decimal(1), Decimal(1), Decimal(0)),
        "RETURN": (Decimal(1), Decimal(0), Decimal(1)),
        "BOC": (Decimal(0), Decimal(2), Decimal(0)),
    }
    for policy, quantities in expected.items():
        result = resolve_fill_remainder(
            policy=policy,  # type: ignore[arg-type]
            requested=Decimal(2),
            available=Decimal(1),
            remainder_evidenced=policy == "RETURN",
        )
        assert (
            result["filled"],
            result["cancelled"],
            result["remaining"],
        ) == quantities
    with pytest.raises(ValueError, match="requires provider evidence"):
        resolve_fill_remainder(
            policy="RETURN",
            requested=Decimal(2),
            available=Decimal(1),
            remainder_evidenced=False,
        )
