"""GodDamnEye - Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import api_router
from backend.config import get_settings
from backend.core.database import async_session_maker, close_db, init_db
from backend.core.security import AuthMiddleware
from backend.services.camera_manager import camera_manager
from backend.services.storage_manager import storage_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def db_session_factory():
    """Database session factory for services.

    Wraps async_session_maker as an async context manager
    for use by camera_manager and other services.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Ensure directories exist
    settings.get_storage_path()
    settings.get_hls_path()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start camera manager (loads enabled cameras and starts streaming)
    await camera_manager.start(db_session_factory)
    logger.info("Camera manager started")

    # Start storage manager (background cleanup and scanning)
    await storage_manager.start(db_session_factory)
    logger.info("Storage manager started")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Stop storage manager
    await storage_manager.stop()
    logger.info("Storage manager stopped")

    # Stop camera manager (stops all stream workers)
    await camera_manager.stop()
    logger.info("Camera manager stopped")

    # Close database
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Open-source CCTV camera management system with RTSP/ONVIF support",
        version=settings.app_version,
        license_info={
            "name": "AGPL-3.0-or-later",
            "url": "https://www.gnu.org/licenses/agpl-3.0.html",
        },
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware (currently pass-through for MVP)
    app.add_middleware(AuthMiddleware)

    # API routes
    app.include_router(api_router)

    # Mount static files for HLS streaming
    # This will serve files from /tmp/goddamneye/hls at /hls/
    try:
        hls_path = settings.get_hls_path()
        app.mount("/hls", StaticFiles(directory=str(hls_path)), name="hls")
    except Exception as e:
        logger.warning(f"Could not mount HLS directory: {e}")

    return app


# Create application instance
app = create_app()


def run():
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
