from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _path_from_env(name: str, default_relative: str) -> Path:
    raw = os.getenv(name)
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    return (PROJECT_ROOT / default_relative).resolve()


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    rawpics_dir: Path = _path_from_env("RAWPICS_DIR", "rawpics")
    qdrant_path: Path = _path_from_env("QDRANT_PATH", "data/qdrant")
    model_cache_dir: Path = _path_from_env("MODEL_CACHE_DIR", "models/hf_cache")
    manifest_path: Path = _path_from_env("MANIFEST_PATH", "data/index_manifest.json")

    model_id: str = os.getenv("SIGLIP_MODEL_ID", "google/siglip-base-patch16-224")
    device: str = os.getenv("SIGLIP_DEVICE", "auto")
    collection_name: str = os.getenv("QDRANT_COLLECTION", "object_images")

    match_threshold: float = float(os.getenv("MATCH_THRESHOLD", "0.80"))
    ambiguity_margin: float = float(os.getenv("AMBIGUITY_MARGIN", "0.03"))
    query_reference_multiplier: int = int(os.getenv("QUERY_REFERENCE_MULTIPLIER", "5"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    batch_size: int = int(os.getenv("INDEX_BATCH_SIZE", "16"))

    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "18080"))


settings = Settings()
