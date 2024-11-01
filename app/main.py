from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.openapi import add_custom_openapi_schema
from app.routes import processing_router, video_router

app = FastAPI()

add_custom_openapi_schema(app)

app.include_router(video_router.router, prefix="/api/v1")
app.include_router(processing_router.router, prefix="/api/v1")


@app.get(
    "/",
    responses={307: {"description": "Redirects to API documentation"}},
    response_class=RedirectResponse,
)
def root() -> RedirectResponse:
    """
    Redirects user to the API documentation page.

    Returns:
        RedirectResponse: Redirect to /docs endpoint.

    Examples:
        >>> from fastapi.testclient import TestClient
        >>> from app.main import app
        >>> client = TestClient(app)
        >>> response = client.get("/", follow_redirects=False)
        >>> assert response.status_code == 307
        >>> assert response.headers["location"] == "/docs"
    """
    return RedirectResponse(url="/docs")
