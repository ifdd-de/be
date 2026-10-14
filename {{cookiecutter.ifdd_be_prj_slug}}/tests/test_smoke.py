import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("IFDD_BE_AUTH_ENABLED", "false")
os.environ.setdefault("IFDD_BE_SSL_ENABLED", "false")
os.environ.setdefault("FASTAPI_SECRET_KEY", "test-secret")


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200


def test_api_documentation_is_served(client):
    # ifdd-be-core serves Swagger UI and ReDoc itself, without a CDN.
    for path in ("/docs", "/redoc", "/docs/oauth2-redirect", "/openapi.json",
                 "/docs/assets/swagger-ui/swagger-ui-bundle.js",
                 "/docs/assets/redoc/redoc.standalone.js",
                 "/docs/assets/ifdd/swagger-init.js"):
        assert client.get(path).status_code == 200, path
    assert "cdn.jsdelivr.net" not in client.get("/docs").text


def test_configured_aspect_routes_exist(client):
    from app.settings import settings

    # The OpenAPI document lists every path; app.routes does not since
    # FastAPI 0.141.1 (included routers have no 'path' of their own).
    paths = set(client.app.openapi()["paths"])
    for segment in settings.IFDD_ASPECTS:
        assert f"/{segment}" in paths
