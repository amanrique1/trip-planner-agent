from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from api.routes import router
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    # startup
    yield
    # shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trip Planner API",
        description="AI-powered trip planner backed by Google ADK agents.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Security middleware ───────────────────────────────────────────────────
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],   # tighten in production: ["yourdomain.com"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tighten in production
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


application = create_app()


def start() -> None:
    """Entry-point used by `trip-planner-api` script."""
    uvicorn.run(
        "api.app:application",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=False,
    )


if __name__ == "__main__":
    start()