import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = tuple(sorted((_ROOT / "tests" / "utils" / "usage").glob("[0-9][0-9]_*.py")))


@pytest.mark.parametrize("script", _SCRIPTS, ids=lambda path: path.name)
def test_usage_script_executes_directly(script: Path) -> None:
    expected_markers = {
        "01_contracts.py": "AuthContext:",
        "02_errors.py": "Mapped exception:",
        "03_identity.py": "Generated request ID:",
        "04_time.py": "Current UTC time:",
        "05_serialization.py": "Canonical JSON:",
        "06_security.py": "Redaction policy:",
        "07_settings.py": "Safe .env application settings:",
        "08_logging.py": "Logging verification:",
    }
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(_ROOT)
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(script)],
        cwd=_ROOT,
        capture_output=True,
        check=False,
        env=environment,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert expected_markers[script.name] in completed.stdout
    if script.name == "07_settings.py":
        sensitive_keys = (
            "MT5_LOGIN",
            "MT5_PASSWORD",
            "MT5_TERMINAL_PATH",
            "CTRADER_ACCOUNT_ID",
            "CTRADER_CLIENT_ID",
            "CTRADER_CLIENT_SECRET",
            "CTRADER_ACCESS_TOKEN",
            "CTRADER_REFRESH_TOKEN",
            "CTRADER_REDIRECT_URL",
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_FROM_PHONE",
            "JWT_SECRET_KEY",
            "DATA_ENCRYPTION_KEY",
            "LANGCHAIN_API_KEY",
            "DATABASE_URL",
        )
        displayed_keys = {
            line.strip().split("=", 1)[0]
            for line in completed.stdout.splitlines()
            if line.startswith("  ") and "=" in line
        }
        assert displayed_keys.isdisjoint(sensitive_keys)
