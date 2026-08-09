"""Internal feature exports for runtime-settings operations."""

from typing import cast

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.utils.settings.loader import load_broker_provider_settings, load_settings
from app.utils.settings.models import AppSettings as _AppSettings
from app.utils.settings.references import (
    build_profile_ref,
    build_version_ref,
    load_profile_document,
    parse_profile_ref,
    parse_version_ref,
)


def get_app_settings_model_config() -> SettingsConfigDict:
    """Return a copy of the canonical immutable application-settings config.

    Returns:
        Canonical Pydantic settings configuration.
    """
    return cast("SettingsConfigDict", dict(_AppSettings.model_config))


def get_app_settings_sources(
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
) -> tuple[PydanticBaseSettingsSource, ...]:
    """Return canonical central settings sources for one settings model.

    Args:
        settings_cls: Concrete application settings model.
        init_settings: Explicit constructor-value source.
        env_settings: Process-environment source.
        dotenv_settings: Optional dotenv source.
        file_secret_settings: File-backed secret source.

    Returns:
        Settings sources in descending precedence order.
    """
    return _AppSettings.settings_customise_sources(
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    )


__all__ = [
    "build_profile_ref",
    "build_version_ref",
    "get_app_settings_model_config",
    "get_app_settings_sources",
    "load_broker_provider_settings",
    "load_profile_document",
    "load_settings",
    "parse_profile_ref",
    "parse_version_ref",
]
