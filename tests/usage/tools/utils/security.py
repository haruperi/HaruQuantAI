"""
Usage example for tools.utils.security.

Run from the project root:

    python tests/usage/tools/utils/security.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import (
    SecretRef,
    SecretRotationPolicy,
    redact_mapping,
    redact_text,
    select_active_secret_version,
)
from tools.utils.security import (
    decrypt_data_value,
    encrypt_data_value,
    generate_encryption_key,
)

request_id = "usage-security-001"

config = {
    "username": "haru",
    "password": "do-not-log-this",
    "broker": {"api_key": "secret-api-key", "server": "demo"},
}

redacted_config = redact_mapping(config, request_id=request_id)
print(redacted_config["data"]["redacted_mapping"])

redacted_log = redact_text(
    "Authorization: Bearer abc.def.ghi password=hidden",
    request_id=request_id,
)
print(redacted_log["data"]["redacted_text"])

refs = [
    SecretRef("mt5-password", "v1", datetime(2026, 1, 1, tzinfo=timezone.utc)),
    SecretRef("mt5-password", "v2", datetime(2026, 2, 1, tzinfo=timezone.utc)),
]
policy = SecretRotationPolicy("mt5-password", max_age_days=30)
selected = select_active_secret_version(refs, policy, request_id=request_id)
print(selected["data"]["secret_ref"])

# Internal application utility example only. Do not expose plaintext or keys to agents.
key = generate_encryption_key()
token = encrypt_data_value("secret-value", key)
assert decrypt_data_value(token, key) == "secret-value"
