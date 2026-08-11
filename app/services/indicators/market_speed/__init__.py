"""Approved public market-speed-indicator API.

Five of the six spec ``IND-MS-*`` indicators calculable from the current
``MarketDataset``/``OHLCVRecord`` bar contract are registered here:
``price_velocity`` (``IND-MS-01``), ``momentum_acceleration``
(``IND-MS-02``), ``volume_acceleration`` (``IND-MS-03``),
``market_event_arrival_rate`` (``IND-MS-04``, a documented bar-arrival
proxy — see its module docstring), ``volatility_expansion_rate``
(``IND-MS-06``), and ``composite_market_speed_gauge`` (``IND-MS-07``).

``order_flow_velocity`` (``IND-MS-05``) is intentionally omitted: it
composes windowed OFI (``IND-OF-01``), and OFI itself was already skipped
in the ``order_flow/`` phase because it requires L2 order-book data the
current contract does not carry (see ``order_flow/__init__.py``). There is
no windowed OFI series to convert into a rate.
"""

from app.services.indicators.market_speed.composite_market_speed_gauge import (
    composite_market_speed_gauge,
)
from app.services.indicators.market_speed.market_event_arrival_rate import (
    market_event_arrival_rate,
)
from app.services.indicators.market_speed.momentum_acceleration import (
    momentum_acceleration,
)
from app.services.indicators.market_speed.price_velocity import price_velocity
from app.services.indicators.market_speed.volatility_expansion_rate import (
    volatility_expansion_rate,
)
from app.services.indicators.market_speed.volume_acceleration import (
    volume_acceleration,
)

__all__ = [
    "composite_market_speed_gauge",
    "market_event_arrival_rate",
    "momentum_acceleration",
    "price_velocity",
    "volatility_expansion_rate",
    "volume_acceleration",
]
