"""Immutable validated runtime and logging settings models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, override

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.utils.errors.exceptions import ConfigurationError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
LogRender = Literal["json", "human"]
LogCompression = Literal["zip", "none"]
Environment = Literal["dev", "test", "staging", "production"]
RuntimeProfile = Literal["research", "simulation", "paper", "live"]


class AppSettings(BaseSettings):
    """Immutable base for explicit values and external bootstrap environment."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
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
        """Declare explicit and external bootstrap settings sources.

        Args:
            settings_cls: The settings class being constructed.
            init_settings: Explicit constructor values source.
            env_settings: Process environment source.
            dotenv_settings: Dotenv file source (unused; no env_file configured).
            file_secret_settings: File secrets source.

        Returns:
            Settings sources in precedence order, excluding repository files.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class _ConfigurationModel(BaseModel):
    """Base model that maps Pydantic failures to shared configuration errors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def __init__(self, **data: object) -> None:
        """Initialize the configuration model, mapping Pydantic validation errors.

        Args:
            data: Arbitrary keyword settings arguments.

        Raises:
            ConfigurationError: If any of the values violate field
                validation constraints.
        """
        try:
            super().__init__(**data)
        except PydanticValidationError:
            raise ConfigurationError("CONFIGURATION_INVALID") from None


class LoggingSettings(_ConfigurationModel):
    """Immutable bounded structured-logging settings.

    Attributes:
        level: Log severity filter level.
        render: Log output style format, human or json.
        file_path: Optional path to write a single log file to.
        log_directory: Optional directory path to write structured logs.
        max_bytes: Size in bytes at which log files roll over.
        backup_count: Maximum count of rotated log files to retain.
        retention_days: Number of days to keep rotated logs before deletion.
        compression: Mode of compression to apply to rotated logs.
        enqueue: If True, writes logs asynchronously via a background queue.
        colorize: If True, adds color escape sequences to terminal logs.
    """

    level: LogLevel = "INFO"
    render: LogRender = "human"
    file_path: Path | None = None
    log_directory: Path | None = Path("data/logs")
    max_bytes: int = Field(default=10_000_000, ge=1_024, le=100_000_000)
    backup_count: int = Field(default=10, ge=1, le=20)
    retention_days: int = Field(default=10, ge=1, le=365)
    compression: LogCompression = "zip"
    enqueue: bool = True
    colorize: bool = True


class RuntimeSettings(_ConfigurationModel):
    """Immutable generic runtime settings.

    Attributes:
        environment: Standard environment classification name.
        runtime_profile: Standard runtime profile categorization name.
        logging: Configured sub-settings representing logging configuration.
    """

    environment: Environment = "dev"
    runtime_profile: RuntimeProfile = "research"
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


class BrokerProviderSettings(_ConfigurationModel):
    """Immutable broker-provider settings supplied by a composition root.

    UI/API resolves database-backed values and injects this secret-redacting
    model at the application composition boundary. Constructing it without
    explicit values is deliberately disabled/default-only and cannot discover
    credentials from repository files or process environment.

    Attributes:
        mt5_enabled: Whether the MT5 provider connection is permitted.
        mt5_environment: MT5 connection environment, demo or live.
        mt5_login: MT5 account login identifier.
        mt5_password: MT5 account password.
        mt5_server: MT5 broker server name.
        mt5_terminal_path: Optional path to the MT5 terminal executable.
        ctrader_enabled: Whether the cTrader provider connection is permitted.
        ctrader_environment: cTrader connection environment, demo or live.
        ctrader_account_id: cTrader trading account identifier.
        ctrader_client_id: cTrader OAuth client identifier.
        ctrader_client_secret: cTrader OAuth client secret.
        ctrader_access_token: cTrader API access token.
        binance_enabled: Whether the Binance Spot provider connection is permitted.
        binance_environment: Binance Spot connection environment (testnet).
        dukascopy_enabled: Whether the Dukascopy provider connection is permitted.
        yahoo_enabled: Whether the Yahoo provider connection is permitted.
        firecrawl_api_key: Licensed Firecrawl scraping-intermediary API key used
            by the Data economic-calendar transport.
    """

    mt5_enabled: bool = False
    mt5_environment: Literal["demo", "live"] = "demo"
    mt5_login: SecretStr | None = None
    mt5_password: SecretStr | None = None
    mt5_server: SecretStr | None = None
    mt5_terminal_path: SecretStr | None = None
    ctrader_enabled: bool = False
    ctrader_environment: Literal["demo", "live"] = "demo"
    ctrader_account_id: SecretStr | None = None
    ctrader_client_id: SecretStr | None = None
    ctrader_client_secret: SecretStr | None = None
    ctrader_access_token: SecretStr | None = None
    binance_enabled: bool = False
    binance_environment: Literal["testnet"] = "testnet"
    dukascopy_enabled: bool = False
    yahoo_enabled: bool = False
    # Licensed Firecrawl scraping-intermediary API key used by the Data
    # economic-calendar transport; the central file stores it as
    # settings.firecrawl.firecrawl.
    firecrawl_api_key: SecretStr | None = Field(
        default=None, validation_alias="firecrawl_firecrawl"
    )
