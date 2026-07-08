"""FX currency-leg decomposition and symbol parsing services."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import Field

from app.services.risk.models.contracts import CurrencyLegExposure, RiskContract
from app.utils.logger import logger

FX_SYMBOL_LENGTH = 6

if TYPE_CHECKING:
    from app.services.risk.models.contracts import ProposedTrade
    from app.services.risk.sizing.contracts import SymbolRiskMetadata


class FxPair(RiskContract):
    """Forex base/quote currency pair identity."""

    base: str = Field(..., description="Base currency ISO code (e.g., 'EUR').")
    quote: str = Field(..., description="Quote currency ISO code (e.g., 'USD').")


class ContractSpecification(RiskContract):
    """Specification of contract size for FX currency decomposition."""

    symbol: str = Field(..., description="Target symbol.")
    contract_size: Decimal = Field(
        ..., description="Underlying contract size per standard lot.", gt=0
    )


def parse_fx_symbol(symbol: str, metadata: SymbolRiskMetadata | None = None) -> FxPair:
    """Parse FX symbol to identify base and quote currencies.

    Args:
        symbol: Symbol string (e.g., 'EURUSD').
        metadata: Optional symbol metadata.

    Returns:
        FxPair: Parsed base/quote currency details.

    Raises:
        ValueError: If the symbol format is invalid.
    """
    logger.debug("Parsing FX symbol: %s", symbol)
    _ = metadata
    sym = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
    if len(sym) == FX_SYMBOL_LENGTH:
        base, quote = sym[:3], sym[3:]
        return FxPair(base=base, quote=quote)

    for suffix in ("USD", "EUR", "JPY", "GBP", "AUD", "NZD", "CAD", "CHF"):
        if sym.endswith(suffix) and len(sym) > len(suffix):
            base = sym[: -len(suffix)]
            return FxPair(base=base, quote=suffix)

    msg = f"Invalid FX symbol format: {symbol}"
    logger.warning(msg)
    raise ValueError(msg)


def decompose_fx_trade(
    trade: ProposedTrade, price: Decimal, contract: ContractSpecification
) -> tuple[CurrencyLegExposure, CurrencyLegExposure]:
    """Decompose proposed trade into base and quote currency leg exposures.

    Args:
        trade: The proposed trade to decompose.
        price: Execution price.
        contract: Symbol contract specifications.

    Returns:
        tuple[CurrencyLegExposure, CurrencyLegExposure]: Decomposed base and quote legs.

    Raises:
        ValueError: If the trade side is invalid.
    """
    logger.info("Decomposing trade on %s with price %s", trade.symbol, price)
    fx = parse_fx_symbol(trade.symbol)
    side = trade.side.lower() if hasattr(trade, "side") else trade.direction.lower()
    qty = Decimal(str(trade.volume))
    contract_size = Decimal(str(contract.contract_size))

    if side in {"buy", "long"}:
        base_amt = qty * contract_size
        quote_amt = -qty * contract_size * price
    elif side in {"sell", "short"}:
        base_amt = -qty * contract_size
        quote_amt = qty * contract_size * price
    else:
        msg = f"Invalid trade side: {side}"
        logger.error(msg)
        raise ValueError(msg)

    return (
        CurrencyLegExposure(currency=fx.base, signed_amount=base_amt),
        CurrencyLegExposure(currency=fx.quote, signed_amount=quote_amt),
    )


def validate_currency_conversion_requirements(
    exposures: list[CurrencyLegExposure] | list[Any],
    rates: dict[str, Any] | dict[str, Decimal],
    account_currency: str = "USD",
) -> dict[str, Any]:
    """Verify that conversion rates are available for all non-account leg currencies.

    Args:
        exposures: Unique leg exposures.
        rates: Active conversion rates lookup mapping.
        account_currency: Target account base currency.

    Returns:
        dict[str, Any]: Validation status result.
    """
    logger.info("Validating currency conversion requirements against rates.")
    account_upper = account_currency.upper()
    missing = []
    for leg in exposures:
        ccy = leg.currency.upper()
        if ccy == account_upper:
            continue

        direct = f"{ccy}{account_upper}"
        reverse = f"{account_upper}{ccy}"

        rates_dict = (
            rates.get("conversion_rates", {}) if isinstance(rates, dict) else rates
        )
        if (
            ccy in rates_dict
            or direct in rates_dict
            or reverse in rates_dict
            or direct in rates
            or reverse in rates
            or ccy in rates
        ):
            continue

        missing.append(ccy)

    if missing:
        msg = f"Missing conversion rate requirements for: {', '.join(missing)}"
        logger.warning(msg)
        return {
            "valid": False,
            "reason": msg,
            "details": {"missing_currencies": missing},
        }

    return {
        "valid": True,
        "reason": "All currency conversion requirements met.",
        "details": {},
    }
