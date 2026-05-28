"""
Usage example for the merged tools.utils.config module.

Run from the project root:

    python tests/usage/tools/utils/config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import (
    get_settings,
    inject_runtime_settings,
    load_runtime_settings_from_mapping,
)

request_id = "usage-config-001"

simple_settings = get_settings()
print(
    {
        "environment": simple_settings.environment,
        "app_name": simple_settings.app_name,
        "log_level": simple_settings.log_level,
    }
)

runtime_result = load_runtime_settings_from_mapping(
    {
        "environment": "test",
        "app_name": "haruquant",
        "api_host": "127.0.0.1",
        "api_port": 8000,
        "log_level": "INFO",
        "custom_runtime_flag": "enabled",
    },
    request_id=request_id,
)

if runtime_result["status"] == "success":
    runtime_state: dict[str, object] = {}
    injection = inject_runtime_settings(
        runtime_state,
        runtime_result["data"],
        request_id=request_id,
    )
    print(injection["status"], runtime_state["environment"])
else:
    print(runtime_result["error"])
