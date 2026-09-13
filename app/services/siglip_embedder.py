from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Iterable

from PIL import Image


class SiglipEmbedder:
    """Lazy-loading SigLIP vision encoder with L2-normalized embeddings."""

    def __init__(self, model_id: str, cache_dir: Path, device: str = "auto") -> None:
        self.model_id = model_id
        self.cache_dir = Path(cache_dir)
        self.requested_device = device
        self._processor = None
        self._model = None
        self._torch = None
        self._device = None
        self._lock = Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str:
        self._ensure_loaded()
        return str(self._device)

    @property
    def dimension(self) -> int:
        self._ensure_loaded()
        return int(self._model.config.hidden_size)

    def _resolve_device(self, torch):
        requested = self.requested_device.strip().lower()
        if requested == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if requested == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("SIGLIP_DEVICE=cuda but CUDA is not available in this PyTorch environment.")
        return torch.device(requested)

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return

            import torch
            import torch.nn.functional as F  # noqa: F401  (validated at load time)
            from transformers import AutoImageProcessor, SiglipVisionModel

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            device = self._resolve_device(torch)

            processor = AutoImageProcessor.from_pretrained(
                self.model_id,
                cache_dir=str(self.cache_dir),
            )
            model = SiglipVisionModel.from_pretrained(
                self.model_id,
                cache_dir=str(self.cache_dir),
            )
            model.eval()
            model.to(device)

            self._torch = torch
            self._processor = processor
            self._model = model
            self._device = device

    @staticmethod
    def _load_rgb(path: Path) -> Image.Image:
        with Image.open(path) as image:
            return image.convert("RGB")

    def embed_image(self, image: Image.Image) -> list[float]:
        return self.embed_images([image])[0]

    def embed_path(self, path: Path) -> list[float]:
        return self.embed_paths([path])[0]

    def embed_paths(self, paths: Iterable[Path]) -> list[list[float]]:
        images = [self._load_rgb(Path(path)) for path in paths]
        return self.embed_images(images)

    def embed_images(self, images: list[Image.Image]) -> list[list[float]]:
        if not images:
            return []
        self._ensure_loaded()
        torch = self._torch
        import torch.nn.functional as F

        prepared = [image.convert("RGB") for image in images]
        inputs = self._processor(images=prepared, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self._device)

        with torch.inference_mode():
            outputs = self._model(pixel_values=pixel_values)
            embeddings = outputs.pooler_output
            embeddings = F.normalize(embeddings, p=2, dim=-1)

        return embeddings.detach().cpu().float().tolist()
