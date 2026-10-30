"""Core trading broker connection and transport abstractions."""

from app.core.trading.connection.base import (
    MAX_RESPONSE_BYTES,
    BridgeError,
    BrokerClient,
    RateLimiter,
    TradingClient,
    create_http_session,
    epoch_millis,
    epoch_seconds,
    execute_bounded_get,
    redact_url_or_message,
    utc_now,
)
from app.core.trading.connection.codecs import (
    CODEC_FR,
    SQ_MAGIC_HEADER_V42,
    decode_sq_dat_bytes,
)
from app.core.trading.connection.trading_dispatch import TradingDispatcher

__all__ = [
    "CODEC_FR",
    "MAX_RESPONSE_BYTES",
    "SQ_MAGIC_HEADER_V42",
    "BridgeError",
    "BrokerClient",
    "RateLimiter",
    "TradingClient",
    "TradingDispatcher",
    "create_http_session",
    "decode_sq_dat_bytes",
    "epoch_millis",
    "epoch_seconds",
    "execute_bounded_get",
    "redact_url_or_message",
    "utc_now",
]
