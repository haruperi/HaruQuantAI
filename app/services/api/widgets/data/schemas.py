"""Data gateway request schemas and owner-response projections."""

from collections.abc import Mapping
from decimal import Decimal
from typing import Final, Literal

from app.services.api import build_api_metadata, build_api_response
from app.services.api.contracts.models import _BaseApiContract

# Data's canonical timeframe manifest, restated here as the accepted query
# domain so an unsupported key is refused at the boundary with a 422 rather
# than reaching Data as an UNSUPPORTED_TIMEFRAME failure.
type BarTimeframe = Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]

BAR_TIMEFRAMES: Final = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1")


class DatasetPrepareRequest(_BaseApiContract):
    """Governed dataset preparation command.

    Preparation is a two-step owner delegation: Data fetches the requested
    market dataset and then persists it. Both request shapes belong to Data; the
    gateway forwards them and stores nothing itself.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_prepare_request.v1"] = (
        "api.dataset_prepare_request.v1"
    )
    market_request: Mapping[str, object]
    save_request: Mapping[str, object]


class DatasetImportRequest(_BaseApiContract):
    """Governed external dataset import command.

    Data owns parsing, dialect handling, validation, and persistence, and
    authors the resulting storage manifest. The gateway forwards the caller
    payload unchanged: it never reads the source file and never selects a
    dialect on the caller's behalf.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.dataset_import_request.v1"] = (
        "api.dataset_import_request.v1"
    )
    payload: Mapping[str, object]


class SeriesUpdateRequest(_BaseApiContract):
    """Governed market-series edit command.

    Carries the editable series fields and the linked instrument
    specification fields. Data validates and applies both atomically; the
    bar-type reference is invariant and therefore not part of the contract.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.series_update_request.v1"] = "api.series_update_request.v1"
    symbol: str
    instrument: str
    broker_id: int | None = None
    timeframe: str | None = None
    timezone: str | None = None
    date_from: int | None = None
    date_to: int | None = None
    data_type: int | None = None
    decimals: int | None = None
    source: int | None = None
    row_count: int | None = None
    remove_weekends: int = 0
    show: int = 1
    description: str | None = None
    point_value: float | None = None
    tick_size: float | None = None
    tick_step: float | None = None
    default_spread: float | None = None
    default_slippage: float | None = None
    min_distance: float | None = None
    order_size_multiplier: float | None = None
    order_size_step: float | None = None


class InstrumentUpdateRequest(_BaseApiContract):
    """Governed instrument specification edit command.

    Carries the editable instrument fields; Data validates and applies the
    single-row update. The instrument identity itself is immutable and lives
    in the route path.
    """

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["api.instrument_update_request.v1"] = (
        "api.instrument_update_request.v1"
    )
    description: str | None = None
    point_value: float | None = None
    tick_size: float | None = None
    tick_step: float | None = None
    default_spread: float | None = None
    default_slippage: float | None = None
    min_distance: float | None = None
    order_size_multiplier: float | None = None
    order_size_step: float | None = None


def _number(value: object) -> float | None:
    """Project one Data-owned decimal price or volume as a JSON number.

    Data returns exact ``Decimal`` values under the ``decimal_string``
    precision policy. A chart plots pixels, so the transport carries plain
    numbers; the exactness that matters downstream stays with Data.

    Args:
        value: Decimal, numeric, or absent record field.

    Returns:
        Finite float, or ``None`` when the field carries no value.
    """
    if value is None:
        return None
    if isinstance(value, Decimal | int | float):
        return float(value)
    return None


def _project_bar(record: object) -> dict[str, object]:
    """Project one canonical OHLCV record into the chart transport shape.

    Args:
        record: Data-owned ``OHLCVRecord``.

    Returns:
        Bar mapping carrying the UTC open time and OHLCV values.
    """
    timestamp = getattr(record, "timestamp", None)
    return {
        "time": timestamp.isoformat() if timestamp is not None else None,
        "open": _number(getattr(record, "open", None)),
        "high": _number(getattr(record, "high", None)),
        "low": _number(getattr(record, "low", None)),
        "close": _number(getattr(record, "close", None)),
        "volume": _number(getattr(record, "volume", None)),
    }


def build_bar_series_response(
    response: object,
    *,
    source_id: str,
    symbol: str,
    timeframe: str,
    request_id: str,
) -> object:
    """Normalize one Data bar dataset into the canonical API envelope.

    A failed or empty owner read stays explicit: the gateway never substitutes
    generated bars for a provider result a chart would render as real history.

    Args:
        response: Data standard response carrying a ``MarketDataset``.
        source_id: Resolved Data provider identifier.
        symbol: Broker-native symbol the caller requested.
        timeframe: Canonical timeframe the caller requested.
        request_id: Canonical API request identifier.

    Returns:
        Validated API response envelope carrying the ordered bar series.
    """
    response_status = str(getattr(response, "status", "error"))
    dataset = getattr(response, "data", None)
    upstream_error = getattr(response, "error", None)

    gateway_error = None
    if response_status != "success":
        gateway_error = {
            "code": "UPSTREAM_UNAVAILABLE",
            "message": str(getattr(upstream_error, "message", "Bars unavailable")),
            "details": {
                "upstream_code": str(getattr(upstream_error, "code", "UNKNOWN_ERROR"))
            },
            "retryable": bool(getattr(upstream_error, "retryable", False)),
            "request_id": request_id,
            "trace_id": None,
        }

    data_payload = None
    if dataset is not None:
        records = tuple(getattr(dataset, "records", ()))
        start = getattr(dataset, "start", None)
        end = getattr(dataset, "end", None)
        data_payload = {
            "source_id": source_id,
            "symbol": str(getattr(dataset, "symbol", symbol)),
            "timeframe": str(getattr(dataset, "timeframe", timeframe) or timeframe),
            "bars": [_project_bar(record) for record in records],
            "count": len(records),
            "start": start.isoformat() if start is not None else None,
            "end": end.isoformat() if end is not None else None,
            "cache_status": str(getattr(dataset, "cache_status", "not_used")),
            "request_id": request_id,
        }

    return build_api_response(
        status=response_status,
        message=(
            "Bars retrieved" if response_status == "success" else "Bars unavailable"
        ),
        data=data_payload,
        error=gateway_error,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/bars",
            operation="api.data.bars",
            side_effect="read",
        ),
    )


__all__ = (
    "BAR_TIMEFRAMES",
    "BarTimeframe",
    "DatasetImportRequest",
    "DatasetPrepareRequest",
    "InstrumentUpdateRequest",
    "SeriesUpdateRequest",
    "build_bar_series_response",
)
