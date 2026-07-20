"""Exact fixture-verified Dukascopy provider instruments."""

from types import MappingProxyType

_INSTRUMENT_PRICE_DIVISORS = MappingProxyType({"EURUSD": 100_000})


def _price_divisor(symbol: str) -> int:
    """Handle price divisor.

    Args:
        symbol: Value supplied to the operation.

    Returns:
        The operation result.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    try:
        return _INSTRUMENT_PRICE_DIVISORS[symbol]
    except KeyError as error:
        raise ValueError("unsupported exact Dukascopy provider symbol") from error
