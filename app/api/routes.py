from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.schemas import IndexStatus, RecognitionResponse

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/v1/index/status", response_model=IndexStatus)
def index_status(request: Request) -> dict:
    return request.app.state.recognition_service.status()


@router.post("/api/v1/recognize", response_model=RecognitionResponse)
def recognize_object(
    request: Request,
    file: UploadFile = File(..., description="Query image"),
    top_k: int = Query(5, ge=1, le=50),
    threshold: float | None = Query(None, ge=-1.0, le=1.0),
    ambiguity_margin: float | None = Query(None, ge=0.0, le=2.0),
) -> dict:
    settings = request.app.state.settings
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds MAX_UPLOAD_MB={settings.max_upload_mb}.",
        )

    try:
        with Image.open(BytesIO(data)) as source:
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc

    decision = request.app.state.recognition_service.recognize(
        image=image,
        top_k=top_k,
        threshold=threshold,
        ambiguity_margin=ambiguity_margin,
    )
    return {
        "recognized": decision.recognized,
        "decision": decision.decision,
        "object_id": decision.object_id,
        "object_name": decision.object_name,
        "score": decision.score,
        "candidates": decision.candidates,
    }
