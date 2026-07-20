"""Correlation matrix calculation, clustering, and portfolio risk impact services."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, overload

from app.services.risk.correlation.contracts import (
    AlignedReturns,
    ClusterExposureAssessment,
    ComponentRiskContribution,
    CorrelationCluster,
    CorrelationMethod,
    CovarianceMatrix,
)
from app.services.risk.correlation.returns import (
    align_return_series,
    calculate_pearson,
    calculate_returns,
)
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.exposure import (
    _resolve_base_quote,
    _resolve_conversion_rate,
)
from app.services.risk.models.contracts import (
    CorrelationSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
)
from app.services.risk.models.enums import RiskDecisionStatus
from app.utils.logger import logger


@overload
def calculate_correlation_matrix(
    returns: AlignedReturns,
    method: CorrelationMethod = CorrelationMethod.PEARSON,
) -> CorrelationSnapshot: ...


@overload
def calculate_correlation_matrix(
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    timeframe: str = "M1",
    method: str = "pearson",
    return_type: str = "close_to_close",
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> dict[str, dict[str, Decimal]]: ...


def calculate_correlation_matrix(*args: Any, **kwargs: Any) -> Any:
    """Compute pairwise Pearson correlation matrix.

    Supports both V1 and V2 signatures.
    """
    logger.info("calculate_correlation_matrix called.")
    if len(args) > 0 and isinstance(args[0], AlignedReturns):
        returns: AlignedReturns = args[0]
        method = args[1] if len(args) > 1 else CorrelationMethod.PEARSON

        matrix: dict[str, dict[str, Decimal]] = {}
        symbols = sorted(returns.returns.keys())
        for i, s1 in enumerate(symbols):
            if s1 not in matrix:
                matrix[s1] = {}
            matrix[s1][s1] = Decimal("1.0")

            for s2 in symbols[i + 1 :]:
                if s2 not in matrix:
                    matrix[s2] = {}

                corr = calculate_pearson(returns.returns[s1], returns.returns[s2])
                matrix[s1][s2] = corr
                matrix[s2][s1] = corr

        return CorrelationSnapshot(
            matrix=matrix,
            lookback=len(returns.timestamps),
            timeframe="M1",
            method=method.value if hasattr(method, "value") else str(method),
            sample_count=len(returns.timestamps),
            fallback_status=False,
        )

    # V1 logic
    raw_market_data = (
        kwargs.get("market_data") if kwargs.get("market_data") is not None else args[0]
    )
    market_data: dict[str, list[Any]] = (
        raw_market_data if isinstance(raw_market_data, dict) else {}
    )
    lookback = kwargs.get("lookback", 50)
    timeframe = kwargs.get("timeframe", "M1")
    method_str = kwargs.get("method", "pearson")
    return_type = kwargs.get("return_type", "close_to_close")
    min_samples = kwargs.get("min_samples", 20)
    fallback_correlation = kwargs.get("fallback_correlation")
    exclude_last = kwargs.get("exclude_last", True)

    snapshot = calculate_correlation_snapshot(
        market_data=market_data,
        lookback=lookback,
        timeframe=timeframe,
        method=method_str,
        return_type=return_type,
        min_samples=min_samples,
        fallback_correlation=fallback_correlation,
        exclude_last=exclude_last,
    )
    return snapshot.matrix


def _build_adjacency_list(
    symbols_list: list[str],
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
) -> dict[str, set[str]]:
    """Build adjacency list based on pairwise correlation threshold."""
    adj: dict[str, set[str]] = {s: set() for s in symbols_list}
    for i, s1 in enumerate(symbols_list):
        for s2 in symbols_list[i + 1 :]:
            corr = snapshot.matrix.get(s1, {}).get(s2)
            if corr is not None and abs(corr) >= threshold:
                adj[s1].add(s2)
                adj[s2].add(s1)
    return adj


def _find_connected_components(
    symbols_list: list[str],
    adj: dict[str, set[str]],
) -> list[list[str]]:
    """Group symbols into connected components (clusters)."""
    visited = set()
    clusters: list[list[str]] = []
    for s in symbols_list:
        if s not in visited:
            comp = []
            queue = [s]
            visited.add(s)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(comp)
    return clusters


def build_correlation_clusters(
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
) -> tuple[CorrelationCluster, ...]:
    """Group symbols into shared-risk clusters using pairwise correlation thresholds.

    Args:
        snapshot: Active correlation snapshot.
        threshold: Grouping threshold.

    Returns:
        tuple[CorrelationCluster, ...]: Set of symbol clusters.
    """
    logger.info("build_correlation_clusters called with threshold %s.", threshold)
    symbols_list = sorted(snapshot.matrix.keys())
    adj = _build_adjacency_list(symbols_list, snapshot, threshold)
    clusters = _find_connected_components(symbols_list, adj)

    # Sort components deterministically
    sorted_clusters = []
    for comp in clusters:
        sorted_clusters.append(sorted(comp))
    sorted_clusters.sort(key=lambda x: x[0])

    res = []
    for idx, comp in enumerate(sorted_clusters):
        res.append(CorrelationCluster(cluster_id=f"Cluster_{idx}", symbols=comp))
    return tuple(res)


@overload
def calculate_cluster_exposure(
    clusters: Sequence[CorrelationCluster],
    exposures: Mapping[str, Decimal],
) -> ClusterExposureAssessment: ...


@overload
def calculate_cluster_exposure(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> dict[str, Decimal]: ...


def calculate_cluster_exposure(*args: Any, **kwargs: Any) -> Any:
    """Calculate gross exposures for correlated clusters.

    Supports both V1 and V2 signatures.
    """
    logger.debug("calculate_cluster_exposure called.")
    if (
        len(args) == 2  # noqa: PLR2004
        and isinstance(args[0], (list, tuple, Sequence))
        and isinstance(args[1], (dict, Mapping))
    ):
        # V2 logic
        clusters: Sequence[CorrelationCluster] = args[0]
        exposures: Mapping[str, Decimal] = args[1]
        res = {}
        for c in clusters:
            c_exp = sum(
                (exposures.get(sym, Decimal("0.0")) for sym in c.symbols),
                Decimal("0.0"),
            )
            res[c.cluster_id] = c_exp
        return ClusterExposureAssessment(exposures=res)

    # V1 logic
    portfolio_state: PortfolioState = kwargs.get("portfolio_state") or args[0]
    proposed_trade: ProposedTrade | None = kwargs.get("proposed_trade") or args[1]
    snapshot: CorrelationSnapshot = kwargs.get("snapshot") or args[2]
    threshold: Decimal = kwargs.get("threshold") or args[3]
    market_context: dict[str, Any] = kwargs.get("market_context") or args[4]

    return calculate_cluster_exposures(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        snapshot=snapshot,
        threshold=threshold,
        market_context=market_context,
    )


def _get_symbol_gross_exposure(
    symbol: str,
    quantity: Decimal,
    _price: Decimal,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate gross exposure of a position/trade in account currency."""
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))
    base_ccy, _ = _resolve_base_quote(symbol, market_context)
    base_exposure = quantity * contract_size
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return abs(base_exposure * rate)


def _get_all_symbols(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
) -> set[str]:
    """Collect unique symbols from positions and proposed trade."""
    symbols = {pos.symbol for pos in portfolio_state.positions}
    if proposed_trade is not None:
        symbols.add(proposed_trade.symbol)
    return symbols


def _calculate_symbol_exposures(
    symbols: set[str],
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    account_ccy: str,
) -> dict[str, Decimal]:
    """Calculate gross exposure in account currency for each symbol."""
    sym_exposures: dict[str, Decimal] = {}
    for sym in symbols:
        gross = Decimal("0.0")
        for pos in portfolio_state.positions:
            if pos.symbol == sym:
                gross += _get_symbol_gross_exposure(
                    pos.symbol,
                    pos.quantity,
                    pos.current_price,
                    market_context,
                    account_ccy,
                )
        if proposed_trade is not None and proposed_trade.symbol == sym:
            p_price = proposed_trade.price
            if p_price <= 0:
                p_price = Decimal(str(market_context.get(f"{sym}_price", "1.0")))
            # gross exposure relies on quantity (lots size volume)
            gross += _get_symbol_gross_exposure(
                sym, proposed_trade.volume, p_price, market_context, account_ccy
            )
        sym_exposures[sym] = gross
    return sym_exposures


def calculate_cluster_exposures(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> dict[str, Decimal]:
    """Calculate gross exposure in account currency for correlated asset clusters."""
    logger.info("calculate_cluster_exposures called.")
    symbols = _get_all_symbols(portfolio_state, proposed_trade)
    account_ccy = portfolio_state.currency.upper()
    sym_exposures = _calculate_symbol_exposures(
        symbols, portfolio_state, proposed_trade, market_context, account_ccy
    )

    symbols_list = sorted(symbols)
    adj = _build_adjacency_list(symbols_list, snapshot, threshold)
    clusters = _find_connected_components(symbols_list, adj)

    sorted_clusters = []
    for comp in clusters:
        sorted_clusters.append(sorted(comp))
    sorted_clusters.sort(key=lambda x: x[0])

    cluster_exposures: dict[str, Decimal] = {}
    for idx, comp in enumerate(sorted_clusters):
        c_name = f"Cluster_{idx}"
        c_exp = sum((sym_exposures[sym] for sym in comp), Decimal("0.0"))
        cluster_exposures[c_name] = c_exp

    return cluster_exposures


def calculate_symbol_cluster_exposure(
    symbol: str,
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> Decimal:
    """Calculate gross exposure for the cluster containing a specific symbol."""
    logger.info("calculate_symbol_cluster_exposure called.")
    symbols = _get_all_symbols(portfolio_state, proposed_trade)
    if symbol not in symbols:
        return Decimal("0.0")

    account_ccy = portfolio_state.currency.upper()
    sym_exposures = _calculate_symbol_exposures(
        symbols, portfolio_state, proposed_trade, market_context, account_ccy
    )

    symbols_list = sorted(symbols)
    adj = _build_adjacency_list(symbols_list, snapshot, threshold)
    clusters = _find_connected_components(symbols_list, adj)

    for comp in clusters:
        if symbol in comp:
            return sum((sym_exposures[sym] for sym in comp), Decimal("0.0"))

    return Decimal("0.0")


def calculate_component_risk_contribution(
    covariance: CovarianceMatrix,
    weights: Sequence[Decimal],
) -> ComponentRiskContribution:
    """Compute contribution per component symbol based on weights and covariance.

    Args:
        covariance: Calculated covariance matrix.
        weights: Allocation weights vector corresponding to alphabetical symbols.

    Returns:
        ComponentRiskContribution: Marginal risk contribution mapping.
    """
    logger.info("calculate_component_risk_contribution called.")
    symbols = sorted(covariance.matrix.keys())
    n = len(symbols)
    if n == 0 or len(weights) != n:
        return ComponentRiskContribution(contributions={})

    # Sigma * w
    sigma_w: dict[str, Decimal] = {}
    for s1 in symbols:
        val = Decimal("0.0")
        for j, s2 in enumerate(symbols):
            val += covariance.matrix[s1][s2] * weights[j]
        sigma_w[s1] = val

    # w^T * Sigma * w
    w_sigma_w = Decimal("0.0")
    for i, s1 in enumerate(symbols):
        w_sigma_w += weights[i] * sigma_w[s1]

    port_vol = (
        Decimal(str(math.sqrt(float(w_sigma_w)))) if w_sigma_w > 0 else Decimal("0.0")
    )

    contributions = {}
    for i, s1 in enumerate(symbols):
        contributions[s1] = (
            (weights[i] * sigma_w[s1] / port_vol) if port_vol > 0 else Decimal("0.0")
        )

    return ComponentRiskContribution(contributions=contributions)


def calculate_portfolio_returns(
    portfolio_state: PortfolioState,
    market_data: dict[str, list[Any]],
    return_type: str = "close_to_close",
    exclude_last: bool = True,
) -> dict[datetime, Decimal]:
    """Calculate weighted historical portfolio returns (V1 compatibility wrapper)."""
    logger.info("calculate_portfolio_returns called.")
    positions = portfolio_state.positions
    if not positions:
        return {}

    pos_returns: dict[str, dict[datetime, Decimal]] = {}
    total_gross_size = sum(abs(pos.quantity) for pos in positions)

    if total_gross_size == 0:
        return {}

    weights: dict[str, Decimal] = {}
    for pos in positions:
        pos_returns[pos.symbol] = calculate_returns(
            market_data.get(pos.symbol, []), return_type, exclude_last
        )
        weights[pos.symbol] = abs(pos.quantity) / total_gross_size

    common_times = None
    for rets in pos_returns.values():
        if common_times is None:
            common_times = set(rets.keys())
        else:
            common_times &= set(rets.keys())

    if not common_times:
        return {}

    portfolio_returns: dict[datetime, Decimal] = {}
    for t in sorted(common_times):
        weighted_ret = Decimal("0.0")
        for pos in positions:
            direction = pos.direction.lower()
            sign = Decimal("1.0") if direction in {"buy", "long"} else Decimal("-1.0")
            weighted_ret += weights[pos.symbol] * sign * pos_returns[pos.symbol][t]
        portfolio_returns[t] = weighted_ret

    return portfolio_returns


def calculate_marginal_correlation(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade,
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    return_type: str = "close_to_close",
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> tuple[Decimal, bool]:
    """Calculate marginal correlation coefficient of proposed trade with portfolio."""
    logger.info("calculate_marginal_correlation called.")
    candidate_sym = proposed_trade.symbol
    candidate_rets = calculate_returns(
        market_data.get(candidate_sym, []), return_type, exclude_last
    )

    if not portfolio_state.positions:
        return Decimal("0.0"), False

    port_rets = calculate_portfolio_returns(
        portfolio_state, market_data, return_type, exclude_last
    )

    aligned_p, aligned_c = align_return_series(port_rets, candidate_rets)
    n = len(aligned_p)

    if n > lookback:
        aligned_p = aligned_p[-lookback:]
        aligned_c = aligned_c[-lookback:]
        n = lookback

    if n < min_samples:
        if fallback_correlation is not None:
            return Decimal(str(fallback_correlation)), True
        msg = (
            f"Insufficient aligned sample size ({n} < {min_samples}) "
            f"between portfolio and proposed trade asset {candidate_sym}."
        )
        raise ValidationError(msg)

    corr = calculate_pearson(aligned_p, aligned_c)

    trade_side = ""
    if hasattr(proposed_trade, "side") and proposed_trade.side is not None:
        trade_side = str(proposed_trade.side).lower()
    else:
        trade_side = str(getattr(proposed_trade, "direction", "")).lower()
    if trade_side in {"sell", "short"}:
        corr = -corr

    return corr, False


def calculate_correlation_multiplier(
    marginal_correlation: Decimal,
    config_multiplier_factor: Decimal = Decimal("0.5"),
) -> Decimal:
    """Calculate the correlation-adjusted sizing multiplier."""
    logger.info("calculate_correlation_multiplier called.")
    if marginal_correlation <= 0:
        return Decimal("1.0")
    mult = Decimal("1.0") - marginal_correlation * config_multiplier_factor
    return max(Decimal("0.1"), min(Decimal("1.0"), mult))


def detect_correlation_spikes(
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
) -> list[tuple[str, str, Decimal]]:
    """Detect asset pairs whose correlation exceeds the given threshold."""
    logger.info("detect_correlation_spikes called.")
    spikes = []
    symbols = sorted(snapshot.matrix.keys())
    for i, s1 in enumerate(symbols):
        for s2 in symbols[i + 1 :]:
            corr = snapshot.matrix[s1].get(s2)
            if corr is not None and abs(corr) >= threshold:
                spikes.append((s1, s2, corr))
    return spikes


def evaluate_proposed_trade_correlation(
    proposed_trade: ProposedTrade,
    portfolio_state: PortfolioState,
    snapshot: CorrelationSnapshot,
    config: RiskConfig,
    market_context: dict[str, Any],
) -> tuple[RiskDecisionStatus, Decimal, str]:
    """Evaluate a proposed trade's correlation impact and recommend action."""
    logger.info("evaluate_proposed_trade_correlation called.")
    if not portfolio_state.positions:
        return (
            RiskDecisionStatus.APPROVE,
            proposed_trade.volume,
            "Portfolio has no active positions.",
        )

    market_data = market_context.get("market_data")
    if not isinstance(market_data, dict):
        market_data = market_context

    env = market_context.get("environment", "local")
    is_live = env in {
        "paper",
        "shadow",
        "live_readonly",
        "micro_live",
        "full_live",
    } or getattr(config, "allow_live_execution", False)
    fallback_val = Decimal("1.0") if is_live else Decimal("0.0")

    min_samples = int(
        market_context.get(
            "min_correlation_samples",
            getattr(config, "min_correlation_samples", 20),
        )
    )

    try:
        marginal_corr, _ = calculate_marginal_correlation(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_data=market_data,
            lookback=snapshot.lookback,
            return_type=snapshot.method
            if snapshot.method
            in {
                "close_to_close",
                "log",
                "open_to_close",
                "sigma_normalized",
            }
            else "close_to_close",
            min_samples=min_samples,
            fallback_correlation=fallback_val,
            exclude_last=True,
        )
    except (ValueError, TypeError, KeyError, ValidationError) as e:
        logger.warning("Failed to calculate marginal correlation, falling back: %s", e)
        marginal_corr = fallback_val

    threshold = config.correlation_threshold
    reject_thresh = min(
        Decimal("0.95"),
        max(Decimal("0.80"), threshold * Decimal("1.5")),
    )

    if abs(marginal_corr) >= reject_thresh:
        return (
            RiskDecisionStatus.REJECT,
            Decimal("0.0"),
            f"Marginal correlation {marginal_corr:.2f} exceeds "
            f"hard rejection ceiling of {reject_thresh:.2f}.",
        )

    if abs(marginal_corr) >= threshold:
        mult = calculate_correlation_multiplier(
            marginal_corr,
            config_multiplier_factor=Decimal("0.5"),
        )
        adjusted_vol = proposed_trade.volume * mult

        sym = proposed_trade.symbol
        volume_step = market_context.get(f"{sym}_volume_step") or market_context.get(
            "volume_step"
        )
        if volume_step is not None:
            v_step = Decimal(str(volume_step))
            adjusted_vol = (adjusted_vol / v_step).quantize(
                Decimal(1), rounding="ROUND_DOWN"
            ) * v_step

        return (
            RiskDecisionStatus.REDUCE_SIZE,
            adjusted_vol,
            f"Marginal correlation {marginal_corr:.2f} exceeds "
            f"threshold {threshold:.2f}. Sizing reduced by factor of "
            f"{mult:.2f}.",
        )

    return (
        RiskDecisionStatus.APPROVE,
        proposed_trade.volume,
        f"Marginal correlation {marginal_corr:.2f} within safe "
        f"threshold {threshold:.2f}.",
    )


class CorrelationEngine:
    """Orchestrator for correlation calculations and cluster risk analysis."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        """Initialize orchestrator.

        Args:
            config: Optional active risk config profile settings.
        """
        self.config = config

    def calculate_returns(
        self,
        bars: list[Any],
        return_type: str,
        exclude_last: bool = True,
    ) -> dict[datetime, Decimal]:
        """Calculate returns series for a list of bars."""
        logger.info("CorrelationEngine.calculate_returns called.")
        return calculate_returns(bars, return_type, exclude_last)

    def align_return_series(
        self,
        returns_a: dict[datetime, Decimal],
        returns_b: dict[datetime, Decimal],
    ) -> tuple[list[Decimal], list[Decimal]]:
        """Align two return series by common timestamps."""
        logger.info("CorrelationEngine.align_return_series called.")
        return align_return_series(returns_a, returns_b)

    def calculate_correlation_matrix(
        self,
        market_data: dict[str, list[Any]],
        lookback: int = 50,
        timeframe: str = "M1",
        method: str = "pearson",
        return_type: str = "close_to_close",
        min_samples: int = 20,
        fallback_correlation: Decimal | None = None,
        exclude_last: bool = True,
    ) -> dict[str, dict[str, Decimal]]:
        """Compute rolling correlation matrix for multiple symbol price series."""
        logger.info("CorrelationEngine.calculate_correlation_matrix called.")
        snapshot = calculate_correlation_snapshot(
            market_data=market_data,
            lookback=lookback,
            timeframe=timeframe,
            method=method,
            return_type=return_type,
            min_samples=min_samples,
            fallback_correlation=fallback_correlation,
            exclude_last=exclude_last,
        )
        return snapshot.matrix

    def calculate_correlation_impact(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade,
        market_data: dict[str, list[Any]],
        lookback: int = 50,
        return_type: str = "close_to_close",
        min_samples: int = 20,
        fallback_correlation: Decimal | None = None,
        exclude_last: bool = True,
    ) -> Decimal:
        """Compute marginal correlation impact of a proposed trade."""
        logger.info("CorrelationEngine.calculate_correlation_impact called.")
        corr, _ = calculate_marginal_correlation(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_data=market_data,
            lookback=lookback,
            return_type=return_type,
            min_samples=min_samples,
            fallback_correlation=fallback_correlation,
            exclude_last=exclude_last,
        )
        return corr

    def calculate_cluster_exposure(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        snapshot: CorrelationSnapshot,
        threshold: Decimal,
        market_context: dict[str, Any],
    ) -> dict[str, Decimal]:
        """Calculate gross exposure for correlated asset clusters."""
        logger.info("CorrelationEngine.calculate_cluster_exposure called.")
        return calculate_cluster_exposures(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            snapshot=snapshot,
            threshold=threshold,
            market_context=market_context,
        )


def calculate_correlation_snapshot(
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    timeframe: str = "M1",
    method: str = "pearson",
    return_type: str = "close_to_close",
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> CorrelationSnapshot:
    """Compute rolling correlation matrix for multiple symbol price series."""
    logger.info("calculate_correlation_snapshot called.")
    symbols = sorted(market_data.keys())
    returns_db: dict[str, dict[datetime, Decimal]] = {}
    for sym in symbols:
        returns_db[sym] = calculate_returns(market_data[sym], return_type, exclude_last)

    matrix: dict[str, dict[str, Decimal]] = {}
    fallback_applied = False
    total_aligned_samples = 0

    for i, s1 in enumerate(symbols):
        if s1 not in matrix:
            matrix[s1] = {}
        matrix[s1][s1] = Decimal("1.0")

        for s2 in symbols[i + 1 :]:
            if s2 not in matrix:
                matrix[s2] = {}

            aligned_1, aligned_2 = align_return_series(returns_db[s1], returns_db[s2])
            n = len(aligned_1)
            total_aligned_samples = max(total_aligned_samples, n)

            if n > lookback:
                aligned_1 = aligned_1[-lookback:]
                aligned_2 = aligned_2[-lookback:]
                n = lookback

            if n < min_samples:
                if fallback_correlation is not None:
                    corr = Decimal(str(fallback_correlation))
                    fallback_applied = True
                else:
                    msg = (
                        f"Insufficient aligned sample size ({n} < {min_samples}) "
                        f"for pair {s1}-{s2}."
                    )
                    raise ValidationError(msg)
            else:
                corr = calculate_pearson(aligned_1, aligned_2)

            matrix[s1][s2] = corr
            matrix[s2][s1] = corr

    return CorrelationSnapshot(
        matrix=matrix,
        lookback=lookback,
        timeframe=timeframe,
        method=method,
        sample_count=total_aligned_samples,
        fallback_status=fallback_applied,
    )


def calculate_correlation_impact(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade,
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    return_type: str = "close_to_close",
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> Decimal:
    """Compute marginal correlation impact of a proposed trade before approval.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Proposed trade candidate.
        market_data: Historical price bars for symbols.
        lookback: Maximum number of return samples.
        return_type: Return formula type.
        min_samples: Minimum required samples.
        fallback_correlation: Fallback value if samples are insufficient.
        exclude_last: Exclude the last bar.

    Returns:
        Decimal: Pearson marginal correlation coefficient.
    """
    logger.info("calculate_correlation_impact called.")
    corr, _ = calculate_marginal_correlation(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_data=market_data,
        lookback=lookback,
        return_type=return_type,
        min_samples=min_samples,
        fallback_correlation=fallback_correlation,
        exclude_last=exclude_last,
    )
    return corr
