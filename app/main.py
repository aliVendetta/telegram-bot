"""FastAPI application entry point with lifespan management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.logging_config import get_logger, setup_logging
from app.routes.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)

    logger.info("Starting application (env=%s)", settings.app_env)
    await init_db()
    logger.info("Application ready")

    yield  # app runs

    logger.info("Shutting down application")


app = FastAPI(
    title="Telegram Notes Bot",
    description="Async Telegram bot that saves notes to a database and syncs them to Notion.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health_check() -> dict:
    """Health-check endpoint for monitoring."""
    return {"status": "healthy"}
