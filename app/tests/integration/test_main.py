import pytest

from ...models.video import VideoMetadata


def test_root_redirect(client):
    """Tests if root endpoint redirects to documentation page."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_docs_endpoint(client):
    """Tests if documentation endpoint is accessible."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "swagger-ui" in response.text.lower()


def test_openapi_schema(client):
    """Tests if OpenAPI schema is properly generated."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "/" in schema["paths"]
    assert schema["info"]["title"] == "Estúdio Backend API"
