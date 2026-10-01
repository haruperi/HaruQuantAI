"""Self-contained deterministic crypto usage; authored input only."""

from app.plugin.DataSource.crypto import ExchangeType, normalize_symbol_for_exchange


def main() -> None:
    """Resolve declared exchange symbol notation without contacting an exchange."""
    assert normalize_symbol_for_exchange("btc/usdt", ExchangeType.BINANCE) == "BTCUSDT"
    assert ExchangeType.resolve("coinm") == ExchangeType.BINANCE_COIN_M


if __name__ == "__main__":
    main()
