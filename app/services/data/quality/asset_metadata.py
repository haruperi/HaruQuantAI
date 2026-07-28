"""Precision and instrument-metadata validation for a supplied symbol.

Answers whether the metadata a source declared is complete and self-consistent enough
for a governed workflow to rely on. It is a pure check on a ``SymbolMetadata`` it is
handed: it performs no lookup, resolves no identity, and contacts no source.

``map_canonical_symbol`` was proposed for this module and deliberately excluded.
``sources/registry.resolve_source_identity`` already performs provider-symbol mapping,
so a second implementation would duplicate it — and importing ``sources`` from
``quality`` would add a dependency edge that the layering does not have. Symbol mapping
stays with its existing owner.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.market_data.symbol_metadata import SymbolMetadata

__all__ = ["validate_symbol_metadata"]

# Fields a governed workflow cannot proceed without. `asset_class` is included because
# it cannot be derived from an artifact, so its absence must fail rather than default.
_REQUIRED_FOR_GOVERNED_USE = ("asset_class", "digits", "price_step")


def _validate_symbol_metadata_raw(metadata: SymbolMetadata) -> SymbolMetadata:
    """Verify symbol metadata is complete and consistent without response wrapping.

    Raises:
        DataError: ``MISSING_ASSET_METADATA`` or ``PRECISION_MISMATCH`` as documented.
    """
    logger.debug("Validating symbol metadata for %s", metadata.canonical_symbol)

    missing = set(metadata.missing_fields)
    for field in _REQUIRED_FOR_GOVERNED_USE:
        if getattr(metadata, field, None) is None or field in missing:
            raise DataError(
                "MISSING_ASSET_METADATA",
                safe_details={
                    "symbol": metadata.canonical_symbol,
                    "field": field,
                },
                request_id=metadata.request_id,
            )

    for field in ("price_step", "quantity_step"):
        step = getattr(metadata, field, None)
        if step is not None and step <= Decimal(0):
            raise DataError(
                "PRECISION_MISMATCH",
                safe_details={
                    "symbol": metadata.canonical_symbol,
                    "field": field,
                    "reason": "non_positive_step",
                },
                request_id=metadata.request_id,
            )

    digits = metadata.digits
    price_step = metadata.price_step
    if digits is not None and price_step is not None:
        expected = Decimal(1).scaleb(-digits)
        if price_step != expected:
            raise DataError(
                "PRECISION_MISMATCH",
                safe_details={
                    "symbol": metadata.canonical_symbol,
                    "reason": "digits_step_disagree",
                },
                request_id=metadata.request_id,
            )

    return metadata


def validate_symbol_metadata(
    metadata: SymbolMetadata,
) -> StandardResponse[SymbolMetadata]:
    """Verify that symbol metadata is complete and internally consistent.

    Checks three things a source can get wrong without the contract noticing: that the
    fields a governed workflow needs are present rather than explicitly missing, that
    the declared step sizes are positive, and that ``digits`` and ``price_step`` agree
    with each other. A five-digit instrument with a step of ``0.01`` is not a rounding
    nuisance — it silently misprices every downstream calculation.

    Args:
        metadata: Normalized symbol metadata to verify.

    Returns:
        Standard response carrying the same metadata, unchanged, when every check
        passes.

    Raises:
        (in-band) ``MISSING_ASSET_METADATA`` when a field required for governed use is
            absent or listed in ``missing_fields``; ``PRECISION_MISMATCH`` when a step
            is non-positive, or when ``digits`` and ``price_step`` disagree.
    """
    return run_data_operation(
        operation="data.quality.validate_symbol_metadata",
        request_id=metadata.request_id,
        start_time=data_start_time(),
        raw=lambda: _validate_symbol_metadata_raw(metadata),
    )
