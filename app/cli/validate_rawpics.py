from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image

from app.config import settings
from app.services.indexing import discover_images, make_record, validate_image


def main() -> None:
    paths = discover_images(settings.rawpics_dir)
    if not paths:
        raise SystemExit(f"No images found under: {settings.rawpics_dir}")

    class_counts: Counter[str] = Counter()
    ext_counts: Counter[str] = Counter()
    size_counts: Counter[str] = Counter()
    invalid: list[dict[str, str]] = []

    for path in paths:
        error = validate_image(path)
        if error:
            invalid.append({"file": str(path.relative_to(settings.rawpics_dir)), "error": error})
            continue
        record = make_record(path, settings.rawpics_dir)
        class_counts[record.object_id] += 1
        ext_counts[path.suffix.lower()] += 1
        with Image.open(path) as image:
            size_counts[f"{image.width}x{image.height}"] += 1

    report = {
        "rawpics": str(settings.rawpics_dir),
        "valid_images": sum(class_counts.values()),
        "invalid_images": len(invalid),
        "class_count": len(class_counts),
        "classes": dict(sorted(class_counts.items())),
        "extensions": dict(sorted(ext_counts.items())),
        "sizes": dict(size_counts.most_common()),
        "invalid": invalid,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if invalid:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
