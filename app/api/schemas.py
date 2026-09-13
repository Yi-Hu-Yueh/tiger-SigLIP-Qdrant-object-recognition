from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Candidate(BaseModel):
    object_id: str
    object_name: str
    score: float
    reference_path: str | None = None
    file_name: str | None = None
    point_id: str


class RecognitionResponse(BaseModel):
    recognized: bool
    decision: Literal["MATCH", "LOW_SIMILARITY", "AMBIGUOUS", "EMPTY_INDEX"]
    object_id: str | None = None
    object_name: str | None = None
    score: float | None = None
    candidates: list[Candidate] = Field(default_factory=list)


class IndexStatus(BaseModel):
    ready: bool
    collection_exists: bool
    vector_count: int
    collection_name: str
    qdrant_path: str
    model_id: str
    model_loaded: bool
