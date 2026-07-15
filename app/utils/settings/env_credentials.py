"""Generic named-credential resolution from environment sources.

Business-neutral: this module has no knowledge of any specific domain,
provider, or credential name. Callers (composition roots, usage examples)
supply their own logical-name-to-environment-variable mapping and receive
back only the named values that are actually present and non-empty, wrapped
as Pydantic secrets so they are never accidentally logged or printed.
"""

from collections.abc import Mapping
from pathlib import Path

from pydantic import SecretStr


def _strip_inline_comment(val_str: str) -> str:
    """Strip trailing inline comments not enclosed in quotes."""
    in_quote = None
    for i, char in enumerate(val_str):
        if char in ("'", '"'):
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        elif char == "#" and in_quote is None:
            return val_str[:i].strip()
    return val_str


def load_dotenv_file(path: Path) -> dict[str, str]:
    """Parse a ``KEY=VALUE`` dotenv-style file without external dependencies.

    Args:
        path: Path to the dotenv file.

    Returns:
        A mapping of parsed keys to raw string values. Returns an empty
        mapping when the file does not exist. Blank lines and lines
        starting with ``#`` are ignored.
    """
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        val_str = _strip_inline_comment(value.strip())
        is_quoted = (val_str.startswith("'") and val_str.endswith("'")) or (
            val_str.startswith('"') and val_str.endswith('"')
        )
        if is_quoted:
            val_str = val_str[1:-1]
        values[key.strip()] = val_str
    return values


def resolve_named_secrets(
    names: Mapping[str, str],
    environment: Mapping[str, str],
) -> dict[str, SecretStr]:
    """Resolve named environment variables into secret-protected values.

    Args:
        names: Mapping of caller-chosen logical name to environment variable
            name, e.g. ``{"login": "MT5_LOGIN"}``.
        environment: Source environment mapping (merged dotenv + process
            environment is a typical caller-assembled value).

    Returns:
        A mapping of the same logical names to ``SecretStr`` values, for only
        the names whose environment variable is present and non-empty.
    """
    resolved: dict[str, SecretStr] = {}
    for local_name, env_key in names.items():
        value = environment.get(env_key)
        if value:
            resolved[local_name] = SecretStr(value)
    return resolved
