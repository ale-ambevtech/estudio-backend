import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.openapi import add_custom_openapi_schema
from app.routes import processing_router, video_router, websocket_router

load_dotenv()

app = FastAPI()

add_custom_openapi_schema(app)

# Get CORS origins from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

API_PREFIX = "/api/v1"

app.include_router(video_router.router, prefix=API_PREFIX)
app.include_router(processing_router.router, prefix=API_PREFIX)
app.include_router(websocket_router.router, prefix=API_PREFIX)


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
