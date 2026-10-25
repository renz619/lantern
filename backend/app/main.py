import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import changes, find, scans


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def get_cors_origins() -> list[str]:
    """Return configured frontend origins or safe local-development defaults."""
    configured_origins = os.getenv("LANTERN_CORS_ORIGINS")
    if not configured_origins:
        return list(DEFAULT_CORS_ORIGINS)

    return [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]


def create_app() -> FastAPI:
    application = FastAPI(title="Lantern API")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    application.include_router(scans.router)
    application.include_router(find.router)
    application.include_router(changes.router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
