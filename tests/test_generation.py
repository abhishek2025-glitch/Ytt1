import pytest
from src.generation import ContentGenerator, TemplateEngine

def test_content_generator_init():
    generator = ContentGenerator()
    assert generator is not None

def test_template_engine_init():
    engine = TemplateEngine()
    assert engine is not None
    assert len(engine.hook_templates) > 0

def test_generate_hooks():
    engine = TemplateEngine()
    topic = {"title": "AI automation trends", "id": "test_1"}
    hooks = engine.generate_hooks(topic)
    assert len(hooks) == 3
    assert all(isinstance(h, str) for h in hooks)

def test_generate_content():
    generator = ContentGenerator()
    topic = {
        "id": "test_1",
        "title": "AI market impact",
        "niche": "ai_tech",
        "narrative_lane": "ai_power",
        "format": "short",
        "final_score": 85
    }
    result = generator.generate_content(topic)
    assert "video_id" in result
    assert "hooks" in result
    assert "edg" in result
    assert "metadata" in result
    assert len(result["hooks"]) >= 3

def test_generate_edg():
    generator = ContentGenerator()
    topic = {
        "id": "test_1",
        "title": "Test topic",
        "format": "short",
        "niche": "general"
    }
    hooks = ["Test hook"]
    edg = generator._generate_short_edg(topic, hooks)
    assert edg["format"] == "short"
    assert edg["aspect_ratio"] == "9:16"
    assert len(edg["scenes"]) > 0
