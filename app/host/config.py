"""Resolve and validate injected host runtime configuration.

Precedence is model defaults, the persisted host/runtime record, HARU_ environment
values, then explicit overrides. The selected data root locates the existing
unified database before other values are merged. Loading is read-only: database
creation and migration belong to persistence operations during maintenance or boot.
"""

import ipaddress
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

from pydantic import Field, SecretStr, model_validator

from app.host.contracts import Document
from app.host.logging import get_logger
from app.persistence.host import read_settings

logger = get_logger(__name__)


class HostSettings(Document):
    """Validated immutable runtime configuration passed to host components.

    Construction validates values but does not inspect TLS files or create paths.
    Password and private-key fields are excluded from model dumps and repr. Zero
    workers requests automatic sizing; session_seconds is a lifetime in seconds.
    Collection fields roots and origins are supplied through records or overrides.
    """

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    data_dir: Path = Path("data")
    password: SecretStr | None = Field(default=None, exclude=True, repr=False)
    workers: int = Field(default=0, ge=0, le=61)
    ui_dist: Path = Path("app/ui/dist")
    installation_root: Path | None = None
    roots: tuple[Path, ...] = (
        Path("app/workspace"),
        Path("app/plugin"),
        Path("app/plugins"),
    )
    open_browser: bool = False
    certificate: Path | None = None
    private_key: Path | None = Field(default=None, exclude=True, repr=False)
    origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")
    session_seconds: int = Field(default=3600, ge=1, le=86400)

    @model_validator(mode="after")
    def validate_network(self) -> Self:
        """Enforce literal bind addresses and remote-host credentials.

        This is a Pydantic after-validator. It checks configuration relationships, not
        certificate contents, file accessibility, or stored operator credentials.

        Returns:
            This validated settings instance.

        Raises:
            ValueError: The address is invalid, TLS files are unpaired, a password is
                empty, or remote binding lacks password/TLS.
        """
        address = ipaddress.ip_address(self.host)
        if bool(self.certificate) != bool(self.private_key):
            raise ValueError("Both certificate and private key are required")
        if not address.is_loopback and not (self.password and self.certificate):
            raise ValueError("Remote binding requires password and TLS")
        if self.password is not None and not self.password.get_secret_value():
            raise ValueError("Password must not be empty")
        return self

    @property
    def database_path(self) -> Path:
        """Derive the unified database location without filesystem access.

        Returns:
            data_dir/database/haruquantai.db; existence is not checked.
        """
        return self.data_dir / "database" / "haruquantai.db"

    @property
    def log_dir(self) -> Path:
        """Derive the host log directory without creating it.

        Returns:
            The logs child of the configured data directory.
        """
        return self.data_dir / "logs"


def load_settings(
    overrides: Mapping[str, Any] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> HostSettings:
    """Load a validated configuration without creating or migrating storage.

    Persisted password, private_key, and data_dir fields are forbidden. HARU_ROOTS
    and HARU_ORIGINS are not parsed as collection overrides. A missing database
    uses defaults and external overrides only.

    Args:
        overrides: Explicit field values, normally parsed CLI options; omitted values
            retain lower-precedence settings.
        environment: Environment mapping for deterministic callers; None reads
            os.environ.

    Returns:
        Frozen HostSettings with the selected data root.

    Raises:
        ValueError: Persisted JSON/version or the merged runtime configuration is
            invalid.
        HostPersistenceSchemaError: An existing settings database cannot be safely read.
    """
    env = os.environ if environment is None else environment
    explicit = dict(overrides or {})
    root = Path(explicit.get("data_dir", env.get("HARU_DATA_DIR", "data")))
    values: dict[str, Any] = {}
    path = root / "database" / "haruquantai.db"
    if path.exists():
        for record in read_settings(path):
            if record.scope == "host" and record.key == "runtime":
                if record.schema_version != 1:
                    raise ValueError("Unsupported runtime settings version")
                raw = json.loads(record.value_json)
                if not isinstance(raw, dict) or any(
                    k in raw for k in ("password", "private_key", "data_dir")
                ):
                    raise ValueError("Invalid persisted runtime configuration")
                values.update(raw)
    for name in HostSettings.model_fields:
        key = "HARU_" + name.upper()
        if key in env and name not in ("roots", "origins"):
            values[name] = env[key]
    values.update(explicit)
    values["data_dir"] = root
    result = HostSettings.model_validate(values)
    logger.debug("B02 Runtime configuration validated")
    return result
