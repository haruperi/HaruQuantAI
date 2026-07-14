from app.utils import load_settings, resolve_secret_reference


def test_settings_bootstrap_and_secret_handoff() -> None:
    settings = load_settings(
        {"ENVIRONMENT": "test", "LOG_RENDER": "human"},
        {"RUNTIME_PROFILE": "simulation"},
    )
    secret = resolve_secret_reference("secret://broker/demo", lambda _: "abc123")
    assert settings.environment == "test"
    assert settings.runtime_profile == "simulation"
    assert settings.logging.render == "human"
    assert secret.get_secret_value() == "abc123"
