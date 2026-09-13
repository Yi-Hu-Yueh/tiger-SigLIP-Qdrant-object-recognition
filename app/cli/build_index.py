from __future__ import annotations

import json
import sys

from app.config import settings
from app.services.indexing import build_index


def main() -> int:
    print("Tiger SigLIP -> Qdrant index builder")
    print(f"Raw images : {settings.rawpics_dir}")
    print(f"Qdrant DB  : {settings.qdrant_path}")
    print(f"Model      : {settings.model_id}")
    print("IMPORTANT  : Stop the FastAPI server before rebuilding local Qdrant.\n")

    try:
        manifest = build_index(settings)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("\nIndex build completed.")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
