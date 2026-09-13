from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.services.recognition_service import RecognitionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.rawpics_dir.mkdir(parents=True, exist_ok=True)
    settings.qdrant_path.mkdir(parents=True, exist_ok=True)
    settings.model_cache_dir.mkdir(parents=True, exist_ok=True)

    app.state.settings = settings
    app.state.recognition_service = RecognitionService(settings)
    try:
        yield
    finally:
        app.state.recognition_service.close()


app = FastAPI(
    title="Tiger SigLIP Qdrant Object Recognition",
    version="2.0.0",
    description=(
        "Image-to-vector object recognition using SigLIP vision embeddings "
        "and persistent Qdrant Local Mode."
    ),
    lifespan=lifespan,
)
app.include_router(router)
