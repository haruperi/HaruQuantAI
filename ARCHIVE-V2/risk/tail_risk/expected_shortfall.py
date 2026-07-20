# ruff: noqa: ANN401, PLR2004, PLR0915
"""Portfolio Expected Shortfall (ES) / CVaR computation service."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal
from statistics import NormalDist
from typing import TYPE_CHECKING, Any, overload

from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models.contracts import (
    ExpectedShortfallSnapshot,
    PortfolioState,
    ProposedTrade,
    VaRSnapshot,
)
from app.services.risk.tail_risk.contracts import (
    ExpectedShortfallMethod,
    ExpectedShortfallRequest,
)
from app.services.risk.tail_risk.var import (
    _prepare_aligned_returns,
    calculate_covariance_matrix,
    calculate_portfolio_volatility,
    shrink_covariance_matrix,
    validate_covariance_matrix,
)
from app.services.risk.validations import ValidationResult, _fail, _ok
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.policy.contracts import EffectiveRiskPolicy


def select_tail_losses(
    losses: Sequence[Decimal], confidence: Decimal
) -> tuple[Decimal, ...]:
    """Deterministically selects tail observations.

    Args:
        losses: Historical sequence of portfolio return/loss values.
        confidence: Tail confidence level (e.g. 0.95).

    Returns:
        tuple[Decimal, ...]: Filtered worst-performing returns in the tail.
    """
    logger.info("select_tail_losses called.")
    n = len(losses)
    if n == 0:
        return ()

    # Sort in ascending order (worst negative returns first)
    sorted_losses = sorted(losses)
    idx = max(0, min(n - 1, int((Decimal("1.0") - confidence) * Decimal(n))))
    return tuple(sorted_losses[: idx + 1])


def validate_tail_risk_assumptions(
    var: VaRSnapshot, es: ExpectedShortfallSnapshot, policy: EffectiveRiskPolicy
) -> ValidationResult:
    """Rejects invalid or insufficient tail evidence.

    Args:
        var: Value-at-Risk snapshot.
        es: Expected Shortfall snapshot.
        policy: Active risk policy profile.

    Returns:
        ValidationResult: The validation outcome.
    """
    logger.info("validate_tail_risk_assumptions called.")
    if es.average_tail_loss < var.result:
        msg = (
            f"Expected Shortfall average tail loss ({es.average_tail_loss}) "
            f"cannot be less than VaR result ({var.result})"
        )
        logger.error(msg)
        return _fail(
            msg,
            code="INVALID_TAIL_RISK_RELATION",
            details={
                "var_result": float(var.result),
                "es_average_tail_loss": float(es.average_tail_loss),
            },
        )

    if var.confidence <= 0 or var.confidence >= 1:
        msg = f"Invalid VaR confidence level: {var.confidence}"
        logger.error(msg)
        return _fail(
            msg,
            code="INVALID_CONFIDENCE",
            details={"confidence": float(var.confidence)},
        )

    if es.confidence <= 0 or es.confidence >= 1:
        msg = f"Invalid ES confidence level: {es.confidence}"
        logger.error(msg)
        return _fail(
            msg,
            code="INVALID_CONFIDENCE",
            details={"confidence": float(es.confidence)},
        )

    min_samples = getattr(policy, "minimum_samples", 20)
    if es.sample_count < min_samples:
        msg = (
            f"Insufficient sample size for tail risk calculation: "
            f"{es.sample_count} < {min_samples}"
        )
        logger.error(msg)
        return _fail(
            msg,
            code="INSUFFICIENT_SAMPLES",
            details={"sample_count": es.sample_count, "min_samples": min_samples},
        )

    return _ok("Tail risk assumptions successfully validated.")


@overload
def calculate_expected_shortfall(
    request: ExpectedShortfallRequest,
) -> ExpectedShortfallSnapshot: ...


@overload
def calculate_expected_shortfall(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: Any = None,
    proposed_trade: ProposedTrade | None = None,
    lookback: int = 50,
    confidence: Decimal = Decimal("0.95"),
    method: str = "parametric",
) -> Decimal: ...


def calculate_expected_shortfall(*args: Any, **kwargs: Any) -> Any:
    """Calculate portfolio Expected Shortfall, supporting both V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V2, the first argument is an
            ExpectedShortfallRequest. For V1, the arguments are:
            portfolio_state (PortfolioState), market_context (dict[str, Any]),
            config (Any, optional), proposed_trade (ProposedTrade, optional),
            lookback (int, optional), confidence (Decimal, optional),
            method (str, optional).
        **kwargs: Keyword arguments. For V2, "request" can be passed. For V1,
            arguments like "portfolio_state", "market_context", "config",
            "proposed_trade", "lookback", "confidence", "method" can be passed.

    Returns:
        ExpectedShortfallSnapshot | Decimal: The Expected Shortfall snapshot for V2,
        or the average tail loss value for V1.

    Raises:
        ValidationError: If returned calculations are non-finite or aligned returns
            check fails.
    """
    logger.info("calculate_expected_shortfall entry.")

    # Detect V2 vs V1
    is_v2 = False
    if (len(args) > 0 and isinstance(args[0], ExpectedShortfallRequest)) or (
        "request" in kwargs and isinstance(kwargs["request"], ExpectedShortfallRequest)
    ):
        is_v2 = True

    if is_v2:
        # V2 logic
        request: ExpectedShortfallRequest = (
            args[0] if len(args) > 0 else kwargs["request"]
        )
        aligned, gross_exposure, weights = _prepare_aligned_returns(
            request.portfolio_state,
            request.proposed_trade,
            request.market_context,
            request.min_samples,
            request.exclude_last,
        )

        if not aligned:
            return ExpectedShortfallSnapshot(
                confidence=request.confidence,
                threshold_loss=Decimal("0.0"),
                average_tail_loss=Decimal("0.0"),
                sample_count=0,
                method=str(request.method),
            )

        sliced = {s: rets[-request.lookback :] for s, rets in aligned.items()}
        first_sym = next(iter(sliced))
        n = len(sliced[first_sym])

        if request.method == ExpectedShortfallMethod.PARAMETRIC:
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

            z_f = float(z)
            phi_z = Decimal(str(math.exp(-0.5 * z_f * z_f) / math.sqrt(2.0 * math.pi)))
            tail_prob = Decimal("1.0") - request.confidence
            if tail_prob <= 0:
                es_val = var_val
            else:
                es_val = vol * (phi_z / tail_prob) * gross_exposure

            if not math.isfinite(float(es_val)):
                msg = (
                    "Non-finite calculation detected in parametric Expected Shortfall."
                )
                logger.error(msg)
                raise ValidationError(msg)

            return ExpectedShortfallSnapshot(
                confidence=request.confidence,
                threshold_loss=var_val,
                average_tail_loss=es_val,
                sample_count=n,
                method=str(ExpectedShortfallMethod.PARAMETRIC),
            )

        # Historical
        port_returns = []
        symbols = sorted(weights.keys())
        for i in range(n):
            r_p = sum((weights[s] * sliced[s][i] for s in symbols), Decimal("0.0"))
            port_returns.append(r_p)

        port_returns.sort()
        idx = max(
            0, min(n - 1, int((Decimal("1.0") - request.confidence) * Decimal(n)))
        )
        var_pct = -port_returns[idx]
        var_val = var_pct * gross_exposure

        tail_returns = select_tail_losses(port_returns, request.confidence)
        if not tail_returns:
            es_pct = var_pct
        else:
            es_pct = -sum(tail_returns, Decimal("0.0")) / Decimal(len(tail_returns))

        es_val = es_pct * gross_exposure

        if not math.isfinite(float(es_val)):
            msg = "Non-finite calculation detected in historical Expected Shortfall."
            logger.error(msg)
            raise ValidationError(msg)

        return ExpectedShortfallSnapshot(
            confidence=request.confidence,
            threshold_loss=var_val,
            average_tail_loss=es_val,
            sample_count=n,
            method=str(ExpectedShortfallMethod.HISTORICAL),
        )

    # V1 logic
    portfolio_state: Any = args[0] if len(args) > 0 else kwargs.get("portfolio_state")
    market_context: Any = args[1] if len(args) > 1 else kwargs.get("market_context")
    config: Any = args[2] if len(args) > 2 else kwargs.get("config")
    proposed_trade: Any = args[3] if len(args) > 3 else kwargs.get("proposed_trade")
    lookback: Any = args[4] if len(args) > 4 else kwargs.get("lookback", 50)
    confidence: Any = (
        args[5] if len(args) > 5 else kwargs.get("confidence", Decimal("0.95"))
    )
    method: Any = args[6] if len(args) > 6 else kwargs.get("method", "parametric")

    # Extract optional kwargs if any
    lookback = kwargs.get("lookback", lookback)
    confidence = kwargs.get("confidence", confidence)
    method = kwargs.get("method", method)
    proposed_trade = kwargs.get("proposed_trade", proposed_trade)

    from app.services.risk.tail_risk import calculate_var_es_snapshots

    _, es_snap = calculate_var_es_snapshots(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_context=market_context,
        config=config,
        lookback=lookback,
        es_confidence=confidence,
        es_method=method,
    )
    return es_snap.average_tail_loss


class ExpectedShortfallEngine:
    """Engine for estimating portfolio Expected Shortfall (CVaR)."""

    def __init__(self, config: object) -> None:
        """Initialize ExpectedShortfallEngine.

        Args:
            config: Active configuration profile.
        """
        self.config = config

    def calculate_es(
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
        """Legacy helper to calculate Expected Shortfall.

        Args:
            portfolio_state: Current portfolio state.
            market_context: Market context containing returns/prices history.
            proposed_trade: Optional candidate proposed trade.
            lookback: Returns lookback length.
            confidence: Confidence level.
            method: ES calculation method ('parametric', 'historical').
            cov_method: Covariance matrix estimation method.
            ewma_decay: EWMA decay factor.
            shrinkage_intensity: Covariance matrix shrinkage intensity.
            min_samples: Minimum required return samples.
            exclude_last: Exclude the last bar.

        Returns:
            ExpectedShortfallResult: Encapsulated Expected Shortfall outputs.
        """
        logger.info("ExpectedShortfallEngine.calculate_es legacy call.")
        req = ExpectedShortfallRequest(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
            lookback=lookback,
            confidence=confidence,
            method=ExpectedShortfallMethod(method),
            cov_method=cov_method,
            ewma_decay=ewma_decay,
            shrinkage_intensity=shrinkage_intensity,
            min_samples=min_samples,
            exclude_last=exclude_last,
        )

        snap = calculate_expected_shortfall(req)

        from app.services.risk.tail_risk.contracts import ExpectedShortfallResult

        return ExpectedShortfallResult(
            confidence=snap.confidence,
            threshold_loss=snap.threshold_loss,
            average_tail_loss=snap.average_tail_loss,
            sample_count=snap.sample_count,
            method=snap.method,
        )
