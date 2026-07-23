"""Private DATA-domain configuration loaded through the shared settings boundary.

The root-private location is approved domain-wide infrastructure under
``CAP-DATA-028``. Behaviour, field names, defaults, and validators remain unchanged.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated, Final, Literal

from pydantic import Field, field_validator
from pydantic_settings import NoDecode

from app.utils import AppSettings, logger

DEFAULT_APPROVED_STORAGE_ROOTS: Final = (
    Path("data/raw"),
    Path("data/processed"),
    Path("data/cache"),
    Path("artifacts/data"),
)

DEFAULT_LOCAL_SOURCES: Final = ("csv", "parquet")
DEFAULT_RAW_ROOT: Final = Path("data/raw")
LOCAL_SYMBOL_MANIFEST_NAME: Final = "symbols.json"


class DataSettings(AppSettings):
    """Immutable DATA-owned settings resolved by the shared settings loader."""

    database_url: str | None = None
    data_dir: Path | None = None
    sqlite_busy_timeout_seconds: float | None = Field(default=None, gt=0)
    write_lock_lease_seconds: float | None = Field(default=None, gt=0)
    approved_storage_roots: Annotated[tuple[Path, ...], NoDecode] = (
        DEFAULT_APPROVED_STORAGE_ROOTS
    )
    symbol_list_max_limit: int = Field(default=10_000, gt=0)
    availability_scan_max_records: int = Field(default=1_000_000, gt=0)
    data_local_sources: Annotated[tuple[str, ...], NoDecode] = DEFAULT_LOCAL_SOURCES
    data_provider_sources: Annotated[tuple[str, ...], NoDecode] = ()
    data_raw_root: Path = DEFAULT_RAW_ROOT
    quality_profile: Literal["strict", "standard", "lenient"] = "standard"

    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, value: object) -> object:
        """Reject blank or padded database URLs at the settings boundary."""
        logger.debug("Validating the DATA database URL setting")
        if isinstance(value, str) and (not value or value != value.strip()):
            raise ValueError("database_url must be non-blank and trimmed")
        return value

    @field_validator(
        "sqlite_busy_timeout_seconds",
        "write_lock_lease_seconds",
        "symbol_list_max_limit",
        "availability_scan_max_records",
        mode="before",
    )
    @classmethod
    def _reject_padded_numeric_settings(cls, value: object) -> object:
        """Reject padded numeric strings before Pydantic conversion."""
        logger.debug("Validating a numeric DATA setting")
        if isinstance(value, str) and value != value.strip():
            raise ValueError("numeric DATA settings must be trimmed")
        return value

    @field_validator("approved_storage_roots", mode="before")
    @classmethod
    def _parse_approved_storage_roots(cls, value: object) -> object:
        """Parse a comma-separated approved-root setting without JSON guessing."""
        logger.debug("Parsing approved DATA storage roots")
        if not isinstance(value, str):
            return value
        roots = tuple(Path(item.strip()) for item in value.split(",") if item.strip())
        if not roots:
            raise ValueError("approved_storage_roots must not be empty")
        return roots

    @field_validator("data_local_sources", "data_provider_sources", mode="before")
    @classmethod
    def _parse_source_identifiers(cls, value: object) -> object:
        """Parse a comma-separated source-identifier setting without JSON guessing.

        An empty configured value is a valid explicit choice meaning "compose no
        source of this kind", so it is preserved rather than replaced by a default.
        """
        logger.debug("Parsing configured DATA source identifiers")
        if not isinstance(value, str):
            return value
        identifiers = tuple(item.strip() for item in value.split(",") if item.strip())
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("source identifiers must be unique")
        return identifiers

    @field_validator("data_raw_root")
    @classmethod
    def _validate_raw_root(cls, value: Path) -> Path:
        """Reject absolute or traversing raw roots at the settings boundary."""
        logger.debug("Validating the DATA raw artifact root")
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("data_raw_root must be a relative path without traversal")
        return value


_DATA_SETTINGS_OVERRIDE: ContextVar[DataSettings | None] = ContextVar(
    "data_settings_override",
    default=None,
)


def get_data_settings() -> DataSettings:
    """Return the active typed DATA settings for the current call context."""
    logger.debug("Resolving typed DATA settings")
    override = _DATA_SETTINGS_OVERRIDE.get()
    return override if override is not None else DataSettings()


@contextmanager
def data_settings_context(settings: DataSettings) -> Iterator[None]:
    """Temporarily install explicit DATA settings for an isolated call context."""
    logger.debug("Installing explicit context-local DATA settings")
    token = _DATA_SETTINGS_OVERRIDE.set(settings)
    try:
        yield
    finally:
        _DATA_SETTINGS_OVERRIDE.reset(token)
        logger.debug("Restored the preceding DATA settings context")


__all__ = [
    "LOCAL_SYMBOL_MANIFEST_NAME",
    "DataSettings",
    "data_settings_context",
    "get_data_settings",
]
