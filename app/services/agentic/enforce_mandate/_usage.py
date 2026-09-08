"""Bounded offline usage for FEAT-AGT-ENFORCE_MANDATE."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.contracts.agentic.mandate import BudgetEnvelope, FirmMandate, ValidateMandateRequest, mandate_digest
from app.services.agentic.enforce_mandate.enforce_mandate import MandateService


async def main() -> None:
    now = datetime.now(timezone.utc)
    budget = BudgetEnvelope(1000, 500, 2, 3, Decimal("1.00"))
    draft = FirmMandate(
        "demo", 1, "offline", now - timedelta(minutes=1), now - timedelta(seconds=1),
        now + timedelta(minutes=5), ("offline-demo",), ("EURUSD",), ("demo-account",),
        ("offline",), ("FEAT-AGT-INVOKE_MODELS",), ("analyst",), budget, ("explicit",),
        ("order_execution",), ("fail_closed",), ("policy-v1",), "", "offline://fixture",
    )
    mandate = replace(draft, integrity_digest=mandate_digest(draft))
    service = MandateService(object(), object(), clock=lambda: now)
    print((await service.enforce_mandate(ValidateMandateRequest(mandate))).outcome)
    service.close()


if __name__ == "__main__":
    asyncio.run(main())
