from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from qdrant_client import models

from app.config import Settings
from app.services.qdrant_store import QdrantStore
from app.services.siglip_embedder import SiglipEmbedder

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    relative_path: str
    object_id: str
    object_name: str
    source_folder: str


def discover_images(rawpics_dir: Path) -> list[Path]:
    rawpics_dir.mkdir(parents=True, exist_ok=True)
    return sorted(
        path
        for path in rawpics_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def normalize_object_id(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[\s\-]+", "_", value)
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        raise ValueError(f"Cannot normalize object id from {value!r}")
    return value


def resolve_object_id(path: Path, rawpics_dir: Path) -> tuple[str, str, str]:
    """Use the first rawpics child directory as the class/object id.

    Preferred layout:
      rawpics/tiger/01.jpg
      rawpics/tiger/02.jpg
      rawpics/blue_whale/01.jpg

    Flat-file fallback:
      rawpics/tiger__01.jpg -> tiger
      rawpics/photo.jpg     -> photo
    """
    relative = path.relative_to(rawpics_dir)
    if len(relative.parts) > 1:
        source_folder = relative.parts[0]
        raw_id = source_folder
    elif "__" in path.stem:
        raw_id = path.stem.split("__", 1)[0]
        source_folder = raw_id
    else:
        raw_id = path.stem
        source_folder = raw_id

    object_id = normalize_object_id(raw_id)
    object_name = source_folder.strip() or object_id
    return object_id, object_name, source_folder


def validate_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def make_record(path: Path, rawpics_dir: Path) -> ImageRecord:
    object_id, object_name, source_folder = resolve_object_id(path, rawpics_dir)
    return ImageRecord(
        path=path,
        relative_path=path.relative_to(rawpics_dir).as_posix(),
        object_id=object_id,
        object_name=object_name,
        source_folder=source_folder,
    )


def deterministic_point_id(relative_path: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"tiger-siglip://{relative_path.lower()}"))


def build_index(settings: Settings) -> dict:
    all_paths = discover_images(settings.rawpics_dir)
    if not all_paths:
        raise RuntimeError(f"No images found in {settings.rawpics_dir}")

    valid_records: list[ImageRecord] = []
    invalid_images: list[dict[str, str]] = []
    for path in all_paths:
        error = validate_image(path)
        if error:
            invalid_images.append({
                "relative_path": path.relative_to(settings.rawpics_dir).as_posix(),
                "error": error,
            })
            continue
        valid_records.append(make_record(path, settings.rawpics_dir))

    if invalid_images:
        sample = invalid_images[:5]
        raise RuntimeError(
            f"Found {len(invalid_images)} invalid image(s). Fix them before indexing. Sample: {sample}"
        )
    if not valid_records:
        raise RuntimeError("No valid images found.")

    counts = Counter(record.object_id for record in valid_records)
    print(f"Classes: {len(counts)} | Images: {len(valid_records)}")
    for name, count in sorted(counts.items()):
        print(f"  {name}: {count}")

    embedder = SiglipEmbedder(
        model_id=settings.model_id,
        cache_dir=settings.model_cache_dir,
        device=settings.device,
    )
    store = QdrantStore(settings.qdrant_path, settings.collection_name)

    try:
        # Load model first, then rebuild Qdrant. This avoids deleting a usable index
        # when the model cannot be loaded/downloaded.
        vector_size = embedder.dimension
        print(f"SigLIP device: {embedder.device}")
        print(f"Vector dimension: {vector_size}")
        store.rebuild_collection(vector_size)

        indexed_count = 0
        batch_size = max(1, settings.batch_size)
        for start in range(0, len(valid_records), batch_size):
            batch = valid_records[start : start + batch_size]
            vectors = embedder.embed_paths([record.path for record in batch])
            points = [
                models.PointStruct(
                    id=deterministic_point_id(record.relative_path),
                    vector=vector,
                    payload={
                        "object_id": record.object_id,
                        "object_name": record.object_name,
                        "source_folder": record.source_folder,
                        "relative_path": record.relative_path,
                        "file_name": record.path.name,
                    },
                )
                for record, vector in zip(batch, vectors, strict=True)
            ]
            store.upsert(points)
            indexed_count += len(points)
            print(f"Indexed {indexed_count}/{len(valid_records)} images")

        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model_id": settings.model_id,
            "device": embedder.device,
            "vector_size": vector_size,
            "distance": "Cosine",
            "collection_name": settings.collection_name,
            "rawpics_dir": str(settings.rawpics_dir),
            "qdrant_path": str(settings.qdrant_path),
            "image_count": indexed_count,
            "object_count": len(counts),
            "objects": dict(sorted(counts.items())),
        }
        settings.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        settings.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return manifest
    finally:
        store.close()
