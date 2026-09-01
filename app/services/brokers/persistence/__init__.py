"""Internal export boundary for Brokers persistence.

Private support package. Nothing here is part of the Brokers public API;
callers reach it through ``app.services.brokers``.
"""

from app.services.brokers.persistence.create import create_health_record

__all__ = [
    "create_health_record",
]
