from app.services.recognition_service import RecognitionService


def candidate(object_id: str, score: float):
    return {
        "object_id": object_id,
        "object_name": object_id,
        "score": score,
        "reference_path": None,
        "file_name": None,
        "point_id": object_id,
    }


def test_match():
    result = RecognitionService.decide(
        [candidate("A", 0.90), candidate("B", 0.70)],
        threshold=0.80,
        ambiguity_margin=0.03,
    )
    assert result.recognized is True
    assert result.decision == "MATCH"
    assert result.object_id == "A"


def test_low_similarity():
    result = RecognitionService.decide(
        [candidate("A", 0.70)], threshold=0.80, ambiguity_margin=0.03
    )
    assert result.recognized is False
    assert result.decision == "LOW_SIMILARITY"


def test_ambiguous():
    result = RecognitionService.decide(
        [candidate("A", 0.90), candidate("B", 0.88)],
        threshold=0.80,
        ambiguity_margin=0.03,
    )
    assert result.recognized is False
    assert result.decision == "AMBIGUOUS"
