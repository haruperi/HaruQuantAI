"""Private DATA-domain configuration loaded through the shared settings boundary.

The root-private location is approved domain-wide infrastructure under
``CAP-DATA-028``. Behaviour, field names, defaults, and validators remain unchanged.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated, Final, Literal, override

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, PydanticBaseSettingsSource

from app.utils import (
    get_app_settings_model_config,
    get_app_settings_sources,
    get_logger,
    load_broker_provider_settings,
)

logger = get_logger(__name__)

DEFAULT_APPROVED_STORAGE_ROOTS: Final = (
    Path("data/raw"),
    Path("data/processed"),
    Path("data/cache"),
    Path("artifacts/data"),
)

DEFAULT_LOCAL_SOURCES: Final = ("csv", "parquet")
DEFAULT_RAW_ROOT: Final = Path("data/raw")
LOCAL_SYMBOL_MANIFEST_NAME: Final = "symbols.json"


class DataSettings(BaseSettings):
    """Immutable DATA-owned settings resolved from explicit or process values."""

    model_config = get_app_settings_model_config()

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

    @override
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Load explicit and externally provisioned process values.

        Args:
            settings_cls: Concrete Data settings model.
            init_settings: Explicit constructor values source.
            env_settings: Process-environment source.
            dotenv_settings: Optional dotenv source.
            file_secret_settings: File-backed secret source.

        Returns:
            Canonical settings sources in descending precedence order.
        """
        return get_app_settings_sources(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, value: object) -> object:
        """Reject blank or padded database URLs at the settings boundary.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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
        """Reject padded numeric strings before Pydantic conversion.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Validating a numeric DATA setting")
        if isinstance(value, str) and value != value.strip():
            raise ValueError("numeric DATA settings must be trimmed")
        return value

    @field_validator("approved_storage_roots", mode="before")
    @classmethod
    def _parse_approved_storage_roots(cls, value: object) -> object:
        """Parse a comma-separated approved-root setting without JSON guessing.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
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

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
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
        """Reject absolute or traversing raw roots at the settings boundary.

        Args:
            value: The ``value`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            ValueError: If the operation cannot be completed safely.
        """
        logger.debug("Validating the DATA raw artifact root")
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("data_raw_root must be a relative path without traversal")
        return value


_DATA_SETTINGS_OVERRIDE: ContextVar[DataSettings | None] = ContextVar(
    "data_settings_override",
    default=None,
)
_DATA_PROVIDER_SETTINGS_OVERRIDE: ContextVar[object | None] = ContextVar(
    "data_provider_settings_override",
    default=None,
)
_DATA_PROVIDER_CONNECTION_RESOLVER: ContextVar[Callable[[str, str], object] | None] = (
    ContextVar("data_provider_connection_resolver", default=None)
)


def get_data_settings() -> DataSettings:
    """Return the active typed DATA settings for the current call context.

    Returns:
        The result produced by the operation.
    """
    logger.debug("Resolving typed DATA settings")
    override = _DATA_SETTINGS_OVERRIDE.get()
    return override if override is not None else DataSettings()


def get_data_provider_settings() -> object:
    """Return the active opaque provider settings for the current context.

    Returns:
        The injected immutable provider settings, or the safe Utils defaults.
    """
    logger.debug("Resolving context-local DATA provider settings")
    override = _DATA_PROVIDER_SETTINGS_OVERRIDE.get()
    return override if override is not None else load_broker_provider_settings()


def get_data_provider_connection_resolver() -> Callable[[str, str], object] | None:
    """Return the active connection-config resolver, if one was injected.

    Returns:
        Context-local provider and request resolver, otherwise None.
    """
    return _DATA_PROVIDER_CONNECTION_RESOLVER.get()


@contextmanager
def data_settings_context(settings: DataSettings) -> Iterator[None]:
    """Temporarily install explicit DATA settings for an isolated call context.

    Args:
        settings: The ``settings`` argument.

    Yields:
        The next value produced by the operation.
    """
    logger.debug("Installing explicit context-local DATA settings")
    token = _DATA_SETTINGS_OVERRIDE.set(settings)
    try:
        yield
    finally:
        _DATA_SETTINGS_OVERRIDE.reset(token)
        logger.debug("Restored the preceding DATA settings context")


@contextmanager
def data_provider_settings_context(settings: object) -> Iterator[None]:
    """Temporarily install validated opaque provider settings.

    Args:
        settings: Immutable provider settings built by the Utils public boundary.

    Yields:
        Control while the provider settings are active for this call context.
    """
    logger.debug("Installing context-local DATA provider settings")
    token = _DATA_PROVIDER_SETTINGS_OVERRIDE.set(settings)
    try:
        yield
    finally:
        _DATA_PROVIDER_SETTINGS_OVERRIDE.reset(token)
        logger.debug("Restored the preceding DATA provider settings context")


@contextmanager
def data_provider_connection_resolver_context(
    resolver: Callable[[str, str], object],
) -> Iterator[None]:
    """Install an API-owned governed connection-config resolver.

    Args:
        resolver: Callable accepting provider ID and request ID.

    Yields:
        Control while the resolver is active in the current context.
    """
    token = _DATA_PROVIDER_CONNECTION_RESOLVER.set(resolver)
    try:
        yield
    finally:
        _DATA_PROVIDER_CONNECTION_RESOLVER.reset(token)


__all__ = [
    "LOCAL_SYMBOL_MANIFEST_NAME",
    "DataSettings",
    "data_provider_connection_resolver_context",
    "data_provider_settings_context",
    "data_settings_context",
    "get_data_provider_connection_resolver",
    "get_data_provider_settings",
    "get_data_settings",
]
