import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


def get_frontend_dir() -> Path | None:
    """Return the built frontend folder if it exists (run `npm run build` in frontend/)."""
    configured = os.getenv("LANTERN_FRONTEND_DIST")
    folder = Path(configured) if configured else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    return folder if (folder / "index.html").is_file() else None


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

    # Serve the built website from the same address as the API, so one tunnel is
    # enough and the browser never makes a cross-origin call. Mounted last so the
    # API routes above always win.
    frontend_dir = get_frontend_dir()
    if frontend_dir:
        application.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return application


app = create_app()
