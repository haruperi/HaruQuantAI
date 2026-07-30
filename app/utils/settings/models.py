"""Immutable validated runtime and logging settings models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, override

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.utils.errors.exceptions import ConfigurationError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
LogRender = Literal["json", "human"]
LogCompression = Literal["zip", "none"]
Environment = Literal["dev", "test", "staging", "production"]
RuntimeProfile = Literal["research", "simulation", "paper", "live"]
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _flatten_leaf(
    next_path: tuple[str, ...], value: object, result: dict[str, Any]
) -> None:
    """Record candidate field key names for a primitive JSON leaf node.

    Args:
        next_path: Sequence of path keys identifying the leaf node.
        value: Primitive value to assign to candidate key names.
        result: Dictionary accumulator receiving candidate settings mappings.
    """
    if len(next_path) > 1:
        joined = "_".join(next_path)
        result[joined] = value
        result[joined.upper()] = value

    if next_path == ("environment", "current"):
        result["environment"] = value
        result["ENVIRONMENT"] = value
    elif next_path == ("google_genai", "agent_model"):
        result["google_agent_model"] = value
        result["GOOGLE_AGENT_MODEL"] = value

    leaf_key = next_path[-1]
    if leaf_key.lower() == "environment" and next_path != ("environment", "current"):
        return

    if leaf_key not in result:
        result[leaf_key] = value
        result[leaf_key.upper()] = value


def _flatten_json(obj: object, path: tuple[str, ...] = ()) -> dict[str, Any]:
    """Recursively flatten nested JSON objects into a lookup dictionary.

    Args:
        obj: Raw JSON object node.
        path: Accumulated path of dictionary keys.

    Returns:
        Mapping of candidate field key names to primitive JSON values.
    """
    result: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                next_path = (*path, key) if path or key != "settings" else ()
                if isinstance(value, dict):
                    result.update(_flatten_json(value, next_path))
                elif next_path:
                    _flatten_leaf(next_path, value, result)
    return result


class _CentralJsonSettingsSource(JsonConfigSettingsSource):
    """Central JSON source matching aliases, uppercase, and exact field names.

    The stock JSON source matches file keys to field names case-sensitively,
    while the repository central settings file uses uppercase environment-style
    or nested snake_case keys. This source reproduces the previous dotenv
    name-matching behavior so every ``AppSettings`` subclass loads identically
    from the JSON file.
    """

    @override
    def __call__(self) -> dict[str, Any]:
        """Return field values loaded from the central JSON settings file.

        Returns:
            Mapping of field aliases or names to raw JSON values; empty when the
            configured file is missing or its root is not an object.
        """
        json_file = self.settings_cls.model_config.get("json_file")
        if json_file is None or not Path(str(json_file)).is_file():
            return {}
        raw: object = json.loads(Path(str(json_file)).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        flattened = _flatten_json(raw)
        values: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            alias = (
                field.validation_alias
                if isinstance(field.validation_alias, str)
                else None
            )
            candidates = ([alias] if alias else []) + [field_name.upper(), field_name]
            for key in candidates:
                if key in flattened:
                    values[alias or field_name] = flattened[key]
                    break
        return values


class AppSettings(BaseSettings):
    """Immutable base for typed settings loaded from the central environment."""

    model_config = SettingsConfigDict(
        json_file=_REPOSITORY_ROOT / "app" / "configs" / "env.json",
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
        """Add the centralized JSON settings file after process overrides.

        Args:
            settings_cls: The settings class being constructed.
            init_settings: Explicit constructor values source.
            env_settings: Process environment source.
            dotenv_settings: Dotenv file source (unused; no env_file configured).
            file_secret_settings: File secrets source.

        Returns:
            Settings sources in precedence order.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            _CentralJsonSettingsSource(settings_cls),
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

    level: LogLevel = "DEBUG"
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


class BrokerProviderSettings(AppSettings):
    """Immutable broker-provider credentials loaded from the central settings file.

    This is the single source of truth for broker connection material. It extends
    ``AppSettings`` so values are read from ``app/configs/env.json`` (under
    ``settings.<provider>.*``) through the shared ``_CentralJsonSettingsSource``,
    with process environment overrides taking precedence. Broker credential
    resolution is owned by the Brokers domain; Data and usage examples select a
    route only and never read these fields directly.

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
