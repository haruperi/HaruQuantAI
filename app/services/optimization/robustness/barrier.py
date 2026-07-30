"""Deterministic first-passage simulation under Risk firm mandates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any, cast

import numpy as np

from app.services.optimization.errors import OptimizationError
from app.services.risk import get_drawdown_mode
from app.utils import get_logger

logger = get_logger(__name__)

DrawdownMode = Any
FirmMandate = Any
_MIN_OBSERVATIONS = 2
_PSD_EIGENVALUE_TOLERANCE = -1e-10


def _probability(count: int, total: int) -> Decimal:
    """Return an exact decimal empirical probability."""
    return Decimal(count) / Decimal(total)


@dataclass(frozen=True)
class FirstPassageReport:
    """Outcome distribution for one mandate and one return process."""

    mandate_version: str
    mode: DrawdownMode
    paths: int
    seed: int
    probability_target: Decimal
    probability_daily_breach: Decimal
    probability_drawdown_breach: Decimal
    probability_expired: Decimal
    median_termination_day: Decimal | None


@dataclass(frozen=True)
class JointFirstPassageReport:
    """Joint account-survival distribution from one correlated simulation."""

    paths: int
    seed: int
    account_ids: tuple[str, ...]
    surviving_accounts_distribution: Mapping[int, Decimal]
    probability_none_survive: Decimal
    measured_correlation: Mapping[str, Decimal]


def _checked_returns(returns: Sequence[Decimal]) -> tuple[Decimal, ...]:
    """Validate a measured non-empty return sample.

    Args:
        returns: Fractional daily returns.

    Returns:
        Finite return observations.

    Raises:
        OptimizationError: If fewer than two finite observations are supplied.
    """
    sample = tuple(returns)
    if len(sample) < _MIN_OBSERVATIONS or any(
        not value.is_finite() for value in sample
    ):
        raise OptimizationError("OPT_INVALID_REQUEST", "INSUFFICIENT_RETURNS")
    return sample


def _target_amount(mandate: FirmMandate) -> Decimal:
    """Resolve a mandate profit target in account currency.

    Args:
        mandate: Verified firm mandate.

    Returns:
        Absolute target amount.

    Raises:
        OptimizationError: If the mandate target is missing.
    """
    target = mandate.profit_target
    if target.value_absolute is not None:
        return cast("Decimal", target.value_absolute)
    if target.value is None:
        raise OptimizationError("OPT_INVALID_REQUEST", "TARGET_MISSING")
    return cast("Decimal", mandate.initial_balance) * cast("Decimal", target.value)


def _loss_limit(mandate: FirmMandate, equity: Decimal) -> Decimal:
    """Resolve the daily loss limit for the current equity state.

    Args:
        mandate: Verified firm mandate.
        equity: Current reference equity.

    Returns:
        Absolute daily loss limit.

    Raises:
        OptimizationError: If the mandate daily limit is missing.
    """
    rule = mandate.daily_loss
    if rule.value_absolute is not None:
        return cast("Decimal", rule.value_absolute)
    if rule.value is None:
        raise OptimizationError("OPT_INVALID_REQUEST", "DAILY_LIMIT_MISSING")
    basis = {
        "initial_balance": mandate.initial_balance,
        "current_balance": equity,
        "equity": equity,
    }[rule.basis]
    return cast("Decimal", basis) * cast("Decimal", rule.value)


def _drawdown_floor(
    mandate: FirmMandate,
    *,
    initial: Decimal,
    peak_eod: Decimal,
    peak_intraday: Decimal,
) -> Decimal:
    """Resolve the current absolute drawdown floor.

    Args:
        mandate: Verified firm mandate.
        initial: Initial account balance.
        peak_eod: Highest end-of-day balance observed.
        peak_intraday: Highest intraday equity observed.

    Returns:
        Current absolute drawdown floor.

    Raises:
        OptimizationError: If the mandate drawdown limit is missing.
    """
    rule = mandate.max_drawdown
    loss = rule.value_absolute
    if loss is None:
        if rule.value is None:
            raise OptimizationError("OPT_INVALID_REQUEST", "DRAWDOWN_LIMIT_MISSING")
        loss = initial * cast("Decimal", rule.value)
    reference = {
        get_drawdown_mode("STATIC"): initial,
        get_drawdown_mode("TRAILING_EOD"): peak_eod,
        get_drawdown_mode("TRAILING_INTRADAY"): peak_intraday,
    }[rule.mode]
    floor = reference - cast("Decimal", loss)
    return min(floor, initial) if bool(rule.trail_stops_at_initial) else floor


def _evaluate_path(
    returns: Sequence[Decimal], mandate: FirmMandate
) -> tuple[str, int | None]:
    """Evaluate one already-sampled path against its absorbing barriers.

    Args:
        returns: One sampled fractional return path.
        mandate: Verified firm mandate.

    Returns:
        Terminal outcome name and first terminating day, if any.
    """
    initial = mandate.initial_balance
    equity = initial
    peak_eod = initial
    peak_intraday = initial
    for day, daily_return in enumerate(returns, start=1):
        start_equity = equity
        equity *= Decimal(1) + daily_return
        if equity <= 0:
            return "drawdown_breach", day
        peak_intraday = max(peak_intraday, equity)
        daily_loss = max(Decimal(0), start_equity - equity)
        if daily_loss > _loss_limit(mandate, start_equity):
            return "daily_breach", day
        if equity < _drawdown_floor(
            mandate,
            initial=initial,
            peak_eod=peak_eod,
            peak_intraday=peak_intraday,
        ):
            return "drawdown_breach", day
        if equity >= initial + _target_amount(mandate):
            return "target", day
        peak_eod = max(peak_eod, equity)
    return "expired", None


def _report(
    outcomes: Sequence[tuple[str, int | None]],
    mandate: FirmMandate,
    *,
    paths: int,
    seed: int,
) -> FirstPassageReport:
    """Aggregate path outcomes into an immutable report.

    Args:
        outcomes: Terminal outcome and day pairs.
        mandate: Mandate used for the paths.
        paths: Number of simulated paths.
        seed: Seed used for reproducibility.

    Returns:
        Immutable first-passage report.
    """
    counts = {
        name: sum(outcome == name for outcome, _ in outcomes)
        for name in (
            "target",
            "daily_breach",
            "drawdown_breach",
            "expired",
        )
    }
    days = sorted(day for _, day in outcomes if day is not None)
    median = None
    if days:
        midpoint = len(days) // 2
        median = (
            Decimal(days[midpoint])
            if len(days) % 2
            else (Decimal(days[midpoint - 1]) + Decimal(days[midpoint])) / Decimal(2)
        )
    return FirstPassageReport(
        mandate_version=mandate.mandate_version,
        mode=mandate.max_drawdown.mode,
        paths=paths,
        seed=seed,
        probability_target=_probability(counts["target"], paths),
        probability_daily_breach=_probability(counts["daily_breach"], paths),
        probability_drawdown_breach=_probability(counts["drawdown_breach"], paths),
        probability_expired=_probability(counts["expired"], paths),
        median_termination_day=median,
    )


def estimate_first_passage(
    returns: Sequence[Decimal],
    mandate: FirmMandate,
    *,
    paths: int,
    seed: int,
) -> FirstPassageReport:
    """Estimate first-passage probabilities by seeded empirical bootstrap.

    Args:
        returns: Measured fractional daily returns.
        mandate: Verified firm mandate.
        paths: Positive number of seeded paths.
        seed: Deterministic random seed.

    Returns:
        First-passage outcome report.

    Raises:
        OptimizationError: If inputs are insufficient or the mandate is invalid.
    """
    logger.info("Estimating Optimization first-passage outcomes")
    sample = _checked_returns(returns)
    if paths <= 0 or not isinstance(seed, int) or not mandate.verified:
        raise OptimizationError("OPT_INVALID_REQUEST", "BARRIER_INPUT_INVALID")
    outcomes: list[tuple[str, int | None]] = []
    rng = np.random.default_rng(seed)
    for _ in range(paths):
        indices = rng.integers(0, len(sample), size=len(sample))
        sampled = tuple(sample[int(index)] for index in indices)
        outcomes.append(_evaluate_path(sampled, mandate))
    return _report(outcomes, mandate, paths=paths, seed=seed)


def _correlation_matrix(
    returns_by_account: Mapping[str, Sequence[Decimal]],
) -> tuple[tuple[str, ...], np.ndarray]:
    """Build and validate the measured account correlation matrix.

    Args:
        returns_by_account: Account-keyed aligned fractional returns.

    Returns:
        Sorted account IDs and their measured correlation matrix.

    Raises:
        OptimizationError: If the account set, alignment, or matrix is invalid.
    """
    account_ids = tuple(sorted(returns_by_account))
    if len(account_ids) < _MIN_OBSERVATIONS:
        raise OptimizationError("OPT_INVALID_REQUEST", "JOINT_ACCOUNT_SET")
    lengths = {len(returns_by_account[account_id]) for account_id in account_ids}
    if len(lengths) != 1 or next(iter(lengths)) < _MIN_OBSERVATIONS:
        raise OptimizationError("OPT_INVALID_REQUEST", "JOINT_ALIGNMENT")
    matrix = np.asarray(
        [
            [float(value) for value in returns_by_account[account_id]]
            for account_id in account_ids
        ],
        dtype=float,
    )
    correlation = np.corrcoef(matrix)
    if not np.all(np.isfinite(correlation)):
        raise OptimizationError("OPT_INVALID_REQUEST", "JOINT_CORRELATION")
    eigenvalues = np.linalg.eigvalsh(correlation)
    if float(np.min(eigenvalues)) < _PSD_EIGENVALUE_TOLERANCE:
        raise OptimizationError("OPT_INVALID_REQUEST", "NON_PSD_CORRELATION")
    return account_ids, correlation


def estimate_joint_first_passage(
    returns_by_account: Mapping[str, Sequence[Decimal]],
    mandates: Mapping[str, FirmMandate],
    *,
    paths: int,
    seed: int,
) -> JointFirstPassageReport:
    """Estimate joint account survival using measured cross-account correlation.

    Args:
        returns_by_account: Account-keyed aligned measured returns.
        mandates: Account-keyed verified mandates.
        paths: Positive number of seeded paths.
        seed: Deterministic random seed.

    Returns:
        Joint first-passage survival distribution.

    Raises:
        OptimizationError: If account keys, returns, or correlation are invalid.
    """
    logger.info("Estimating Optimization joint first-passage outcomes")
    if set(returns_by_account) != set(mandates) or paths <= 0:
        raise OptimizationError("OPT_INVALID_REQUEST", "JOINT_ACCOUNT_KEYS")
    account_ids, correlation = _correlation_matrix(returns_by_account)
    try:
        cholesky = np.linalg.cholesky(correlation)
    except np.linalg.LinAlgError as error:
        raise OptimizationError("OPT_INVALID_REQUEST", "NON_PSD_CORRELATION") from error
    sorted_returns = {
        account_id: np.sort(
            np.asarray([float(value) for value in returns_by_account[account_id]])
        )
        for account_id in account_ids
    }
    rng = np.random.default_rng(seed)
    survivor_counts = dict.fromkeys(range(len(account_ids) + 1), 0)
    for _ in range(paths):
        innovations = rng.standard_normal(
            (len(next(iter(sorted_returns.values()))), len(account_ids))
        )
        correlated = innovations @ cholesky.T
        sampled_by_account: dict[str, tuple[Decimal, ...]] = {}
        for column, account_id in enumerate(account_ids):
            ranks = np.argsort(np.argsort(correlated[:, column]))
            values = sorted_returns[account_id]
            sampled_by_account[account_id] = tuple(
                Decimal(str(values[int(rank)])) for rank in ranks
            )
        survivors = 0
        for account_id in account_ids:
            outcome, _ = _evaluate_path(
                sampled_by_account[account_id], mandates[account_id]
            )
            survivors += outcome == "target"
        survivor_counts[survivors] += 1
    distribution = MappingProxyType(
        {count: _probability(value, paths) for count, value in survivor_counts.items()}
    )
    measured = MappingProxyType(
        {
            f"{account_ids[row]}:{account_ids[column]}": Decimal(
                str(correlation[row, column])
            )
            for row in range(len(account_ids))
            for column in range(row + 1, len(account_ids))
        }
    )
    return JointFirstPassageReport(
        paths=paths,
        seed=seed,
        account_ids=account_ids,
        surviving_accounts_distribution=distribution,
        probability_none_survive=distribution[0],
        measured_correlation=measured,
    )


def estimate_drawdown_mode_sensitivity(
    returns: Sequence[Decimal],
    mandate: FirmMandate,
    *,
    paths: int,
    seed: int,
) -> Mapping[DrawdownMode, FirstPassageReport]:
    """Evaluate identical seeded return paths under all drawdown modes.

    Args:
        returns: Measured fractional daily returns.
        mandate: Verified base mandate.
        paths: Positive number of seeded paths.
        seed: Deterministic random seed.

    Returns:
        One first-passage report for each supported drawdown mode.

    Raises:
        OptimizationError: If the return sample or mandate is invalid.
    """
    logger.info("Estimating Optimization drawdown-mode sensitivity")
    reports: dict[DrawdownMode, FirstPassageReport] = {}
    for mode in (
        get_drawdown_mode("STATIC"),
        get_drawdown_mode("TRAILING_EOD"),
        get_drawdown_mode("TRAILING_INTRADAY"),
    ):
        rule_data = mandate.max_drawdown.model_dump()
        rule_data["mode"] = mode
        rule_data["trails_on_unrealised"] = mode is get_drawdown_mode(
            "TRAILING_INTRADAY"
        )
        if mode is get_drawdown_mode("TRAILING_EOD"):
            rule_data["eod_snapshot_time"] = rule_data["eod_snapshot_time"] or "23:59"
            rule_data["eod_snapshot_tz"] = rule_data["eod_snapshot_tz"] or "UTC"
        else:
            rule_data["eod_snapshot_time"] = None
            rule_data["eod_snapshot_tz"] = None
        adjusted = mandate.model_copy(
            update={
                "max_drawdown": type(mandate.max_drawdown).model_validate(rule_data)
            }
        )
        reports[mode] = estimate_first_passage(
            returns, adjusted, paths=paths, seed=seed
        )
    return MappingProxyType(reports)


__all__ = [
    "FirstPassageReport",
    "JointFirstPassageReport",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
]
