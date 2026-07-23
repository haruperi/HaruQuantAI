"""Licence enforcement and attribution for governed source use.

Licence policy is the rule that decides whether Data may read, store, or export a
source's output for a given workflow. Before ``CAP-DATA-026`` Phase 9 that rule was one
condition inlined in ``sources/policy.py``. Extracting it gives licence policy a single
owner: a change to what a licence permits happens here, not in whichever module happened
to need the check.

Every function fails closed. Absent licence metadata is a refusal, not a default —
``SourceLicensePolicy`` carries ``status``, so "unknown" is a value the model can hold
and the enforcement must reject rather than optimistically permit. A licence system that
allows use when it cannot prove permission provides no protection at all.

This module decides nothing about *terms*. Terms are declared in the source descriptor;
this only enforces them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.sources.contracts import SourceDescriptor

__all__ = [
    "enforce_license",
    "get_attribution_text",
]


def enforce_license(
    descriptor: SourceDescriptor,
    workflow_context: str,
    request_id: str | None = None,
) -> None:
    """Reject a source read whose licence does not permit the declared workflow.

    Args:
        descriptor: Source descriptor carrying the licence policy.
        workflow_context: Declared workflow the read serves.
        request_id: Optional trace identifier for the failure.

    Raises:
        DataError: With code ``LICENSE_RESTRICTION`` when the workflow is not in
            ``permitted_workflows``. The safe details name the source but never the
            licence terms themselves, which may be commercially sensitive.
    """
    logger.debug(
        "Enforcing licence for %s in %s", descriptor.source_id, workflow_context
    )
    if workflow_context not in descriptor.license_policy.permitted_workflows:
        raise DataError(
            "LICENSE_RESTRICTION",
            safe_details={"source_id": descriptor.source_id},
            request_id=request_id,
        )


def get_attribution_text(
    descriptor: SourceDescriptor,
    request_id: str | None = None,
) -> str:
    """Return the attribution a publication must carry for this source.

    Returns an empty string when the source requires no attribution — that is a real
    answer, not a missing one. But when attribution *is* required and no text was
    declared, this raises rather than returning empty: silently publishing without a
    mandated credit is the licence breach the field exists to prevent, and an empty
    string would look like a valid result at the call site.

    Args:
        descriptor: Source descriptor carrying the licence policy.
        request_id: Optional trace identifier for the failure.

    Returns:
        The declared attribution text, or an empty string when none is required.

    Raises:
        DataError: With code ``LICENSE_RESTRICTION`` when attribution is required but
            no text was declared.
    """
    logger.debug("Resolving attribution for %s", descriptor.source_id)
    policy = descriptor.license_policy
    if not policy.attribution_required:
        return ""
    if not policy.attribution_text:
        raise DataError(
            "LICENSE_RESTRICTION",
            safe_details={
                "source_id": descriptor.source_id,
                "reason": "attribution_required_but_undeclared",
            },
            request_id=request_id,
        )
    return policy.attribution_text
