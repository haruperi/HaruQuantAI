"""Service-level broker resolver.

Centralizes active broker module selection so API routes do not own broker
adapter policy.
"""

from types import ModuleType

from app.services.utils.logger import logger


def get_active_broker_name() -> str:
    """Description.
        Return the configured broker name with compatibility fallbacks.
    
    Args:
        None.
    
    Returns:
        str.
    """
    settings_obj: object | None = None
    try:
        from app.services.utils import settings as settings_module

        settings_obj = getattr(settings_module, "settings", None)
    except ImportError:
        settings_obj = None

    if settings_obj is None:
        try:
            from app.core.config import (  # type: ignore[import-not-found, unused-ignore]
                settings as core_settings,
            )

            settings_obj = core_settings
        except ImportError:
            settings_obj = None

    active = str(getattr(settings_obj, "active_broker", "mt5")).lower()
    logger.debug("Resolved active broker name: '{}'.", active)
    return active


def get_broker_module() -> ModuleType:
    """Description.
        Resolve and return the active broker module from runtime settings.
    
    Args:
        None.
    
    Returns:
        ModuleType.
    """
    active = get_active_broker_name()
    if active == "ctrader":
        from app.services.brokers import ctrader

        logger.debug("Resolved broker module: ctrader.")
        return ctrader

    if active == "simulator":
        from importlib import import_module

        logger.debug("Resolved broker module: simulator.")
        return import_module("app.services.simulator")

    from app.services.brokers import mt5

    logger.debug("Resolved broker module: mt5 (default).")
    return mt5


__all__ = [
    "get_active_broker_name",
    "get_broker_module",
]
