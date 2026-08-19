"""HTTP route declarations for ordered event delivery.

Ordered event delivery is consumed by owning route features and does not expose
an independent HTTP resource family.
"""

from fastapi import APIRouter

router = APIRouter()

__all__ = ("router",)
