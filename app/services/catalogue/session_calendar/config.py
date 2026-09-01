"""Configuration dataclass for Sessions and Calendars."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SessionCalendarConfig:
    """Configuration options for Sessions and Calendars."""

    database_path: str | Path | None = None
    auto_migrate: bool = True
