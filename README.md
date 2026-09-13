# Tiger SigLIP + Qdrant Object Recognition

A lightweight image-recognition API built with **SigLIP**, **Qdrant Local Mode**, and **FastAPI**.

The project treats each first-level folder under `rawpics/` as a class/object ID, embeds every reference image with SigLIP, stores normalized vectors in Qdrant, and recognizes new images with cosine similarity search.

## Architecture

```text
Reference images
rawpics/<class_name>/*
        |
        v
      SigLIP
        |
        v
L2-normalized 768-d vectors
        |
        v
Qdrant Local Mode
        |
        v
FastAPI /api/v1/recognize
```

## Features

- `google/siglip-base-patch16-224`
- GPU auto-detection with CPU fallback
- Persistent Qdrant Local Mode
- Batch indexing from `rawpics/`
- Class/object IDs derived from folder names
- Top-K candidate search
- `MATCH`, `LOW_SIMILARITY`, `AMBIGUOUS`, and `EMPTY_INDEX` decisions
- Swagger/OpenAPI UI through FastAPI
- Windows PowerShell helper scripts

## Requirements

- Python 3.11+
- Windows PowerShell for the included helper scripts
- Optional NVIDIA GPU with a compatible PyTorch/CUDA installation

## Quick start

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If you already have a compatible virtual environment, activate that instead.

### 2. Install dependencies

```powershell
.\scripts\setup.ps1
```

### 3. Add reference images

```text
rawpics\
  tiger\
    tiger_01.jpg
    tiger_02.jpg
  eagle\
    eagle_01.jpg
    eagle_02.jpg
```

The first folder below `rawpics` becomes the class/object ID. Folder names are normalized to lowercase snake_case.

A flat naming convention is also supported:

```text
rawpics\tiger__01.jpg
rawpics\tiger__02.jpg
```

### 4. Validate the dataset

```powershell
.\scripts\validate_rawpics.ps1
```

### 5. Build or rebuild the Qdrant index

Stop the API first, then run:

```powershell
.\scripts\build_index.ps1
```

The first run downloads the SigLIP model into `models/hf_cache/`.

### 6. Check index status

```powershell
.\scripts\status.ps1
```

### 7. Start the API

```powershell
.\scripts\start.ps1
```

Swagger UI:

```text
http://127.0.0.1:18080/docs
```

## API

- `GET /health`
- `GET /api/v1/index/status`
- `POST /api/v1/recognize`

Example:

```bash
curl -X POST "http://127.0.0.1:18080/api/v1/recognize?top_k=5" \
  -H "accept: application/json" \
  -F "file=@test.jpg;type=image/jpeg"
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

Important settings:

```env
SIGLIP_MODEL_ID=google/siglip-base-patch16-224
SIGLIP_DEVICE=auto
QDRANT_COLLECTION=object_images
MATCH_THRESHOLD=0.80
AMBIGUITY_MARGIN=0.03
INDEX_BATCH_SIZE=16
```

`MATCH_THRESHOLD` and `AMBIGUITY_MARGIN` are application-specific and should be calibrated using positive and unknown/negative test images. A SigLIP cosine score is a similarity value, not a probability.

## Data and generated files

The public repository intentionally does **not** track:

- `.env`
- `rawpics/` image datasets
- `data/qdrant/`
- `data/index_manifest.json`
- `models/hf_cache/`
- virtual environments

This keeps the repository small, avoids committing local configuration, and prevents accidental publication of datasets or model caches.

## Current scope

This implementation works best as **semantic/category image recognition** against known reference classes. Distinguishing a specific person's identity from visually similar people is a different problem and may require a face/identity embedding model rather than general SigLIP embeddings.

## License

No license has been selected yet. Public visibility on GitHub does not automatically grant reuse rights. Add a license if you want others to copy, modify, or redistribute the project.
