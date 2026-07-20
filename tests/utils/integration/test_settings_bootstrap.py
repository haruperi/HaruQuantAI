from app.utils import load_settings


def test_settings_bootstrap_returns_immutable_validated_settings() -> None:
    """Build the immutable settings boundary from approved inputs."""
    settings = load_settings(
        {"ENVIRONMENT": "test", "LOG_RENDER": "human"},
        {"RUNTIME_PROFILE": "simulation"},
    )
    assert settings.environment == "test"
    assert settings.runtime_profile == "simulation"
    assert settings.logging.render == "human"
