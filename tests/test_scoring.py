import pytest
from src.scoring import VPSScorer

def test_scorer_init():
    scorer = VPSScorer()
    assert scorer is not None
    assert sum(scorer.weights.values()) == pytest.approx(1.0, 0.01)

def test_score_single():
    scorer = VPSScorer()
    candidate = {
        "id": "test_1",
        "title": "AI investment opportunities",
        "description": "Finance meets technology",
        "origin_count": 3,
        "emotional_vector": "curiosity",
        "explainability_seconds": 45,
    }
    result = scorer.score_single(candidate)
    assert "base_vps" in result
    assert "niche" in result
    assert "final_score" in result
    assert 0 <= result["base_vps"] <= 100

def test_niche_detection():
    scorer = VPSScorer()
    candidate = {
        "id": "1",
        "title": "Cryptocurrency market analysis",
        "description": "Bitcoin and Ethereum trends"
    }
    result = scorer.score_single(candidate)
    assert result["niche"] == "crypto"

def test_score_batch():
    scorer = VPSScorer()
    candidates = [
        {"id": "1", "title": "AI news", "emotional_vector": "surprise"},
        {"id": "2", "title": "Finance update", "emotional_vector": "concern"},
    ]
    results = scorer.score_batch(candidates)
    assert len(results) == 2
    assert results[0]["final_score"] >= results[1]["final_score"]  # Sorted
