"""Optimization scoring and metrics assessment.

Implements Sharpe, Sortino, Calmar, profit factor, total return, and
custom composite scoring functions.  Also implements Deflated Sharpe
Ratio (DSR), Multiple Testing Bias (MTB) correction, and nominal trial
count diagnostics.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Protocol

import numpy as np

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
_EULER_MASCHERONI: float = 0.5772156649015328
"""Euler-Mascheroni constant used in DSR expected-max Sharpe calculation."""

_DSR_PASS_THRESHOLD: float = 0.95
"""Minimum DSR probability to pass the multiple-testing bias gate."""

_MIN_SAMPLE_SIZE: int = 2
"""Minimum number of return observations required to compute a ratio."""

_MIN_SKEW_KURTOSIS_SAMPLES: int = 3
"""Minimum samples required for skewness/kurtosis estimation."""

_ANNUAL_TRADING_DAYS: float = 252.0
"""Standard annualisation factor for daily return statistics."""


# ---------------------------------------------------------------------------
# Scoring function protocol
# ---------------------------------------------------------------------------
class ScoringFunction(Protocol):
    """Protocol that all candidate scoring callables must satisfy."""

    def __call__(
        self,
        trades: list[dict[str, Any]],
        initial_balance: float,
    ) -> float:
        """Compute a scalar score from a list of realized trades.

        Args:
            trades: List of realized trade dictionaries.  Each dict
                must expose a ``"profit"`` key (float).
            initial_balance: Starting account balance used to compute
                return-based metrics.

        Returns:
            float: Scalar score; higher values indicate better
                performance.
        """
        ...


# ---------------------------------------------------------------------------
# Internal return helpers
# ---------------------------------------------------------------------------
def get_daily_returns(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> list[float]:
    """Group trade profits by close day and compute fractional returns.

    Args:
        trades: List of executed trades.  Each dict must expose
            ``"close_time"`` (or ``"close_timestamp"``) and
            ``"profit"`` keys.
        initial_balance: Starting account balance.

    Returns:
        list[float]: Daily fractional return values.
    """
    if not trades:
        return []
    daily_profits: dict[str, float] = {}
    for t in trades:
        close_time = t.get("close_time") or t.get("close_timestamp")
        if not close_time:
            continue
        if isinstance(close_time, str):
            try:
                dt = datetime.fromisoformat(close_time)
            except ValueError:
                dt = datetime.now(UTC)
        else:
            dt = close_time
        day = dt.date().isoformat()
        daily_profits[day] = daily_profits.get(day, 0.0) + float(t.get("profit", 0.0))
    return [p / initial_balance for p in daily_profits.values()]


# ---------------------------------------------------------------------------
# Drawdown helper
# ---------------------------------------------------------------------------
def calculate_max_drawdown(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate peak-to-trough maximum drawdown from trade sequence.

    Args:
        trades: List of realized trades ordered chronologically.
        initial_balance: Starting balance used as the initial peak.

    Returns:
        float: Maximum drawdown as a fraction of peak equity (0-1).
    """
    balance = initial_balance
    peak = balance
    max_dd = 0.0
    for t in trades:
        balance += float(t.get("profit", 0.0))
        peak = max(peak, balance)
        dd = (peak - balance) / peak if peak > 0.0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd


# ---------------------------------------------------------------------------
# Primary scoring functions
# ---------------------------------------------------------------------------
def total_return_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate total net return as a fraction of initial balance.

    Args:
        trades: Realized trades list.
        initial_balance: Starting balance.

    Returns:
        float: Total return fraction (e.g. 0.10 = 10 % return).
    """
    if not initial_balance:
        return 0.0
    net_profit = sum(float(t.get("profit", 0.0)) for t in trades)
    return float(net_profit / initial_balance)


def profit_factor_score(
    trades: list[dict[str, Any]],
    initial_balance: float,  # noqa: ARG001  # kept for ScoringFunction compat
) -> float:
    """Calculate profit factor (gross wins divided by absolute gross loss).

    Args:
        trades: Realized trades list.
        initial_balance: Unused; present for ``ScoringFunction`` protocol
            compatibility.

    Returns:
        float: Profit factor.  Returns gross-win total when there are no
            losing trades, and ``0.0`` when there are no trades at all.
    """
    wins = [
        float(t.get("profit", 0.0)) for t in trades if float(t.get("profit", 0.0)) > 0.0
    ]
    losses = [
        float(t.get("profit", 0.0)) for t in trades if float(t.get("profit", 0.0)) < 0.0
    ]
    if not losses:
        return float(sum(wins)) if wins else 0.0
    return float(sum(wins) / abs(sum(losses)))


def sharpe_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate annualized Sharpe ratio from daily returns.

    Args:
        trades: Realized trades list.
        initial_balance: Starting balance.

    Returns:
        float: Annualized Sharpe ratio.  Returns ``0.0`` when there are
            fewer than ``_MIN_SAMPLE_SIZE`` observations or zero return
            standard deviation.
    """
    returns = get_daily_returns(trades, initial_balance)
    if len(returns) < _MIN_SAMPLE_SIZE:
        return 0.0
    ret_std = float(np.std(returns, ddof=1))
    if ret_std == 0.0:
        return 0.0
    return float((np.mean(returns) / ret_std) * math.sqrt(_ANNUAL_TRADING_DAYS))


def sortino_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate annualized Sortino ratio from daily returns.

    Uses a zero minimum acceptable return (MAR) threshold; the downside
    deviation denominator is scaled against total observation count.

    Args:
        trades: Realized trades list.
        initial_balance: Starting balance.

    Returns:
        float: Annualized Sortino ratio.  Returns ``0.0`` when samples
            are insufficient or downside deviation is zero.
    """
    returns = get_daily_returns(trades, initial_balance)
    if len(returns) < _MIN_SAMPLE_SIZE:
        return 0.0
    downside_sq_sum = sum(r**2 for r in returns if r < 0.0)
    if downside_sq_sum == 0.0:
        return 0.0
    downside_std = math.sqrt(downside_sq_sum / len(returns))
    if downside_std == 0.0:
        return 0.0
    return float(
        (float(np.mean(returns)) / downside_std) * math.sqrt(_ANNUAL_TRADING_DAYS)
    )


def calmar_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate Calmar ratio (total return divided by max drawdown).

    Args:
        trades: Realized trades list.
        initial_balance: Starting balance.

    Returns:
        float: Calmar ratio.  Returns ``0.0`` when max drawdown is zero.
    """
    max_dd = calculate_max_drawdown(trades, initial_balance)
    if max_dd <= 0.0:
        return 0.0
    return float(total_return_score(trades, initial_balance) / max_dd)


def custom_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
) -> float:
    """Calculate weighted composite score from return, Sharpe, and drawdown.

    Weights:  ``0.4 * total_return + 0.4 * sharpe - 0.2 * max_drawdown``

    Args:
        trades: Realized trades list.
        initial_balance: Starting balance.

    Returns:
        float: Weighted composite score.
    """
    ret = total_return_score(trades, initial_balance)
    sharpe = sharpe_score(trades, initial_balance)
    max_dd = calculate_max_drawdown(trades, initial_balance)
    return float(0.4 * ret + 0.4 * sharpe - 0.2 * max_dd)


# ---------------------------------------------------------------------------
# Scoring function resolver
# ---------------------------------------------------------------------------
def optimization_get_scoring_func(name: str) -> ScoringFunction:
    """Resolve a supported objective name to its scoring function.

    Unrecognized names fall back to ``total_return_score``.

    Args:
        name: Objective name string (case-insensitive).

    Returns:
        ScoringFunction: Callable matching the ``ScoringFunction``
            protocol.
    """
    funcs: dict[str, ScoringFunction] = {
        "sharpe": sharpe_score,
        "sortino": sortino_score,
        "calmar": calmar_score,
        "profit_factor": profit_factor_score,
        "total_return": total_return_score,
        "custom": custom_score,
    }
    return funcs.get(name.strip().lower(), total_return_score)


# ---------------------------------------------------------------------------
# Normal-distribution inverse CDF approximation
# ---------------------------------------------------------------------------
def _norm_inv(p: float) -> float:
    """Inverse standard normal CDF via Beasley-Springer-Moro approximation.

    Uses ``scipy.stats.norm.ppf`` when available; falls back to the
    rational polynomial approximation.

    Args:
        p: Target probability (0 < p < 1).

    Returns:
        float: Standard normal quantile (Z-score).
    """
    try:
        from scipy.stats import norm

        return float(norm.ppf(p))
    except ImportError:
        pass

    if p <= 0.0 or p >= 1.0:
        return 0.0
    y = p - 0.5
    if abs(y) < 0.42:  # noqa: PLR2004
        r = y * y
        a = [
            2.50662823884,
            -18.61500062529,
            41.39119773534,
            -28.47609504908,
        ]
        b = [
            1.0,
            -8.47351093090,
            23.08336743743,
            -21.06224101826,
            3.13082909833,
        ]
        num = a[0] + r * (a[1] + r * (a[2] + r * a[3]))
        den = b[0] + r * (b[1] + r * (b[2] + r * (b[3] + r * b[4])))
        return y * num / den
    r = p if y < 0 else 1.0 - p
    s = math.log(-math.log(r))
    c = [2.92246467, 1.85957931, -0.08962697, -0.02244095]
    x = c[0] + s * (c[1] + s * (c[2] + s * c[3]))
    return -x if y < 0 else x


# ---------------------------------------------------------------------------
# Deflated Sharpe Ratio
# ---------------------------------------------------------------------------
def calculate_dsr(
    sharpe: float,
    trial_count: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
    t_samples: int = 100,
) -> float:
    """Calculate Deflated Sharpe Ratio (DSR) probability.

    Adjusts the observed Sharpe for multiple-testing bias using the
    expected maximum Sharpe under trial repetition.

    Args:
        sharpe: Observed annualized Sharpe ratio.
        trial_count: Number of optimization trials executed.
        skew: Skewness of the daily return distribution.
        kurtosis: Kurtosis of the daily return distribution.
        t_samples: Number of daily return observations.

    Returns:
        float: DSR probability fraction (0-1).  Higher values indicate
            the observed Sharpe is unlikely to be a false discovery.
    """
    if trial_count <= 1:
        return 1.0 if sharpe > 0.0 else 0.0

    z_inv = _norm_inv(1.0 - 1.0 / trial_count)
    z_inv_e = _norm_inv(1.0 - 1.0 / (trial_count * math.e))
    e_max = (1.0 - _EULER_MASCHERONI) * z_inv + _EULER_MASCHERONI * z_inv_e
    sr0 = e_max / math.sqrt(t_samples) if t_samples > 0 else 0.0

    if t_samples > 1:
        var_sr = (1.0 - skew * sharpe + ((kurtosis - 1.0) / 4.0) * (sharpe**2)) / (
            t_samples - 1
        )
    else:
        var_sr = 1.0

    if var_sr <= 0.0:
        return 0.0

    stat = (sharpe - sr0) / math.sqrt(var_sr)
    return 0.5 * (1.0 + math.erf(stat / math.sqrt(2.0)))


# ---------------------------------------------------------------------------
# Candidate evaluation
# ---------------------------------------------------------------------------
def evaluate_candidate_score(
    trades: list[dict[str, Any]],
    initial_balance: float,
    objective: str = "sharpe",
    trial_count: int = 1,
) -> dict[str, Any]:
    """Evaluate performance score and anti-overfitting metrics for a candidate.

    Computes the primary objective score alongside raw Sharpe, Deflated
    Sharpe Ratio, and Multiple Testing Bias gate metadata.

    Args:
        trades: Realized candidate trades.
        initial_balance: Starting balance.
        objective: Primary optimization objective name.
        trial_count: Number of unique candidate trials in the search.

    Returns:
        dict[str, Any]: Score and anti-overfitting metrics including:
            ``score``, ``raw_sharpe``, ``deflated_sharpe``,
            ``skewness``, ``kurtosis``, ``trade_count``,
            ``ending_balance``, ``net_profit``, ``max_drawdown``,
            ``multiple_testing_method``, ``mtb_pass_status``,
            ``mtb_rejection_reason``, and
            ``trial_count_independence_warning``.
    """
    func = optimization_get_scoring_func(objective)
    score = func(trades, initial_balance)

    raw_sr = sharpe_score(trades, initial_balance)
    returns = get_daily_returns(trades, initial_balance)

    skew = 0.0
    kurtosis = 3.0
    n = len(returns)
    if n >= _MIN_SKEW_KURTOSIS_SAMPLES:
        arr = np.array(returns)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        if std > 0.0:
            skew = float(np.mean((arr - mean) ** 3) / (std**3))
            kurtosis = float(np.mean((arr - mean) ** 4) / (std**4))

    t_samples = max(n, _MIN_SAMPLE_SIZE)
    dsr = calculate_dsr(raw_sr, trial_count, skew, kurtosis, t_samples)
    mtb_pass = bool(dsr >= _DSR_PASS_THRESHOLD)

    return {
        "score": score,
        "raw_sharpe": raw_sr,
        "deflated_sharpe": dsr,
        "skewness": skew,
        "kurtosis": kurtosis,
        "trade_count": len(trades),
        "ending_balance": (
            initial_balance + sum(float(t.get("profit", 0.0)) for t in trades)
        ),
        "net_profit": sum(float(t.get("profit", 0.0)) for t in trades),
        "max_drawdown": calculate_max_drawdown(trades, initial_balance),
        "multiple_testing_method": "deflated_sharpe_ratio",
        "mtb_pass_status": mtb_pass,
        "mtb_rejection_reason": (
            None if mtb_pass else "deflated_sharpe_ratio_below_95_percent"
        ),
        "trial_count_independence_warning": (
            trial_count_independence_warning(trial_count)
        ),
    }


# ---------------------------------------------------------------------------
# Candidate ranking
# ---------------------------------------------------------------------------
def rank_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sort parameter candidates deterministically by score and tie-breakers.

    Sort order (descending priority):
    1. ``score`` — descending (highest first).
    2. ``trade_count`` — descending (more trades first when tied);
       missing ``trade_count`` sorts last.
    3. ``candidate_hash`` — ascending (lexicographic tie-breaker).

    Implemented as three stable sort passes so each pass refines the
    previous without breaking its ordering guarantee.

    Args:
        candidates: List of candidate result dictionary blocks.

    Returns:
        list[dict[str, Any]]: Deterministically ranked candidate blocks.
    """
    # Pass 1: candidate_hash ascending
    result = sorted(
        candidates,
        key=lambda c: str(c.get("candidate_hash", "")),
    )
    # Pass 2: trade_count descending — None sorts last (uses sentinel -1)
    result.sort(
        key=lambda c: (
            float(c["trade_count"]) if c.get("trade_count") is not None else -1.0
        ),
        reverse=True,
    )
    # Pass 3: score descending
    result.sort(
        key=lambda c: float(c.get("score", 0.0)),
        reverse=True,
    )
    return result


# ---------------------------------------------------------------------------
# Nominal trial count
# ---------------------------------------------------------------------------
def nominal_trial_count(
    candidates: list[dict[str, Any]],
) -> int:
    """Calculate nominal trial count from unique candidate hashes.

    Counts unique ``candidate_hash`` values after canonical
    normalization, inactive-conditional exclusion, constraint rejection,
    and cache deduplication have already been applied by the caller.

    Args:
        candidates: List of candidate result dictionaries, each
            containing a ``"candidate_hash"`` key.

    Returns:
        int: Number of unique candidate hashes observed.
    """
    return len({c["candidate_hash"] for c in candidates if c.get("candidate_hash")})


def trial_count_independence_warning(
    trial_count: int,
    search_method: str = "grid",
) -> str | None:
    """Return a warning string when trial-count independence may be overstated.

    Bayesian and genetic methods produce correlated candidates; the
    nominal trial count should not be interpreted as statistically
    independent in those cases.

    Args:
        trial_count: Number of trials recorded.
        search_method: Algorithm that generated the candidates
            (e.g. ``"grid"``, ``"bayesian"``, ``"genetic"``).

    Returns:
        str | None: Warning string when correlation concerns apply,
            otherwise ``None``.
    """
    if trial_count < _MIN_SAMPLE_SIZE:
        return "Trial count is below minimum for reliable DSR estimation."
    if search_method in ("bayesian", "genetic"):
        return (
            f"nominal_trial_count may overstate independence: "
            f"'{search_method}' produces correlated candidates."
        )
    return None


# ---------------------------------------------------------------------------
# Pareto selection
# ---------------------------------------------------------------------------
def pareto_select(
    candidates: list[dict[str, Any]],
    objectives: list[str],
    initial_balance: float = 10000.0,
) -> list[dict[str, Any]]:
    """Perform deterministic Pareto front selection over multiple objectives.

    When only one objective is provided the single best-ranked candidate
    is returned.  Knee-point selection is not applied; all non-dominated
    candidates are returned.

    Args:
        candidates: Evaluated candidate dictionaries.
        objectives: Multi-objective metric names (see
            :func:`optimization_get_scoring_func` for supported values).
        initial_balance: Starting balance forwarded to scoring functions.

    Returns:
        list[dict[str, Any]]: Non-dominated (Pareto optimal) candidates.
    """
    if not candidates:
        return []
    if len(objectives) <= 1:
        ranked = rank_candidates(candidates)
        return [ranked[0]] if ranked else []

    candidate_scores: list[tuple[dict[str, Any], np.ndarray]] = []
    for c in candidates:
        scores = np.array(
            [
                optimization_get_scoring_func(obj)(c.get("trades", []), initial_balance)
                for obj in objectives
            ]
        )
        candidate_scores.append((c, scores))

    pareto_front = []
    for i, (c1, s1) in enumerate(candidate_scores):
        dominated = any(
            i != j and bool(np.all(s2 >= s1)) and bool(np.any(s2 > s1))
            for j, (_c2, s2) in enumerate(candidate_scores)
        )
        if not dominated:
            pareto_front.append(c1)

    return pareto_front
