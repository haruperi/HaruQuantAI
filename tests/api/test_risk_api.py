"""Unit tests for capability-aware RiskAPI facade."""

from typing import override

import pytest

from app.api.risk import RiskAPI
from app.contracts.broker.execution import OrderRequest, OrderSide, OrderType
from app.contracts.risk.approval import (
    RISK_APPROVAL,
    RiskApproval,
    RiskDecision,
    RiskVerdict,
)
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import ServiceRegistry


class DummyRiskService(RiskApproval):
    @override
    async def evaluate_order(self, order: OrderRequest) -> RiskDecision:
        return RiskDecision(
            verdict=RiskVerdict.APPROVED,
            reason=f"Order for {order.symbol} within risk parameters",
        )


@pytest.mark.asyncio
async def test_risk_api_approval_available() -> None:
    """Test RiskAPI approves order when risk capability is active."""
    registry = ServiceRegistry()
    service = DummyRiskService()
    registry.register(RISK_APPROVAL, service, owner_id="FEAT-RISK-CHECK_LIMITS")

    api = RiskAPI(registry)
    assert api.is_approval_available is True

    order = OrderRequest(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
    )
    decision = await api.evaluate_order(order)
    assert decision.verdict == RiskVerdict.APPROVED
    assert "EURUSD" in decision.reason


@pytest.mark.asyncio
async def test_risk_api_approval_unavailable() -> None:
    """Test RiskAPI raises CapabilityUnavailableError when risk approval is absent."""
    registry = ServiceRegistry()
    api = RiskAPI(registry)
    assert api.is_approval_available is False

    order = OrderRequest(
        symbol="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
    )
    with pytest.raises(CapabilityUnavailableError, match=r"risk\.approval@1"):
        await api.evaluate_order(order)
