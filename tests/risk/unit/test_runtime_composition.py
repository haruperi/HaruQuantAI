"""Tests for Risk-owned API runtime composition adapters."""

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import patch

import pytest
from app.services.risk import (
    build_allocation_runtime_operation,
    build_governance_runtime_operation,
)


def _clock() -> datetime:
    """Return a stable aware runtime instant.

    Returns:
        Fixed UTC instant.
    """
    return datetime(2026, 8, 1, tzinfo=UTC)


def test_allocation_runtime_delegates_complete_owner_evidence() -> None:
    """Allocation composition constructs every typed input before delegation."""
    store = cast("Any", object())
    audit = cast("Any", object())
    expected = object()
    with (
        patch(
            "app.services.risk.allocation.runtime.create_allocation_review_request",
            return_value="request",
        ),
        patch(
            "app.services.risk.allocation.runtime.create_portfolio_risk_snapshot",
            return_value="snapshot",
        ),
        patch(
            "app.services.risk.allocation.runtime.build_market_context_evidence",
            return_value="market",
        ),
        patch(
            "app.services.risk.allocation.runtime.create_risk_config",
            return_value="config",
        ),
        patch(
            "app.services.risk.allocation.runtime.review_allocation_proposal",
            return_value=expected,
        ) as review,
    ):
        operation = build_allocation_runtime_operation(
            store=store,
            audit=audit,
            clock=_clock,
        )
        result = operation(
            {
                "request": {},
                "snapshot": {},
                "market_context": {},
                "config": {},
            },
            object(),
        )

    assert result is expected
    review.assert_called_once_with(
        "request",
        "snapshot",
        "market",
        "config",
        store,
        audit,
        now=_clock(),
    )


def test_governance_runtime_rejects_unstructured_switch_evidence() -> None:
    """Governance composition fails closed before calling its owner."""
    operation = build_governance_runtime_operation(
        governor=cast("Any", object()),
        clock=_clock,
    )

    with pytest.raises(TypeError, match="must be an array"):
        operation({"kill_switch_states": "invalid"}, object())


def test_allocation_runtime_rejects_missing_nested_evidence() -> None:
    """Allocation composition rejects an incomplete request boundary."""
    operation = build_allocation_runtime_operation(
        store=cast("Any", object()),
        audit=cast("Any", object()),
        clock=_clock,
    )

    with pytest.raises(TypeError, match="request must be an object"):
        operation({}, object())


def test_governance_runtime_delegates_complete_owner_evidence() -> None:
    """Governance composition constructs typed evidence and delegates to RiskGovernor."""
    governor = cast("Any", object())
    expected = object()
    with (
        patch(
            "app.services.risk.governor.runtime.create_portfolio_risk_snapshot",
            return_value="snapshot",
        ),
        patch(
            "app.services.risk.governor.runtime.build_market_context_evidence",
            return_value="market",
        ),
        patch(
            "app.services.risk.governor.runtime.create_regime_assessment",
            return_value="regime",
        ),
        patch(
            "app.services.risk.governor.runtime.create_kill_switch_state",
            return_value="state_1",
        ),
        patch(
            "app.services.risk.governor.runtime.run_portfolio_risk_governor",
            return_value=expected,
        ) as run_gov,
    ):
        operation = build_governance_runtime_operation(
            governor=governor,
            clock=_clock,
        )
        body = {
            "snapshot": {},
            "market_context": {},
            "regime": {},
            "kill_switch_states": [{"scope_level": "global", "state": "active"}],
        }
        auth = object()
        result = operation(body, auth)

        assert result is expected
        run_gov.assert_called_once_with(
            governor,
            "snapshot",
            "market",
            "regime",
            ("state_1",),
            auth,
            now=_clock(),
        )


def test_governance_runtime_rejects_invalid_kill_switch_items() -> None:
    """Governance composition fails when kill_switch_states items are not mappings."""
    operation = build_governance_runtime_operation(
        governor=cast("Any", object()),
        clock=_clock,
    )
    with pytest.raises(TypeError, match="kill_switch_states entries must be objects"):
        operation({"kill_switch_states": ["not_a_mapping"]}, object())


def test_governance_runtime_rejects_invalid_nested_mapping() -> None:
    """Governance composition fails when nested snapshot or regime is not a mapping."""
    operation = build_governance_runtime_operation(
        governor=cast("Any", object()),
        clock=_clock,
    )
    with pytest.raises(TypeError, match="snapshot must be an object"):
        operation({"kill_switch_states": [], "snapshot": "not_a_mapping"}, object())
