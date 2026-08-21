"""System clock capability contract."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@runtime_checkable
class SystemClock(Protocol):
    """Protocol for system and simulated clock providers."""

    def now(self) -> datetime:
        """Return the current system or simulation datetime in UTC.

        Returns:
            Current datetime in UTC.
        """
        ...

    def timestamp(self) -> float:
        """Return the current epoch timestamp in seconds.

        Returns:
            Epoch timestamp in seconds.
        """
        ...


SYSTEM_CLOCK = CapabilityKey[SystemClock](
    name="system.clock",
    major=1,
)
