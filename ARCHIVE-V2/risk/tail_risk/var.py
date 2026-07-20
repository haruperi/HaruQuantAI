# ruff: noqa: ANN401, PLR2004, C901, PLR0912
"""Portfolio Value-at-Risk (VaR) computation service."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from statistics import NormalDist
from typing import Any, overload

from app.services.risk.correlation import calculate_returns
from app.services.risk.correlation.contracts import (
    ComponentRiskContribution,
    CovarianceMatrix,
)
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.exposure import (
    _resolve_base_quote,
    _resolve_conversion_rate,
)
from app.services.risk.models.contracts import (
    PortfolioState,
    ProposedTrade,
    VaRSnapshot,
)
from app.services.risk.tail_risk.contracts import (
    VaRCalculationRequest,
    VaRMethod,
)
from app.utils.logger import logger

MIN_SAMPLES_FOR_COVARIANCE = 2


def calculate_covariance(x: Sequence[Decimal], y: Sequence[Decimal]) -> Decimal:
    """Calculate sample covariance between two aligned series.

    Args:
        x: First returns sequence.
        y: Second returns sequence.

    Returns:
        Decimal: Sample covariance value.
    """
    logger.debug("Calculating sample covariance.")
    n = len(x)
    if n < MIN_SAMPLES_FOR_COVARIANCE:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    sum_prod = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y, strict=True))
    return sum_prod / Decimal(n - 1)


def calculate_ewma_covariance(
    x: Sequence[Decimal],
    y: Sequence[Decimal],
    decay: Decimal = Decimal("0.94"),
) -> Decimal:
    """Calculate Exponentially Weighted Moving Average (EWMA) covariance.

    Args:
        x: First returns sequence.
        y: Second returns sequence.
        decay: Decay factor lambda (typically 0.94).

    Returns:
        Decimal: Calculated EWMA covariance.
    """
    logger.debug("Calculating EWMA covariance with decay %s.", decay)
    n = len(x)
    if n < MIN_SAMPLES_FOR_COVARIANCE:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    weights = [decay ** (n - 1 - i) for i in range(n)]
    sum_weights = sum(weights, Decimal("0.0"))
    if sum_weights == Decimal("0.0"):
        return Decimal("0.0")

    weighted_sum = sum(
        (
            (w * (xi - mean_x) * (yi - mean_y))
            for w, xi, yi in zip(weights, x, y, strict=True)
        ),
        Decimal("0.0"),
    )

    return weighted_sum / sum_weights


def calculate_covariance_matrix(
    returns_db: Mapping[str, Sequence[Decimal]],
    method: str = "parametric",
    ewma_decay: Decimal = Decimal("0.94"),
) -> dict[str, dict[str, Decimal]]:
    """Compute pairwise covariance matrix for return series.

    Args:
        returns_db: A dictionary mapping symbol to list of aligned returns.
        method: Method used ('parametric' or 'ewma').
        ewma_decay: EWMA decay factor.

    Returns:
        dict[str, dict[str, Decimal]]: Covariance matrix dictionary.
    """
    logger.info("Computing covariance matrix using method %s.", method)
    symbols = sorted(returns_db.keys())
    matrix: dict[str, dict[str, Decimal]] = {}

    for i, s1 in enumerate(symbols):
        if s1 not in matrix:
            matrix[s1] = {}
        for s2 in symbols[i:]:
            if s2 not in matrix:
                matrix[s2] = {}

            if method == "ewma":
                cov = calculate_ewma_covariance(
                    returns_db[s1], returns_db[s2], decay=ewma_decay
                )
            else:
                cov = calculate_covariance(returns_db[s1], returns_db[s2])

            matrix[s1][s2] = cov
            matrix[s2][s1] = cov

    return matrix


def shrink_covariance_matrix(
    matrix: dict[str, dict[str, Decimal]],
    shrinkage_intensity: Decimal = Decimal("0.1"),
) -> dict[str, dict[str, Decimal]]:
    """Apply shrinkage towards diagonal target (constant variance target).

    Args:
        matrix: Covariance matrix.
        shrinkage_intensity: Shrinkage intensity delta (0.0 to 1.0).

    Returns:
        dict[str, dict[str, Decimal]]: Shrunk covariance matrix.
    """
    logger.info(
        "Applying shrinkage to covariance matrix with intensity %s.",
        shrinkage_intensity,
    )
    symbols = sorted(matrix.keys())
    shrunk: dict[str, dict[str, Decimal]] = {}

    for s1 in symbols:
        shrunk[s1] = {}
        for s2 in symbols:
            val = matrix[s1][s2]
            if s1 == s2:
                shrunk[s1][s2] = val
            else:
                shrunk[s1][s2] = val * (Decimal("1.0") - shrinkage_intensity)

    return shrunk


def validate_covariance_matrix(
    matrix: dict[str, dict[str, Decimal]] | CovarianceMatrix,
) -> None:
    """Verify covariance matrix has non-negative diagonal values and is symmetric.

    Args:
        matrix: Covariance matrix (dict or model).

    Raises:
        ValidationError: If covariance matrix validation checks fail.
    """
    logger.info("Validating covariance matrix properties.")
    raw_matrix = matrix.matrix if isinstance(matrix, CovarianceMatrix) else matrix
    for s1, row1 in raw_matrix.items():
        diag = row1.get(s1, Decimal("0.0"))
        if diag < 0:
            msg = f"Invalid covariance matrix: negative variance for {s1} ({diag})"
            logger.error(msg)
            raise ValidationError(msg)
        for s2, val in row1.items():
            val2 = raw_matrix[s2].get(s1)
            if val is None or val2 is None:
                msg = f"Invalid covariance matrix: missing elements for {s1}-{s2}"
                logger.error(msg)
                raise ValidationError(msg)
            if abs(val - val2) > Decimal("1e-6"):
                msg = f"Invalid covariance matrix: asymmetry detected between {s1}-{s2}"
                logger.error(msg)
                raise ValidationError(msg)


@overload
def calculate_portfolio_volatility(
    covariance: CovarianceMatrix,
    weights: Sequence[Decimal],
) -> Decimal: ...


@overload
def calculate_portfolio_volatility(
    covariance: dict[str, dict[str, Decimal]],
    weights: dict[str, Decimal] | Sequence[Decimal],
) -> Decimal: ...


def calculate_portfolio_volatility(*args: Any, **_kwargs: Any) -> Decimal:
    """Calculate portfolio volatility using signed weights and covariance matrix.

    Args:
        *args: Variable length argument list. Automatically parses and identifies
            both (weights, covariance) and (covariance, weights) argument orders.
            covariance is either a CovarianceMatrix or dict[str, dict[str, Decimal]].
            weights is either a dict[str, Decimal] or Sequence[Decimal].
        **_kwargs: Arbitrary keyword arguments.

    Returns:
        Decimal: Calculated portfolio volatility.
    """
    logger.debug("Calculating portfolio volatility.")
    if len(args) < 2:
        return Decimal("0.0")

    arg1, arg2 = args[0], args[1]

    # Detect which argument is covariance and which is weights
    is_cov_first = False
    if isinstance(arg1, CovarianceMatrix):
        is_cov_first = True
    elif isinstance(arg1, dict) and len(arg1) > 0:
        first_val = next(iter(arg1.values()))
        if isinstance(first_val, dict):
            is_cov_first = True

    if is_cov_first:
        cov_arg = arg1
        weights_arg = arg2
    else:
        cov_arg = arg2
        weights_arg = arg1

    raw_matrix = cov_arg.matrix if isinstance(cov_arg, CovarianceMatrix) else cov_arg
    symbols = sorted(raw_matrix.keys())

    if not symbols:
        return Decimal("0.0")

    if isinstance(weights_arg, dict):
        weights_dict = weights_arg
        weights_seq = [weights_dict.get(s, Decimal("0.0")) for s in symbols]
    else:
        weights_seq = list(weights_arg)

    if len(weights_seq) != len(symbols):
        return Decimal("0.0")

    variance = Decimal("0.0")
    for i, s1 in enumerate(symbols):
        w1 = weights_seq[i]
        for j, s2 in enumerate(symbols):
            w2 = weights_seq[j]
            cov = raw_matrix[s1].get(s2, Decimal("0.0"))
            variance += w1 * w2 * cov

    if variance <= 0:
        return Decimal("0.0")

    return Decimal(str(math.sqrt(float(variance))))


def get_position_signed_exposure(
    symbol: str,
    quantity: Decimal,
    direction: str,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate signed exposure of a position in account currency.

    Args:
        symbol: The instrument symbol (e.g. "EURUSD").
        quantity: The position quantity.
        direction: Position direction ("buy", "sell", "long", "short").
        market_context: Market context containing configuration and rates.
        account_ccy: Base account currency.

    Returns:
        Decimal: Signed exposure amount.
    """
    logger.debug("Calculating signed exposure for position in %s.", symbol)
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))

    base_ccy, _ = _resolve_base_quote(symbol, market_context)
    sign = Decimal("1.0") if direction.lower() in {"buy", "long"} else Decimal("-1.0")
    base_exposure = abs(quantity) * contract_size * sign
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return base_exposure * rate


def get_proposed_trade_signed_exposure(
    proposed_trade: ProposedTrade,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate signed exposure of a proposed trade in account currency.

    Args:
        proposed_trade: Proposed trade details.
        market_context: Market context containing configuration and rates.
        account_ccy: Base account currency.

    Returns:
        Decimal: Signed exposure amount.
    """
    logger.debug("Calculating signed exposure for proposed trade.")
    symbol = proposed_trade.symbol
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))

    base_ccy, _ = _resolve_base_quote(symbol, market_context)
    sign = (
        Decimal("1.0")
        if proposed_trade.side.lower() in {"buy", "long"}
        else Decimal("-1.0")
    )
    base_exposure = proposed_trade.volume * contract_size * sign
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return base_exposure * rate


def align_multiple_return_series(
    returns_db: dict[str, dict[datetime, Decimal]],
) -> dict[str, list[Decimal]]:
    """Align multiple return series by their common timestamps.

    Args:
        returns_db: Dictionary mapping symbol to timestamped returns.

    Returns:
        dict[str, list[Decimal]]: Aligned returns dictionary.
    """
    logger.info("Aligning multiple returns series.")
    if not returns_db:
        return {}

    common_times = None
    for rets in returns_db.values():
        if common_times is None:
            common_times = set(rets.keys())
        else:
            common_times &= set(rets.keys())

    if not common_times:
        return {s: [] for s in returns_db}

    sorted_times = sorted(common_times)
    aligned: dict[str, list[Decimal]] = {}
    for s, rets in returns_db.items():
        aligned[s] = [rets[t] for t in sorted_times]
    return aligned


def _compute_exposures_and_weights(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    account_ccy: str,
) -> tuple[Decimal, dict[str, Decimal]]:
    """Compute gross exposure and net weights per symbol.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market context containing configuration and rates.
        account_ccy: Base account currency.

    Returns:
        tuple[Decimal, dict[str, Decimal]]: Total gross exposure
        and dictionary of net weights.
    """
    symbol_exposures: dict[str, Decimal] = {}
    for pos in portfolio_state.positions:
        symbol_exposures[pos.symbol] = symbol_exposures.get(
            pos.symbol, Decimal("0.0")
        ) + get_position_signed_exposure(
            pos.symbol, pos.quantity, pos.direction, market_context, account_ccy
        )

    if proposed_trade is not None:
        symbol_exposures[proposed_trade.symbol] = symbol_exposures.get(
            proposed_trade.symbol, Decimal("0.0")
        ) + get_proposed_trade_signed_exposure(
            proposed_trade, market_context, account_ccy
        )

    total_gross_exposure = sum(
        (abs(v) for v in symbol_exposures.values()), Decimal("0.0")
    )

    weights: dict[str, Decimal] = {}
    if total_gross_exposure > 0:
        for s, exp in symbol_exposures.items():
            weights[s] = exp / total_gross_exposure
    else:
        for s in symbol_exposures:
            weights[s] = Decimal("0.0")

    return total_gross_exposure, weights


def _prepare_aligned_returns(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    min_samples: int,
    exclude_last: bool,
) -> tuple[dict[str, list[Decimal]], Decimal, dict[str, Decimal]]:
    """Helper to parse, align and calculate weights for VaR/ES snapshots.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market context containing configuration and rates.
        min_samples: Minimum required return samples.
        exclude_last: Exclude the last bar.

    Returns:
        tuple[dict[str, list[Decimal]], Decimal, dict[str, Decimal]]: A tuple
        containing aligned returns, total gross exposure, and weights.

    Raises:
        ValidationError: If returned series cannot be aligned or samples
            are insufficient.
    """
    account_ccy = portfolio_state.currency.upper()
    symbols = {pos.symbol for pos in portfolio_state.positions}
    if proposed_trade is not None:
        symbols.add(proposed_trade.symbol)

    if not symbols:
        return {}, Decimal("0.0"), {}

    market_data = market_context.get("market_data", market_context)
    returns_db: dict[str, dict[datetime, Decimal]] = {}
    for s in symbols:
        bars = market_data.get(s, [])
        returns_db[s] = calculate_returns(
            bars, return_type="close_to_close", exclude_last=exclude_last
        )

    aligned_returns = align_multiple_return_series(returns_db)
    if not aligned_returns:
        msg = "Fail-Closed: Return series alignment returned empty dataset."
        logger.error(msg)
        raise ValidationError(msg)

    first_sym = next(iter(aligned_returns))
    sample_count = len(aligned_returns[first_sym])
    if sample_count < min_samples:
        msg = (
            f"Fail-Closed: Insufficient aligned samples "
            f"({sample_count} < {min_samples}) for VaR/ES calculations."
        )
        logger.error(msg)
        raise ValidationError(msg)

    total_gross_exposure, weights = _compute_exposures_and_weights(
        portfolio_state, proposed_trade, market_context, account_ccy
    )

    return aligned_returns, total_gross_exposure, weights


@overload
def calculate_parametric_var(request: VaRCalculationRequest) -> VaRSnapshot: ...


@overload
def calculate_parametric_var(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> Decimal: ...


def calculate_parametric_var(*args: Any, **kwargs: Any) -> Any:
    """Compute covariance/volatility-based VaR, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V2, the first argument is a
            VaRCalculationRequest. For V1, the arguments are:
            weights (dict[str, Decimal]), matrix (dict[str, dict[str, Decimal]]),
            confidence (Decimal), total_gross_exposure (Decimal).
        **kwargs: Keyword arguments. For V2, "request" can be passed. For V1,
            arguments like "weights", "matrix", "confidence",
            "total_gross_exposure" can be passed.

    Returns:
        VaRSnapshot | Decimal: The VaR snapshot for V2, or the VaR amount for V1.

    Raises:
        ValidationError: If returned calculations are non-finite or returns
            alignment fails.
    """
    logger.info("calculate_parametric_var entry.")

    is_v2 = False
    if (len(args) > 0 and isinstance(args[0], VaRCalculationRequest)) or (
        "request" in kwargs and isinstance(kwargs["request"], VaRCalculationRequest)
    ):
        is_v2 = True

    if is_v2:
        request: VaRCalculationRequest = args[0] if len(args) > 0 else kwargs["request"]
        aligned, gross_exposure, weights = _prepare_aligned_returns(
            request.portfolio_state,
            request.proposed_trade,
            request.market_context,
            request.min_samples,
            request.exclude_last,
        )

        if not aligned:
            return VaRSnapshot(
                method=str(VaRMethod.PARAMETRIC),
                confidence=request.confidence,
                portfolio_volatility=Decimal("0.0"),
                exposure=Decimal("0.0"),
                result=Decimal("0.0"),
                assumptions={},
            )

        sliced = {s: rets[-request.lookback :] for s, rets in aligned.items()}
        raw_matrix = calculate_covariance_matrix(
            sliced, method=request.cov_method, ewma_decay=request.ewma_decay
        )
        shrunk_matrix = shrink_covariance_matrix(
            raw_matrix, shrinkage_intensity=request.shrinkage_intensity
        )
        validate_covariance_matrix(shrunk_matrix)

        symbols = sorted(shrunk_matrix.keys())
        weights_seq = [weights[s] for s in symbols]
        vol = calculate_portfolio_volatility(shrunk_matrix, weights_seq)

        nd = NormalDist()
        z = Decimal(str(nd.inv_cdf(float(request.confidence))))
        var_val = z * vol * gross_exposure

        if not math.isfinite(float(vol)) or not math.isfinite(float(var_val)):
            msg = "Non-finite calculations detected in parametric VaR."
            logger.error(msg)
            raise ValidationError(msg)

        # Risk decomposition contributions
        crc: dict[str, Decimal] = {}
        if vol > 0:
            for s1 in symbols:
                sigma_w_i = sum(
                    shrunk_matrix[s1].get(s2, Decimal("0.0")) * weights[s2]
                    for s2 in symbols
                )
                mrc_val = sigma_w_i / vol
                crc_val = weights[s1] * z * mrc_val * gross_exposure
                crc[s1] = crc_val
        else:
            for s in symbols:
                crc[s] = Decimal("0.0")

        assumptions = {
            "covariance_method": request.cov_method,
            "ewma_decay": float(request.ewma_decay),
            "shrinkage_intensity": float(request.shrinkage_intensity),
            "component_contributions": {k: float(v) for k, v in crc.items()},
        }

        return VaRSnapshot(
            method=str(VaRMethod.PARAMETRIC),
            confidence=request.confidence,
            portfolio_volatility=vol,
            exposure=gross_exposure,
            result=var_val,
            assumptions=assumptions,
        )

    # V1 logic
    weights_v1: Any = (
        kwargs.get("weights")
        if kwargs.get("weights") is not None
        else (args[0] if len(args) > 0 else None)
    )
    matrix: Any = (
        kwargs.get("matrix")
        if kwargs.get("matrix") is not None
        else (args[1] if len(args) > 1 else None)
    )
    confidence: Any = (
        kwargs.get("confidence")
        if kwargs.get("confidence") is not None
        else (args[2] if len(args) > 2 else Decimal("0.95"))
    )
    total_gross_exposure: Any = (
        kwargs.get("total_gross_exposure")
        if kwargs.get("total_gross_exposure") is not None
        else (args[3] if len(args) > 3 else Decimal("0.0"))
    )

    vol = calculate_portfolio_volatility(matrix, weights_v1)
    nd = NormalDist()
    z = Decimal(str(nd.inv_cdf(float(confidence))))
    return z * vol * total_gross_exposure


@overload
def calculate_historical_var(request: VaRCalculationRequest) -> VaRSnapshot: ...


@overload
def calculate_historical_var(
    aligned_returns: dict[str, list[Decimal]],
    weights: dict[str, Decimal],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> Decimal: ...


def calculate_historical_var(*args: Any, **kwargs: Any) -> Any:
    """Compute empirical VaR from aligned returns, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V2, the first argument is a
            VaRCalculationRequest. For V1, the arguments are:
            aligned_returns (dict[str, list[Decimal]]), weights (dict[str, Decimal]),
            confidence (Decimal), total_gross_exposure (Decimal).
        **kwargs: Keyword arguments. For V2, "request" can be passed. For V1,
            arguments like "aligned_returns", "weights", "confidence",
            "total_gross_exposure" can be passed.

    Returns:
        VaRSnapshot | Decimal: The VaR snapshot for V2, or the VaR amount for V1.

    Raises:
        ValidationError: If returned calculations are non-finite or returns
            alignment fails.
    """
    logger.info("calculate_historical_var entry.")

    is_v2 = False
    if (len(args) > 0 and isinstance(args[0], VaRCalculationRequest)) or (
        "request" in kwargs and isinstance(kwargs["request"], VaRCalculationRequest)
    ):
        is_v2 = True

    if is_v2:
        request: VaRCalculationRequest = args[0] if len(args) > 0 else kwargs["request"]
        aligned, gross_exposure, weights = _prepare_aligned_returns(
            request.portfolio_state,
            request.proposed_trade,
            request.market_context,
            request.min_samples,
            request.exclude_last,
        )

        if not aligned:
            return VaRSnapshot(
                method=str(VaRMethod.HISTORICAL),
                confidence=request.confidence,
                portfolio_volatility=Decimal("0.0"),
                exposure=Decimal("0.0"),
                result=Decimal("0.0"),
                assumptions={},
            )

        sliced = {s: rets[-request.lookback :] for s, rets in aligned.items()}
        first_sym = next(iter(sliced))
        n = len(sliced[first_sym])

        port_returns = []
        symbols = sorted(weights.keys())
        for i in range(n):
            r_p = sum(weights[s] * sliced[s][i] for s in symbols)
            port_returns.append(r_p)

        port_returns.sort()
        idx = max(
            0, min(n - 1, int((Decimal("1.0") - request.confidence) * Decimal(n)))
        )
        var_pct = -port_returns[idx]
        var_val = var_pct * gross_exposure

        if not math.isfinite(float(var_val)):
            msg = "Non-finite calculation detected in historical VaR."
            logger.error(msg)
            raise ValidationError(msg)

        # Volatility estimation for representation
        raw_matrix = calculate_covariance_matrix(
            sliced, method=request.cov_method, ewma_decay=request.ewma_decay
        )
        shrunk_matrix = shrink_covariance_matrix(
            raw_matrix, shrinkage_intensity=request.shrinkage_intensity
        )
        weights_seq = [weights[s] for s in symbols]
        vol = calculate_portfolio_volatility(shrunk_matrix, weights_seq)

        return VaRSnapshot(
            method=str(VaRMethod.HISTORICAL),
            confidence=request.confidence,
            portfolio_volatility=vol,
            exposure=gross_exposure,
            result=var_val,
            assumptions={"sample_size": n},
        )

    # V1 logic
    aligned_returns: Any = (
        kwargs.get("aligned_returns")
        if kwargs.get("aligned_returns") is not None
        else (args[0] if len(args) > 0 else None)
    )
    weights_v1: Any = (
        kwargs.get("weights")
        if kwargs.get("weights") is not None
        else (args[1] if len(args) > 1 else None)
    )
    confidence: Any = (
        kwargs.get("confidence")
        if kwargs.get("confidence") is not None
        else (args[2] if len(args) > 2 else Decimal("0.95"))
    )
    total_gross_exposure: Any = (
        kwargs.get("total_gross_exposure")
        if kwargs.get("total_gross_exposure") is not None
        else (args[3] if len(args) > 3 else Decimal("0.0"))
    )

    first_sym = next(iter(aligned_returns))
    n = len(aligned_returns[first_sym])
    if n == 0:
        return Decimal("0.0")

    port_returns = []
    symbols = sorted(weights_v1.keys())
    for i in range(n):
        r_p = sum(weights_v1[s] * aligned_returns[s][i] for s in symbols)
        port_returns.append(r_p)

    port_returns.sort()
    idx = max(0, min(n - 1, int((Decimal("1.0") - confidence) * Decimal(n))))
    var_pct = -port_returns[idx]
    return var_pct * total_gross_exposure


def calculate_var_component_contribution(
    request: VaRCalculationRequest,
) -> ComponentRiskContribution:
    """Decompose Value-at-Risk component contributions.

    Args:
        request: Request containing details for VaR decomposition.

    Returns:
        ComponentRiskContribution: Calculated risk contributions.
    """
    logger.info("calculate_var_component_contribution called.")
    snap = calculate_parametric_var(request)
    contribs = snap.assumptions.get("component_contributions", {})
    typed_contribs = {k: Decimal(str(v)) for k, v in contribs.items()}
    return ComponentRiskContribution(contributions=typed_contribs)


class PortfolioVaREngine:
    """Engine for estimating portfolio Value-at-Risk."""

    def __init__(self, config: object) -> None:
        """Initialize PortfolioVaREngine.

        Args:
            config: Active configuration profile.
        """
        self.config = config

    def calculate_var(
        self,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
        proposed_trade: ProposedTrade | None = None,
        lookback: int = 50,
        confidence: Decimal = Decimal("0.95"),
        method: str = "parametric",
        cov_method: str = "parametric",
        ewma_decay: Decimal = Decimal("0.94"),
        shrinkage_intensity: Decimal = Decimal("0.1"),
        min_samples: int = 20,
        exclude_last: bool = True,
    ) -> Any:
        """Helper to calculate VaR, converting back to legacy V1 VaRResult.

        Args:
            portfolio_state: Current portfolio state.
            market_context: Market context containing returns/prices history.
            proposed_trade: Optional candidate proposed trade.
            lookback: Returns lookback length.
            confidence: Confidence level.
            method: VaR calculation method.
            cov_method: Covariance matrix calculation method.
            ewma_decay: EWMA decay factor.
            shrinkage_intensity: Shrinkage intensity.
            min_samples: Minimum required returns samples.
            exclude_last: Exclude the last bar.

        Returns:
            VaRResult: Encapsulated Value-at-Risk outputs.
        """
        logger.info("PortfolioVaREngine.calculate_var legacy call.")
        req = VaRCalculationRequest(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
            lookback=lookback,
            confidence=confidence,
            method=VaRMethod(method),
            cov_method=cov_method,
            ewma_decay=ewma_decay,
            shrinkage_intensity=shrinkage_intensity,
            min_samples=min_samples,
            exclude_last=exclude_last,
        )

        if req.method == VaRMethod.PARAMETRIC:
            snap = calculate_parametric_var(req)
        else:
            snap = calculate_historical_var(req)

        from app.services.risk.tail_risk.contracts import VaRResult

        return VaRResult(
            method=snap.method,
            confidence=snap.confidence,
            portfolio_volatility=snap.portfolio_volatility,
            exposure=snap.exposure,
            result=snap.result,
            assumptions=snap.assumptions,
        )


def calculate_risk_contributions(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    portfolio_vol: Decimal,
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Calculate marginal and component risk contributions.

    Args:
        weights: Signed portfolio weights.
        matrix: Covariance matrix dictionary.
        portfolio_vol: Portfolio volatility.
        confidence: Confidence level.
        total_gross_exposure: Total gross exposure.

    Returns:
        tuple[dict[str, Decimal], dict[str, Decimal]]: MRC and CRC.
    """
    logger.info("calculate_risk_contributions called.")
    symbols = sorted(weights.keys())
    mrc: dict[str, Decimal] = {}
    crc: dict[str, Decimal] = {}

    nd = NormalDist()
    z = Decimal(str(nd.inv_cdf(float(confidence))))

    if portfolio_vol <= 0:
        for s in symbols:
            mrc[s] = Decimal("0.0")
            crc[s] = Decimal("0.0")
        return mrc, crc

    for s1 in symbols:
        sigma_w_i = sum(
            matrix[s1].get(s2, Decimal("0.0")) * weights[s2] for s2 in symbols
        )
        mrc_val = sigma_w_i / portfolio_vol
        mrc[s1] = mrc_val
        crc_val = weights[s1] * z * mrc_val * total_gross_exposure
        crc[s1] = crc_val

    return mrc, crc


def calculate_risk_contribution(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    portfolio_vol: Decimal,
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Calculate marginal and component risk contributions.

    Args:
        weights: Signed portfolio weights.
        matrix: Covariance matrix dictionary.
        portfolio_vol: Portfolio volatility.
        confidence: Confidence level.
        total_gross_exposure: Total gross exposure.

    Returns:
        tuple[dict[str, Decimal], dict[str, Decimal]]: Marginal and
            component risk contributions.
    """
    return calculate_risk_contributions(
        weights=weights,
        matrix=matrix,
        portfolio_vol=portfolio_vol,
        confidence=confidence,
        total_gross_exposure=total_gross_exposure,
    )


def calculate_parametric_var_es(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculate parametric portfolio VaR and Expected Shortfall.

    Args:
        weights: Signed portfolio weights.
        matrix: Covariance matrix dictionary.
        confidence: Confidence level.
        total_gross_exposure: Total gross exposure.

    Returns:
        tuple[Decimal, Decimal, Decimal]: Volatility, VaR value,
            and Expected Shortfall value.
    """
    logger.info("calculate_parametric_var_es called.")
    vol = calculate_portfolio_volatility(matrix, weights)
    nd = NormalDist()
    z = Decimal(str(nd.inv_cdf(float(confidence))))
    var_val = z * vol * total_gross_exposure

    z_f = float(z)
    phi_z = Decimal(str(math.exp(-0.5 * z_f * z_f) / math.sqrt(2.0 * math.pi)))
    tail_prob = Decimal("1.0") - confidence
    if tail_prob <= 0:
        es_val = var_val
    else:
        es_val = vol * (phi_z / tail_prob) * total_gross_exposure

    return vol, var_val, es_val


def calculate_historical_var_es(
    aligned_returns: dict[str, list[Decimal]],
    weights: dict[str, Decimal],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[Decimal, Decimal]:
    """Calculate historical portfolio VaR and Expected Shortfall.

    Args:
        aligned_returns: Aligned return series.
        weights: Signed portfolio weights.
        confidence: Confidence level.
        total_gross_exposure: Total gross exposure.

    Returns:
        tuple[Decimal, Decimal]: VaR value and Expected Shortfall value.
    """
    logger.info("calculate_historical_var_es called.")
    if not aligned_returns:
        return Decimal("0.0"), Decimal("0.0")

    first_sym = next(iter(aligned_returns))
    n = len(aligned_returns[first_sym])
    if n == 0:
        return Decimal("0.0"), Decimal("0.0")

    port_returns = []
    symbols = sorted(weights.keys())
    for i in range(n):
        r_p = sum(weights[s] * aligned_returns[s][i] for s in symbols)
        port_returns.append(r_p)

    port_returns.sort()

    idx = max(0, min(n - 1, int((Decimal("1.0") - confidence) * Decimal(n))))
    var_pct = -port_returns[idx]

    tail_returns = port_returns[: idx + 1]
    if not tail_returns:
        es_pct = var_pct
    else:
        es_pct = -sum(tail_returns, Decimal("0.0")) / Decimal(len(tail_returns))

    return var_pct * total_gross_exposure, es_pct * total_gross_exposure
