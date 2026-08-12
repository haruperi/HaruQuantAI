"""Composition of governed dataset preparation behind the API boundary.

Dataset preparation is a two-step Data delegation: fetch the requested market
dataset, then persist it through Data's storage boundary. Both request shapes
and both operations belong to Data. The gateway forwards caller payloads to
Data package-root builders, sequences the two owner calls, and returns the
owner-authored storage manifest. It never reads, writes, caches, or reshapes a
dataset itself, and it never invents a storage location.

External import follows the same shape: Data parses, validates, and persists
the caller-named source and authors the resulting storage manifest. The gateway
never reads the file itself and never chooses a dialect — `describe_import_dialects`
exposes Data's own supported set so a caller can choose from owner truth.

Both operations are bound unconditionally because neither needs a receiver-owned
runtime: Data owns its own connection, storage, and locking infrastructure.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.services.data import (
    build_dataset_save_request,
    build_external_import_request,
    build_market_data_request,
    describe_import_dialects,
    fetch_market_dataset,
    import_external_dataset,
    save_dataset,
)

type AuthContext = Any
type _DataOperation = Callable[..., object]


def build_dataset_source() -> _DataOperation:
    """Build one dataset preparation dispatcher.

    Returns:
        Route operation dispatcher bound to Data public functions.
    """

    def _operation(operation: str, *args: object) -> object:
        """Fetch and persist one requested market dataset.

        Args:
            operation: Canonical operation name — ``prepare``, ``import``, or
                ``dialects``.
            *args: Operation-specific serialized payloads.

        Returns:
            Data-owned response for the requested operation.

        Raises:
            ValueError: If the requested operation is not registered.
            RuntimeError: If Data reports no dataset for the request.
        """
        if operation == "dialects":
            return describe_import_dialects()
        if operation == "import":
            payload = dict(cast("Mapping[str, object]", args[0]))
            return import_external_dataset(
                cast("Any", build_external_import_request(**payload))
            )
        if operation != "prepare":
            raise ValueError("unsupported Data operation")
        market_payload = dict(cast("Mapping[str, object]", args[0]))
        save_payload = dict(cast("Mapping[str, object]", args[1]))

        market_response = fetch_market_dataset(
            cast("Any", build_market_data_request(**market_payload))
        )
        dataset = getattr(market_response, "data", None)
        if dataset is None:
            raise RuntimeError("DATASET_UNAVAILABLE")
        return save_dataset(
            cast("Any", build_dataset_save_request(dataset=dataset, **save_payload))
        )

    return _operation


__all__ = ("build_dataset_source",)
