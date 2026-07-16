"""Typed credential-gated provider settings for tests and usage examples."""

from __future__ import annotations

from typing import Literal

from app.utils import AppSettings
from pydantic import SecretStr


class ProviderTestSettings(AppSettings):
    """Immutable provider credentials loaded only by the shared settings boundary."""

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


__all__ = ["ProviderTestSettings"]
