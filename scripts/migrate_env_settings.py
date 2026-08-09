"""One-time fail-closed migration from legacy env.json to API-owned storage."""

from __future__ import annotations

import argparse
import base64
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from app.services.api import (
    get_legacy_settings_classification,
    get_system_settings,
    run_api_migrations,
    store_system_credential,
    update_system_settings,
)
from app.utils import generate_id

_DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "app" / "configs" / "env.json"
_ENCRYPTION_KEY_BYTES = 32


def _leaf_values(value: object, path: tuple[str, ...] = ()) -> dict[str, object]:
    """Flatten one JSON object to dotted leaf paths.

    Args:
        value: JSON-compatible node.
        path: Current object path.

    Returns:
        Dotted leaf paths mapped to their values.
    """
    if not isinstance(value, dict):
        return {".".join(path): value}
    result: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(key, str):
            result.update(_leaf_values(item, (*path, key)))
    return result


def _encryption_bootstrap() -> tuple[Mapping[str, bytes], str]:
    """Load the externally provisioned one-time credential encryption key.

    Returns:
        Single-key mapping and active key identifier.

    Raises:
        RuntimeError: If bootstrap is absent or invalid.
    """
    key_id = os.environ.get("ACTIVE_CREDENTIAL_KEY_ID", "")
    encoded = os.environ.get("CREDENTIAL_ENCRYPTION_KEY", "")
    try:
        key = base64.urlsafe_b64decode(encoded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError("credential encryption bootstrap is invalid") from error
    if not key_id or len(key) != _ENCRYPTION_KEY_BYTES:
        raise RuntimeError("credential encryption bootstrap is missing or invalid")
    return {key_id: key}, key_id


def _setting_text(value: object) -> str:
    """Serialize one JSON scalar to its canonical settings representation.

    Args:
        value: Legacy JSON scalar.

    Returns:
        Lowercase JSON booleans or the ordinary scalar text.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.casefold() in {"false", "true"}:
        return value.casefold()
    return str(value)


def migrate(source: Path, *, apply: bool) -> dict[str, object]:
    """Classify and optionally persist every legacy configuration leaf.

    Args:
        source: Legacy JSON source path.
        apply: Whether to persist after validation; false performs a dry run.

    Returns:
        Secret-free migration summary.

    Raises:
        RuntimeError: If environment safety or classification is incomplete.
        TypeError: If the legacy document root is not an object.
    """
    if os.environ.get("ENVIRONMENT", "dev").casefold() != "dev":
        raise RuntimeError("migration is restricted to ENVIRONMENT=dev")
    parsed: object = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise TypeError("legacy settings root must be an object")
    leaves = _leaf_values(parsed)
    classification = cast(
        "Mapping[str, Mapping[str, str]]",
        get_legacy_settings_classification(),
    )
    unknown = sorted(set(leaves) - set(classification))
    if unknown:
        detail = f"unclassified legacy settings: {', '.join(unknown)}"
        raise RuntimeError(detail)

    system_values: dict[str, str] = {}
    credentials: dict[str, dict[str, str]] = {}
    bootstrap: list[str] = []
    for path, value in leaves.items():
        rule = classification[path]
        category = str(rule["classification"])
        if category == "system":
            system_values[str(rule["target"])] = _setting_text(value)
        elif category == "credential":
            credentials.setdefault(str(rule["target"]), {})[str(rule["field"])] = str(
                value
            )
        else:
            bootstrap.append(str(rule["target"]))

    if apply:
        request_id = generate_id("req")
        run_api_migrations(request_id)
        current = cast("Any", get_system_settings(request_id=generate_id("req")))
        update_system_settings(
            system_values,
            actor_id="env-json-migration",
            expected_version=current.version,
            request_id=generate_id("req"),
        )
        if credentials:
            key_set, active_key_id = _encryption_bootstrap()
            for slot, material in sorted(credentials.items()):
                store_system_credential(
                    slot,
                    material,
                    key_set=key_set,
                    active_key_id=active_key_id,
                    request_id=generate_id("req"),
                )
    return {
        "mode": "apply" if apply else "dry-run",
        "system_setting_count": len(system_values),
        "credential_slot_count": len(credentials),
        "external_bootstrap_keys": sorted(bootstrap),
        "source_deleted": False,
    }


def main() -> None:
    """Run the bounded migration utility and print its secret-free summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=_DEFAULT_SOURCE)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(args.source, apply=args.apply), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
