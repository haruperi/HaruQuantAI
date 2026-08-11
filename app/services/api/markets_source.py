"""Runtime-broker resolution for the Markets directory route.

The Markets widget shows tradable symbols from the configured Runtime Broker.
The broker identity lives in the database-backed system settings
(``settings.environment.runtime_broker``), which only the API layer may read;
Data owns the directory aggregation but must not reach into identity settings.
This module is the API-layer injection point that reads the setting, maps the
operator-facing broker token to a Data source identifier, and hands it to the
route handler as a plain string. The route stays a pure delegator.

This module deliberately lives at ``app/services/api`` (sibling to ``_settings``
and ``_limits``) rather than under ``composition`` so that importing it from a
route module does not trigger the full application-composition import graph
(which would create a circular import back into ``routes.data``). It depends
only on the identity boundary and utils.

Mapping rationale: the ``RUNTIME_BROKER`` allowed values
(``mt5, ctrader, binance, dukascopy, yahoo``) are operator tokens, while the
Data domain composes sources under provider identifiers that differ for one
case (``binance`` -> ``binance_spot``). Every other token maps verbatim.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from app.services.api.identity import get_system_settings
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

_DEFAULT_SOURCE_ID: Final = "mt5"

# Operator-facing RUNTIME_BROKER token -> Data source identifier. Every token
# maps verbatim except Binance, whose Data source identifier is the venue
# ``binance_spot``.
_BROKER_TO_SOURCE: Final = MappingProxyType(
    {
        "mt5": "mt5",
        "ctrader": "ctrader",
        "binance": "binance_spot",
        "dukascopy": "dukascopy",
        "yahoo": "yahoo",
    }
)


def resolve_runtime_source_id(
    override: str | None = None, *, request_id: str | None = None
) -> str:
    """Resolve the active runtime broker to a Data source identifier.

    When an explicit ``override`` is supplied (a caller-provided ``source_id``
    query parameter) it is returned verbatim after trimming. Otherwise the
    database-backed ``RUNTIME_BROKER`` system setting is read and mapped. A
    missing or unmappable setting falls back to the default source (``mt5``)
    so the route never fails solely because broker configuration is absent.

    Args:
        override: Optional explicit source identifier from the request.
        request_id: Canonical request identifier for the settings read.

    Returns:
        Data source identifier for the active runtime broker.
    """
    if override is not None and override.strip():
        return override.strip()
    trace_id = request_id if request_id is not None else generate_id("req")
    record = get_system_settings(request_id=trace_id)
    broker = str(record.settings.get("RUNTIME_BROKER", "")).strip().lower()
    source_id = _BROKER_TO_SOURCE.get(broker, _DEFAULT_SOURCE_ID)
    logger.info(
        "Resolved runtime broker %r to source %r", broker or "<unset>", source_id
    )
    return source_id


__all__ = ("resolve_runtime_source_id",)
