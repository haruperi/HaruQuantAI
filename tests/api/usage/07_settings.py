"""Standalone Settings boundary usage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.kernel.identity import generate_id
from app.services.api import (
    build_system_broker_connection_config,
    create_api_app,
    get_canonical_route_contract_registry,
    get_system_credential_statuses,
    get_system_settings,
    resolve_system_credential_slot,
    run_api_migrations,
)


def main() -> None:
    """Verify Settings route contracts and print system settings and MT5 credential resolution."""
    req_id = generate_id("req")
    run_api_migrations(req_id)

    application = create_api_app()
    operations = {
        (method.upper(), path)
        for path, path_item in application.openapi()["paths"].items()
        for method in path_item
    }
    contracts = get_canonical_route_contract_registry()
    declarations = {(item.method, item.path) for item in contracts.all()}
    settings_routes = {
        (method, path) for method, path in operations if "/settings" in path
    }
    assert settings_routes <= declarations
    assert settings_routes == {
        ("GET", "/api/v1/settings"),
        ("GET", "/api/v1/settings/credentials"),
        ("GET", "/api/v1/settings/manifest"),
        ("PUT", "/api/v1/settings"),
        ("PUT", "/api/v1/settings/credentials/{slot}"),
    }

    # 1. System Settings from api_settings table
    system_settings_record = get_system_settings(request_id=generate_id("req"))
    print("\n=== System Settings (api_settings) ===")
    print(f"Scope: {system_settings_record.scope}")
    print(f"Version: {system_settings_record.version}")
    print(f"Updated At: {system_settings_record.updated_at}")
    print(f"Settings: {system_settings_record.settings}")

    # 2. Credentials Statuses from api_credentials table
    credential_statuses = get_system_credential_statuses(request_id=generate_id("req"))
    print("\n=== System Credentials Statuses (api_credentials) ===")
    for status in credential_statuses:
        print(
            f"Slot: {status['slot']} | Configured: {status['configured']} | "
            f"Version: {status['version']} | Label: {status['label']}"
        )

    # 3. MT5 Credential & Broker Config Resolution
    print("\n=== MT5 System Credential Slot Resolution ===")
    mt5_credentials = resolve_system_credential_slot(
        "mt5", request_id=generate_id("req")
    )
    print(f"MT5 Credentials Resolved Fields: {list(mt5_credentials.keys())}")
    mt5_config = build_system_broker_connection_config(
        "mt5", request_id=generate_id("req")
    )
    print(f"MT5 Connection Config Broker ID: {getattr(mt5_config, 'broker_id', 'mt5')}")
    print(f"MT5 Account Reference: {getattr(mt5_config, 'account_reference', None)}")

    print(
        "\nSummary:",
        {
            "feature": "settings",
            "operations": len(settings_routes),
            "system_settings_count": len(system_settings_record.settings),
            "credential_slots_count": len(credential_statuses),
        },
    )


if __name__ == "__main__":
    main()
