"""Migration bridge for SimulatorClient to app.core.trading.simulation.client."""

import sys

from app.core.trading.simulation import client as _implementation
from app.core.trading.simulation.client import *  # noqa: F403

sys.modules[__name__] = _implementation
