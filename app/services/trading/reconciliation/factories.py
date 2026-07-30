"""Function-only construction for Trading reconciliation evidence."""

from __future__ import annotations

from app.services.trading.reconciliation.authority import AuthorityResolution
from app.services.trading.reconciliation.compare import ReconciliationReport
from app.services.trading.reconciliation.snapshots import AuthoritySnapshot


def create_authority_resolution(**values: object) -> AuthorityResolution:
    """Construct one validated authority resolution.

    Args:
        **values: Resolution field values.

    Returns:
        Validated internal resolution.
    """
    return AuthorityResolution.model_validate(values)


def create_authority_snapshot(**values: object) -> AuthoritySnapshot:
    """Construct one validated authority snapshot.

    Args:
        **values: Snapshot field values.

    Returns:
        Validated internal snapshot.
    """
    return AuthoritySnapshot.model_validate(values)


def create_reconciliation_report(**values: object) -> ReconciliationReport:
    """Construct one validated reconciliation report.

    Args:
        **values: Report field values.

    Returns:
        Validated internal report.
    """
    return ReconciliationReport.model_validate(values)


__all__ = [
    "create_authority_resolution",
    "create_authority_snapshot",
    "create_reconciliation_report",
]
