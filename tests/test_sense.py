import pytest
from src.sense import TrendAggregator, SemanticDeduplicator

def test_trend_aggregator_init():
    aggregator = TrendAggregator()
    assert aggregator is not None
    assert len(aggregator.sources) > 0

def test_evergreen_topics():
    aggregator = TrendAggregator()
    assert len(aggregator.evergreen_topics) > 0
    assert all("title" in t for t in aggregator.evergreen_topics)

def test_deduplicator_init():
    dedup = SemanticDeduplicator()
    assert dedup is not None
    assert dedup.similarity_threshold == 0.75

def test_deduplicator_empty_list():
    dedup = SemanticDeduplicator()
    result = dedup.deduplicate([])
    assert result == []

def test_deduplicator_single_item():
    dedup = SemanticDeduplicator()
    trends = [{"title": "Test", "description": "Test description"}]
    result = dedup.deduplicate(trends)
    assert len(result) == 1

def test_merge_origins():
    dedup = SemanticDeduplicator()
    trends = [
        {"title": "Test", "source": "reddit"},
        {"title": "Test", "source": "hackernews"},
    ]
    result = dedup.merge_origins(trends)
    assert len(result) == 1
    assert result[0]["origin_count"] == 2
