"""Identity module for the registered Discretionary Manual Order strategy.

This module intentionally contains no signal-generation code and declares no
``supported_hooks``. The Discretionary Manual Order strategy exists so a
human-initiated order can carry a genuine Strategy-owned ``TradeIntent``
through Risk's fixed-precedence review; the trading decision itself is made
by the authenticated operator at the moment they confirm the order, never by
this module. Its only role is to exist as a stable, hashed, versioned
registration target that :mod:`app.services.strategy.discretionary.registration`
points ``StrategyManifest.module_path`` at.
"""

from __future__ import annotations

__all__: list[str] = []
