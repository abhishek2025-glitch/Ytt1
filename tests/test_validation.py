import pytest
from src.validation import TrendValidator

def test_validator_init():
    validator = TrendValidator()
    assert validator is not None
    assert validator.base_rules["min_source_count"] == 2

def test_validate_single():
    validator = TrendValidator()
    candidate = {
        "id": "test_1",
        "title": "AI transforms business operations",
        "description": "New study shows AI impact",
        "origin_count": 2
    }
    result = validator.validate_single(candidate)
    assert "passed" in result
    assert "explainability_seconds" in result
    assert "emotional_vector" in result
    assert "relevance" in result

def test_validate_batch():
    validator = TrendValidator()
    candidates = [
        {"id": "1", "title": "AI news", "origin_count": 2},
        {"id": "2", "title": "Market update", "origin_count": 1},
    ]
    results = validator.validate_batch(candidates)
    assert len(results) == 2

def test_emotion_detection():
    validator = TrendValidator()
    candidate = {"title": "Surprising breakthrough in AI", "description": ""}
    result = validator.validate_single(candidate)
    assert result["emotional_vector"] in ["surprise", "curiosity", "awe", "concern", "neutral"]
