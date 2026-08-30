from app.config import Settings


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        service_base_postcode="HP00 0AA",
        environment="testing",
        _env_file=None,
    )

    assert settings.service_base_postcode == "HP00 0AA"
    assert settings.environment == "testing"
