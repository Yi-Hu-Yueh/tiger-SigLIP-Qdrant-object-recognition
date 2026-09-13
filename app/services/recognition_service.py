from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app.config import Settings
from app.services.qdrant_store import QdrantStore
from app.services.siglip_embedder import SiglipEmbedder


@dataclass(frozen=True)
class RecognitionDecision:
    recognized: bool
    decision: str
    object_id: str | None
    object_name: str | None
    score: float | None
    candidates: list[dict]


class RecognitionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder = SiglipEmbedder(
            model_id=settings.model_id,
            cache_dir=settings.model_cache_dir,
            device=settings.device,
        )
        self.store = QdrantStore(settings.qdrant_path, settings.collection_name)

    def close(self) -> None:
        self.store.close()

    def status(self) -> dict:
        exists = self.store.collection_exists()
        return {
            "ready": exists and self.store.count() > 0,
            "collection_exists": exists,
            "vector_count": self.store.count() if exists else 0,
            "collection_name": self.settings.collection_name,
            "qdrant_path": str(self.settings.qdrant_path),
            "model_id": self.settings.model_id,
            "model_loaded": self.embedder.loaded,
        }

    @staticmethod
    def _group_candidates(points, top_k: int) -> list[dict]:
        best_by_object: dict[str, dict] = {}
        for point in points:
            payload = point.payload or {}
            object_id = str(payload.get("object_id", point.id))
            candidate = {
                "object_id": object_id,
                "object_name": str(payload.get("object_name", object_id)),
                "score": float(point.score),
                "reference_path": payload.get("relative_path"),
                "file_name": payload.get("file_name"),
                "point_id": str(point.id),
            }
            previous = best_by_object.get(object_id)
            if previous is None or candidate["score"] > previous["score"]:
                best_by_object[object_id] = candidate

        candidates = sorted(
            best_by_object.values(),
            key=lambda item: item["score"],
            reverse=True,
        )
        return candidates[:top_k]

    @staticmethod
    def decide(candidates: list[dict], threshold: float, ambiguity_margin: float) -> RecognitionDecision:
        if not candidates:
            return RecognitionDecision(False, "EMPTY_INDEX", None, None, None, [])

        first = candidates[0]
        score = float(first["score"])
        if score < threshold:
            return RecognitionDecision(
                False,
                "LOW_SIMILARITY",
                first["object_id"],
                first["object_name"],
                score,
                candidates,
            )

        if len(candidates) > 1:
            margin = score - float(candidates[1]["score"])
            if margin < ambiguity_margin:
                return RecognitionDecision(
                    False,
                    "AMBIGUOUS",
                    first["object_id"],
                    first["object_name"],
                    score,
                    candidates,
                )

        return RecognitionDecision(
            True,
            "MATCH",
            first["object_id"],
            first["object_name"],
            score,
            candidates,
        )

    def recognize(
        self,
        image: Image.Image,
        top_k: int,
        threshold: float | None = None,
        ambiguity_margin: float | None = None,
    ) -> RecognitionDecision:
        if not self.store.collection_exists() or self.store.count() == 0:
            return self.decide([], threshold or self.settings.match_threshold, self.settings.ambiguity_margin)

        threshold = self.settings.match_threshold if threshold is None else threshold
        ambiguity_margin = (
            self.settings.ambiguity_margin if ambiguity_margin is None else ambiguity_margin
        )
        vector = self.embedder.embed_image(image)
        reference_limit = max(
            top_k,
            top_k * max(1, self.settings.query_reference_multiplier),
        )
        points = self.store.query(vector, limit=reference_limit)
        candidates = self._group_candidates(points, top_k=top_k)
        return self.decide(candidates, threshold, ambiguity_margin)
