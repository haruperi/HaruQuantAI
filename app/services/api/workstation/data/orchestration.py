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
from typing import TYPE_CHECKING, Any, cast

from app.services.api.workstation.data.schemas import build_bar_series_response
from app.services.api.workstation.markets import resolve_runtime_source_id
from app.services.data import (
    build_dataset_save_request,
    build_external_import_request,
    build_market_data_request,
    describe_import_dialects,
    fetch_market_dataset,
    get_market_data,
    import_external_dataset,
    save_dataset,
)

if TYPE_CHECKING:
    from datetime import datetime

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


def _bar_request(
    *,
    source_id: str,
    symbol: str,
    timeframe: str,
    limit: int,
    start: datetime | None,
    end: datetime | None,
    request_id: str,
) -> object:
    """Build one bounded Data bar-history request.

    Args:
        source_id: Resolved Data provider identifier.
        symbol: Broker-native symbol.
        timeframe: Canonical timeframe key.
        limit: Bounded bar count.
        start: Optional inclusive window start.
        end: Optional inclusive window end.
        request_id: Canonical request identifier.

    Returns:
        Validated Data-owned market-data request.
    """
    return build_market_data_request(
        source_id=source_id,
        symbol=symbol,
        data_kind="bars",
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        # A chart is a live view: its newest bar changes on every tick, so a
        # cached window would render as a frozen market.
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=request_id,
    )


def orchestrate_bars(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source_id: str | None,
    start: datetime | None,
    end: datetime | None,
    request_id: str,
) -> object:
    """Delegate one bounded bar-history read to Data.

    Args:
        symbol: Broker-native symbol requested by the caller.
        timeframe: Canonical timeframe key.
        limit: Bounded bar count.
        source_id: Optional explicit Data provider.
        start: Optional inclusive window start.
        end: Optional inclusive window end.
        request_id: Canonical request identifier.

    Returns:
        Normalized API bar-series response.
    """
    resolved_source_id = resolve_runtime_source_id(source_id, request_id=request_id)
    request = _bar_request(
        source_id=resolved_source_id,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        start=start,
        end=end,
        request_id=request_id,
    )
    response = get_market_data(cast("Any", request))

    dataset = getattr(response, "data", None)
    if (
        getattr(response, "status", None) == "success"
        and dataset is not None
        and len(getattr(dataset, "records", ())) <= 1
        and limit > 1
    ):
        # MT5 can return only its current bar while it synchronizes a symbol's
        # history. One retry reads the synchronized window; a genuinely short
        # history simply returns the same result.
        response = get_market_data(
            cast(
                "Any",
                _bar_request(
                    source_id=resolved_source_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    start=start,
                    end=end,
                    request_id=request_id,
                ),
            )
        )

    return build_bar_series_response(
        response,
        source_id=resolved_source_id,
        symbol=symbol,
        timeframe=timeframe,
        request_id=request_id,
    )


__all__ = ("build_dataset_source", "orchestrate_bars")
