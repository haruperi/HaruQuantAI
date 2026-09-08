from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.contracts.agentic.mandate import BudgetEnvelope, CheckMandateScopeRequest, FirmMandate, MandateOutcome, ValidateMandateRequest, mandate_digest
from app.services.agentic.enforce_mandate.enforce_mandate import MandateService


def _mandate(now: datetime) -> FirmMandate:
    budget = BudgetEnvelope(100, 50, 2, 3, Decimal("1.0"))
    draft = FirmMandate("m1", 1, "issuer", now-timedelta(minutes=2), now-timedelta(minutes=1), now+timedelta(minutes=1), ("research",), ("EURUSD",), ("acct",), ("offline",), ("feat",), ("role",), budget, ("explicit",), ("order_execution",), ("fail_closed",), ("p1",), "", "sig://1")
    return replace(draft, integrity_digest=mandate_digest(draft))


@pytest.mark.asyncio
async def test_validate_integrity_time_and_scope() -> None:
    now = datetime.now(timezone.utc)
    service = MandateService(object(), object(), clock=lambda: now)
    mandate = _mandate(now)
    assert (await service.enforce_mandate(ValidateMandateRequest(mandate))).outcome is MandateOutcome.ACCEPTED
    assert (await service.enforce_mandate(ValidateMandateRequest(replace(mandate, enabled_roles=("other",))))).outcome is MandateOutcome.INVALID
    expired = replace(mandate, issued_at=now-timedelta(minutes=3), effective_at=now-timedelta(minutes=2), expires_at=now, integrity_digest="")
    expired = replace(expired, integrity_digest=mandate_digest(expired))
    assert (await service.enforce_mandate(ValidateMandateRequest(expired))).outcome is MandateOutcome.INVALID
    request = CheckMandateScopeRequest(mandate, "feat", "role", "offline", "acct", "EURUSD", BudgetEnvelope(10, 10, 1, 1, Decimal("0.1")))
    assert (await service.enforce_mandate(request)).outcome is MandateOutcome.ALLOWED


@pytest.mark.asyncio
async def test_scope_and_budget_fail_closed() -> None:
    now = datetime.now(timezone.utc)
    service = MandateService(object(), object(), clock=lambda: now)
    request = CheckMandateScopeRequest(_mandate(now), "feat", "role", "offline", "other", "EURUSD", BudgetEnvelope(1000, 10, 1, 1, Decimal("0.1")))
    result = await service.enforce_mandate(request)
    assert result.outcome is MandateOutcome.DENIED
    assert "ACCOUNT_NOT_ALLOWED" in result.reason_codes
    assert "BUDGET_EXCEEDED" in result.reason_codes
