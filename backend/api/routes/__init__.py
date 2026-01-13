"""API route modules."""

from fastapi import APIRouter

from backend.api.routes import cameras, recordings, streams, system

api_router = APIRouter(prefix="/api")

api_router.include_router(system.router, tags=["system"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(streams.router, prefix="/streams", tags=["streams"])
api_router.include_router(recordings.router, prefix="/recordings", tags=["recordings"])
