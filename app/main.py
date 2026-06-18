from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    default_response_class=ORJSONResponse,
    redoc_url=None,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Return the current status of the application."""
    return {"status": "ok"}


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
    )
