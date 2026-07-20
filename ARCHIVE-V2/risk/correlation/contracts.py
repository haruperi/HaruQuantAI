"""Correlation and cluster risk engine contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from app.services.risk.models.contracts import RiskContract
from pydantic import Field


class ReturnMethod(StrEnum):
    """Supported returns calculation types."""

    CLOSE_TO_CLOSE = "close_to_close"
    LOG = "log"
    OPEN_TO_CLOSE = "open_to_close"
    SIGMA_NORMALIZED = "sigma_normalized"


class CorrelationMethod(StrEnum):
    """Supported correlation calculation methods."""

    PEARSON = "pearson"


class CorrelationAlignmentPolicy(StrEnum):
    """Alignment methods for returns series."""

    INTERSECT = "intersect"


class ClosedBar(RiskContract):
    """Bar structure representing a historical period."""

    time: datetime = Field(..., description="Opening time of the bar.")
    open: Decimal = Field(..., description="Opening price of the bar.")
    close: Decimal = Field(..., description="Closing price of the bar.")


class ReturnSeries(RiskContract):
    """Series representing return calculations for a single symbol."""

    symbol: str = Field(..., description="Target symbol identifier.")
    returns: Mapping[datetime, Decimal] = Field(
        default_factory=dict, description="DateTime mapped returns values."
    )


class AlignedReturns(RiskContract):
    """Matrix of aligned returns across multiple symbols."""

    timestamps: Sequence[datetime] = Field(
        default_factory=list, description="Ordered common timestamps."
    )
    returns: Mapping[str, Sequence[Decimal]] = Field(
        default_factory=dict, description="Aligned returns arrays per symbol."
    )


class CorrelationCluster(RiskContract):
    """Group of highly correlated symbols representing shared portfolio risk."""

    cluster_id: str = Field(..., description="Unique cluster identifier.")
    symbols: Sequence[str] = Field(
        default_factory=list, description="Collection of symbols in cluster."
    )


class ClusterExposureAssessment(RiskContract):
    """Aggregated gross exposure assessment by cluster."""

    exposures: Mapping[str, Decimal] = Field(
        default_factory=dict, description="Exposures mapped by cluster name."
    )


class CovarianceMatrix(RiskContract):
    """Covariance values table."""

    matrix: Mapping[str, Mapping[str, Decimal]] = Field(
        default_factory=dict, description="Covariance matrix values."
    )


class ComponentRiskContribution(RiskContract):
    """Contribution details per portfolio component."""

    contributions: Mapping[str, Decimal] = Field(
        default_factory=dict, description="Risk contribution values by symbol."
    )


class CorrelationFallbackContext(RiskContract):
    """Context details when correlation matrix fallback triggers."""

    symbols: Sequence[str] = Field(..., description="Active symbols.")
    mode: str = Field(..., description="Operating risk mode.")
    sample_count: int = Field(..., description="Number of aligned samples.", ge=0)
    minimum_samples: int = Field(..., description="Minimum samples required.", gt=0)
