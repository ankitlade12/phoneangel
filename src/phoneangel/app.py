"""PhoneAngel — AI Phone Call Agent & Coach for Autistic Adults.

Built on DigitalOcean Gradient AI for the Gradient AI Hackathon (dev server).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog

from phoneangel.config import settings
from phoneangel.models.database import init_db
from phoneangel.api.routes import router

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    log.info("phoneangel.starting", mode="development" if settings.DEBUG else "production")
    await init_db()
    log.info("phoneangel.db_ready")
    yield
    log.info("phoneangel.shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered phone call accessibility tool for autistic adults. "
        "Three modes: Prep (visualize the call), Coach (live guidance), "
        "and Proxy (AI calls for you)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router)


def main():
    """CLI entry point."""
    import uvicorn

    uvicorn.run(
        "phoneangel.app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
