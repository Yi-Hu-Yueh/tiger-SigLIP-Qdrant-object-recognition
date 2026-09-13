from __future__ import annotations

import json

from app.config import settings
from app.services.qdrant_store import QdrantStore


def main() -> int:
    store = QdrantStore(settings.qdrant_path, settings.collection_name)
    try:
        payload = {
            "collection_name": settings.collection_name,
            "collection_exists": store.collection_exists(),
            "vector_count": store.count(),
            "qdrant_path": str(settings.qdrant_path),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
