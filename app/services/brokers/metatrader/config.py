"""Configuration dataclass for MetaTrader 5 connection feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {"database_path", "terminal_path", "login", "password", "server", "timeout"}
)


@dataclass(frozen=True, slots=True)
class MetaTraderConfig:
    """Configuration options for MetaTrader 5 connection.

    Attributes:
        database_path: Optional path to SQLite central database.
        terminal_path: Path to terminal64.exe executable.
        login: MT5 account login number.
        password: MT5 account password.
        server: MT5 broker server name.
        timeout: Connection timeout in seconds.
    """

    database_path: Path | None = None
    terminal_path: str | None = None
    login: int | None = None
    password: str | None = None
    server: str | None = None
    timeout: int = 30

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MetaTraderConfig:
        """Parse configuration mapping.

        Args:
            data: Raw feature configuration mapping.

        Returns:
            Validated immutable MetaTraderConfig instance.

        Raises:
            TypeError: If database_path, login, or timeout have invalid types.
            ValueError: If unknown keys are provided or strings are blank.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            msg = f"Unknown MetaTrader configuration keys: {', '.join(sorted(unknown))}"
            raise ValueError(msg)

        raw_db = data.get("database_path")
        db_path = None
        if raw_db is not None:
            if not isinstance(raw_db, (str, Path)):
                msg = "database_path must be a string or Path"
                raise TypeError(msg)
            str_db = str(raw_db).strip()
            if not str_db:
                msg = "database_path cannot be an empty string"
                raise ValueError(msg)
            db_path = Path(str_db)

        raw_term = data.get("terminal_path")
        term_path = str(raw_term).strip() if raw_term is not None else None

        raw_login = data.get("login")
        login_val = None
        if raw_login is not None:
            if isinstance(raw_login, int):
                login_val = raw_login
            elif isinstance(raw_login, str) and raw_login.strip().isdigit():
                login_val = int(raw_login.strip())
            else:
                msg = "login must be an integer or digit string"
                raise TypeError(msg)

        raw_pwd = data.get("password")
        pwd_val = str(raw_pwd).strip() if raw_pwd is not None else None

        raw_srv = data.get("server")
        srv_val = str(raw_srv).strip() if raw_srv is not None else None

        raw_timeout = data.get("timeout", 30)
        if not isinstance(raw_timeout, int) or raw_timeout <= 0:
            msg = "timeout must be a positive integer"
            raise TypeError(msg)

        return cls(
            database_path=db_path,
            terminal_path=term_path,
            login=login_val,
            password=pwd_val,
            server=srv_val,
            timeout=raw_timeout,
        )
