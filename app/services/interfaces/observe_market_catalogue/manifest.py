"""Feature specification for the market catalogue browsing gateway."""

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_CATALOGUE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OBSERVE_MARKET_CATALOGUE",
    domain="interfaces",
    provides=frozenset({OBSERVE_MARKET_CATALOGUE_CAPABILITY}),
    requires=frozenset({CATALOG_INSTRUMENTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose bounded market catalogue browse pages.",
    state=None,
    config_keys=frozenset({"default_page_size", "max_page_size"}),
)
