"""Feature specification and capability metadata for Mock Broker Feed."""

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BROKER-FEED_MOCK",
    domain="broker",
    provides=frozenset({BROKER_MARKET_DATA}),
    description="Mock broker market data provider for testing and simulation",
)
