"""Test domain and profile capability dependencies manifest (domains.toml)."""

from __future__ import annotations

import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOMAINS_TOML = _REPO_ROOT / "domains.toml"


def test_domains_toml_exists_and_valid() -> None:
    """Verify domains.toml exists and conforms to required schema."""
    assert _DOMAINS_TOML.is_file(), "domains.toml must exist at repo root"
    data = tomllib.loads(_DOMAINS_TOML.read_text(encoding="utf-8"))

    assert data["schema"]["version"] == 1
    assert "domain" in data
    assert "profile" in data

    # Verify core domain keys exist
    expected_domains = {
        "brokers",
        "data",
        "indicators",
        "strategy",
        "risk",
        "trading",
        "simulator",
        "analytics",
        "optimization",
        "research",
        "portfolio",
        "api",
    }
    assert expected_domains.issubset(set(data["domain"].keys()))

    # Verify safety property: live profile requires risk and trading capabilities
    live_profile = data["profile"]["live"]["required_capabilities"]
    assert any("risk." in cap for cap in live_profile), "Live profile MUST require Risk"
    assert any("trading." in cap for cap in live_profile), (
        "Live profile MUST require Trading"
    )

    # Verify safety property: demo profile requires risk
    demo_profile = data["profile"]["demo"]["required_capabilities"]
    assert any("risk." in cap for cap in demo_profile), "Demo profile MUST require Risk"

    # Verify research profile does NOT require live execution or trading
    research_profile = data["profile"]["research"]["required_capabilities"]
    assert not any("trading." in cap for cap in research_profile), (
        "Research profile must NOT require live trading"
    )
