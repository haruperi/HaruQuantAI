"""Provider dispatch and bounded normalized research records."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType

from app.services.data.contracts.errors import DataError
from app.services.data.research_sources import (
    bea,
    bls,
    cftc_cot,
    eia,
    gdelt,
    sec_edgar,
    treasury,
    usda_nass,
)

_MAX_PAYLOAD_BYTES = 1_048_576
_PARSERS = {
    "sec-edgar": sec_edgar.parse_payload,
    "sec-edgar-filing-index": sec_edgar.parse_filing_index_payload,
    "bls": bls.parse_payload,
    "bea": bea.parse_payload,
    "eia": eia.parse_payload,
    "treasury-fiscal-data": treasury.parse_payload,
    "cftc-cot": cftc_cot.parse_payload,
    "gdelt": gdelt.parse_payload,
    "usda-nass": usda_nass.parse_payload,
}


def normalize_research_provider_payload(
    provider: str,
    payload: bytes,
    *,
    observed_at: datetime,
) -> tuple[Mapping[str, object], ...]:
    """Normalize bounded provider bytes without network access.

    Args:
        provider: Registered provider identifier.
        payload: Retrieved provider bytes.
        observed_at: UTC instant when HaruQuantAI observed the payload.

    Returns:
        Detached normalized records containing source values and provenance.

    Raises:
        DataError: If the provider or payload is invalid.
    """
    parser = _PARSERS.get(provider)
    if parser is None:
        raise DataError("INVALID_INPUT", safe_details={"field": "research_provider"})
    if not payload or len(payload) > _MAX_PAYLOAD_BYTES:
        raise DataError("LIMIT_EXCEEDED", safe_details={"field": "source_payload"})
    records = parser(payload, observed_at)
    if not records:
        raise DataError("EMPTY_RESULT")
    digest = hashlib.sha256(payload).hexdigest()
    detached: list[Mapping[str, object]] = []
    for record in records[:200]:
        value = dict(record)
        value["content_sha256"] = digest
        value["provider"] = provider
        detached.append(MappingProxyType(value))
    return tuple(detached)


__all__ = ("normalize_research_provider_payload",)
