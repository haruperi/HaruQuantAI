"""Display safe application settings from the repository ``.env`` file."""

from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_SAFE_ENV_KEYS = (
    "ENVIRONMENT",
    "APP_NAME",
    "API_HOST",
    "API_PORT",
    "UI_ORIGIN",
    "LOG_LEVEL",
    "HOME_DIR",
    "DATA_DIR",
    "CACHE_DIR",
    "AUDIT_DIR",
    "TIMEZONE",
    "MT5_ENABLED",
    "MT5_ENVIRONMENT",
    "CTRADER_ENABLED",
    "CTRADER_ENVIRONMENT",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "HARUQUANT_AGENT_MODEL",
    "HARUQUANT_FAST_MODEL",
    "HARUQUANT_PREMIUM_MODEL",
    "HARUQUANT_FALLBACK_MODEL",
    "HARUQUANT_TEMPERATURE",
    "HARUQUANT_MAX_TOKENS",
    "HARUQUANT_TOP_P",
    "HARUQUANT_TOP_K",
    "JWT_ALGORITHM",
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_PROJECT",
)


def example_construct_configuration() -> dict[str, str]:
    """Load only allowlisted non-secret values from the repository ``.env``."""
    if not _ENV_PATH.is_file():
        return {}
    allowed = frozenset(_SAFE_ENV_KEYS)
    settings: dict[str, str] = {}
    for raw_line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        if normalized_key in allowed:
            normalized_value = value.strip()
            if not normalized_value.startswith(('"', "'")):
                normalized_value = normalized_value.split(" #", 1)[0].rstrip()
            settings[normalized_key] = normalized_value.strip("\"'")
    return settings


def main() -> None:
    """Display safe application values from the repository ``.env`` file."""
    settings = example_construct_configuration()
    print("Safe .env application settings:")
    if not settings:
        print("  No allowlisted settings found.")
        return
    for key in _SAFE_ENV_KEYS:
        if key in settings:
            print(f"  {key}={settings[key]}")


if __name__ == "__main__":
    main()
