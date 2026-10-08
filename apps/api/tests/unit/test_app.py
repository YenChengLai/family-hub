from family_hub.config import Settings
from family_hub.main import create_app


def test_api_docs_disabled_in_production() -> None:
    app = create_app(Settings(environment="production", secret_key="x" * 32))

    assert app.openapi_url is None
    assert app.docs_url is None


def test_api_docs_enabled_outside_production() -> None:
    app = create_app(Settings(environment="development"))

    assert app.openapi_url == "/api/v1/openapi.json"
