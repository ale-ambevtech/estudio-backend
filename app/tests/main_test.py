from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)


def test_root_redirect():
    """
    Tests if root endpoint redirects to documentation page.

    The root endpoint (/) should:
    1. Return a 307 status code (redirect)
    2. Redirect to the /docs endpoint
    3. Include proper redirect headers
    """
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_docs_endpoint():
    """
    Tests if documentation endpoint is accessible.

    The docs endpoint (/docs) should:
    1. Return a 200 status code
    2. Return HTML content
    3. Include Swagger UI elements
    """
    response = client.get("/docs")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "swagger-ui" in response.text.lower()


def test_openapi_schema():
    """
    Tests if OpenAPI schema is properly generated.

    The OpenAPI schema endpoint (/openapi.json) should:
    1. Return a 200 status code
    2. Return JSON content
    3. Include basic API information
    4. Include all defined routes
    """
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema

    # Verify root path is in schema
    assert "/" in schema["paths"]

    # Verify API metadata
    assert (
        schema["info"]["title"] == "Estúdio Backend API"
    )  # Adjust according to your API title
