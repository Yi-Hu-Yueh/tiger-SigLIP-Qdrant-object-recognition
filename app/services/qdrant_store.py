from __future__ import annotations

from pathlib import Path
from typing import Iterable

from qdrant_client import QdrantClient, models


class QdrantStore:
    """Persistent Qdrant Local Mode store."""

    def __init__(self, path: Path, collection_name: str) -> None:
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = QdrantClient(path=str(self.path))

    def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            close()

    def collection_exists(self) -> bool:
        return bool(self.client.collection_exists(self.collection_name))

    def rebuild_collection(self, vector_size: int) -> None:
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert(self, points: Iterable[models.PointStruct]) -> None:
        points = list(points)
        if not points:
            return
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def query(self, vector: list[float], limit: int):
        if not self.collection_exists():
            return []
        return self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        ).points

    def count(self) -> int:
        if not self.collection_exists():
            return 0
        return int(
            self.client.count(
                collection_name=self.collection_name,
                exact=True,
            ).count
        )
