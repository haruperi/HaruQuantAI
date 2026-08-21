"""Feature specification for Historical Bars."""

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-RETRIEVE_BARS",
    domain="data",
    provides=frozenset({HISTORICAL_BARS}),
    requires=frozenset({BROKER_MARKET_DATA}),
    description="Retrieve and normalize historical OHLCV bars from broker",
    config_keys=frozenset({"default_timeframe"}),
)
