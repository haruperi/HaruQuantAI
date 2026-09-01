"""Typed API bootstrap settings owned by the Settings feature."""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Literal, override

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from app.composition.config import (
    get_app_settings_model_config,
    get_app_settings_sources,
)
from app.services.api.widgets.settings.limits import (
    API_DEFAULT_PAGE_SIZE,
    API_ENDPOINT_TIMEOUT_SECONDS,
    API_MAX_PAGE_SIZE,
    HTTP_IDEMPOTENCY_RETENTION_SECONDS,
    PREFLIGHT_WARNING_TTL_SECONDS,
    get_default_rate_limits,
)


class ApiSettings(BaseSettings):
    """Immutable configuration for the canonical API application."""

    model_config = get_app_settings_model_config()

    environment: Literal["dev", "test", "staging", "production"] = "dev"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_version: Literal["v1"] = "v1"
    runtime_profile: Literal["research", "simulation", "demo", "live"] = "research"
    execution_route: Literal["none", "sim", "demo", "live"] = "none"
    simulation_artifact_root: Path = Path("artifacts/simulation")
    allow_live_mutations: bool = False
    # Shared persistence configuration. Data owns the connection, locking, and
    # migration-execution infrastructure; UI/API only names the target so its
    # own schemas and records resolve to the same store. A raw connection is
    # never constructed here and never crosses the API boundary.
    database_url: str | None = None
    data_dir: Path | None = None
    ui_origins: tuple[str, ...] = ("http://localhost:3000",)
    session_ttl_seconds: int = Field(default=3600, ge=60, le=2_592_000)
    api_default_page_size: int = Field(default=API_DEFAULT_PAGE_SIZE, ge=1)
    api_max_page_size: int = Field(default=API_MAX_PAGE_SIZE, ge=1)
    api_endpoint_timeout_seconds: float = Field(
        default=API_ENDPOINT_TIMEOUT_SECONDS,
        gt=0,
        le=300,
    )
    preflight_warning_ttl_seconds: float = Field(
        default=PREFLIGHT_WARNING_TTL_SECONDS,
        gt=0,
        le=300,
    )
    idempotency_retention_seconds: int = Field(
        default=HTTP_IDEMPOTENCY_RETENTION_SECONDS,
        ge=HTTP_IDEMPOTENCY_RETENTION_SECONDS,
    )
    stream_heartbeat_seconds: float = Field(default=15.0, gt=0, le=300)
    stream_heartbeat_timeout_seconds: float = Field(default=45.0, gt=0, le=600)
    stream_max_connections_per_actor: int = Field(default=4, ge=1, le=100)
    stream_max_connections_process: int = Field(default=100, ge=1, le=10_000)
    stream_resume_window: int = Field(default=256, ge=1, le=100_000)
    auth_transport: Literal["cookie_and_bearer"] = "cookie_and_bearer"
    # Development mode auto login default
    dev_auto_login: bool = True
    active_credential_key_id: str | None = None
    credential_encryption_key: SecretStr | None = None
    credential_key_refs: tuple[str, ...] = ()
    rate_limits_by_class: Mapping[str, tuple[int, float]] = Field(
        default_factory=lambda: dict(get_default_rate_limits())
    )

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

    @field_validator("api_host")
    @classmethod
    def _validate_host(cls, value: str) -> str:
        """Reject empty or whitespace-padded bind hosts.

        Returns:
            Validated bind host.

        Raises:
            ValueError: If the host is empty or padded.
        """
        if not value or value != value.strip():
            raise ValueError("api_host must be non-empty and trimmed")
        return value

    @field_validator("ui_origins")
    @classmethod
    def _validate_origins(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate an exact-origin CORS allowlist.

        Returns:
            Unique exact HTTP origins.

        Raises:
            ValueError: If an origin is unsafe or duplicated.
        """
        if not value:
            raise ValueError("ui_origins must not be empty")
        normalized = tuple(origin.strip().rstrip("/") for origin in value)
        if any(
            not origin.startswith(("http://", "https://")) or "*" in origin
            for origin in normalized
        ):
            raise ValueError("ui_origins must contain exact HTTP origins")
        if len(set(normalized)) != len(normalized):
            raise ValueError("ui_origins must be unique")
        return normalized

    def _validate_execution_and_dev(self) -> None:
        """Validate execution routes and development options.

        Raises:
            ValueError: If development or execution options are invalid.
        """
        if self.dev_auto_login and self.environment != "dev":
            raise ValueError("dev_auto_login is allowed only in dev environment")
        expected_route = {
            "research": "none",
            "simulation": "sim",
            "demo": "demo",
            "live": "live",
        }[self.runtime_profile]
        if self.execution_route != expected_route:
            raise ValueError("runtime profile and execution route are incompatible")

    @model_validator(mode="after")
    def _validate_cross_field_limits(self) -> ApiSettings:
        """Validate related pagination, stream, and key-selection limits.

        Returns:
            Validated settings.

        Raises:
            ValueError: If cross-field invariants fail.
        """
        self._validate_execution_and_dev()
        if self.api_default_page_size > self.api_max_page_size:
            raise ValueError("default page size cannot exceed maximum")
        if self.stream_heartbeat_timeout_seconds <= self.stream_heartbeat_seconds:
            raise ValueError("stream timeout must exceed heartbeat interval")
        if self.stream_max_connections_per_actor > self.stream_max_connections_process:
            raise ValueError("actor connection limit cannot exceed process limit")
        if (
            self.active_credential_key_id is not None
            and self.active_credential_key_id not in self.credential_key_refs
        ):
            raise ValueError("active credential key must be declared")
        if (self.active_credential_key_id is None) != (
            self.credential_encryption_key is None
        ):
            raise ValueError(
                "active credential key ID and encryption key must be supplied together"
            )
        expected_rate_classes = {
            "authentication",
            "compute",
            "governed_write",
            "read",
            "stream",
        }
        if set(self.rate_limits_by_class) != expected_rate_classes:
            raise ValueError("rate_limits_by_class must define the canonical classes")
        if any(
            isinstance(capacity, bool) or capacity <= 0 or window_seconds <= 0
            for capacity, window_seconds in self.rate_limits_by_class.values()
        ):
            raise ValueError("rate limit values must be positive")
        return self


@lru_cache(maxsize=1)
def get_api_settings() -> ApiSettings:
    """Return process-cached immutable API settings.

    Returns:
        Validated API settings loaded through ``AppSettings``.
    """
    return ApiSettings()


__all__ = ("ApiSettings", "get_api_settings")
