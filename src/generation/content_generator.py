import json
import hashlib
from typing import Dict, List
from .llm_client import LLMClient
from .template_engine import TemplateEngine
from ..shared import get_logger

logger = get_logger(__name__)

class ContentGenerator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.template_engine = TemplateEngine()
        logger.info("ContentGenerator initialized")
    
    def generate_content(self, topic: Dict) -> Dict:
        title = topic.get("title", "")
        niche = topic.get("niche", "general")
        lane = topic.get("narrative_lane", "hidden_data")
        format_type = topic.get("format", "short")
        
        logger.info(
            "Generating content",
            title=title[:50],
            niche=niche,
            lane=lane,
            format=format_type
        )
        
        hooks = self._generate_hooks(topic)
        
        edg = self._generate_edg(topic, hooks)
        
        metadata = self._generate_metadata(topic, hooks)
        
        result = {
            "video_id": self._generate_video_id(topic),
            "topic": topic,
            "hooks": hooks,
            "edg": edg,
            "metadata": metadata,
        }
        
        logger.info("Content generation complete", video_id=result["video_id"])
        return result
    
    def _generate_hooks(self, topic: Dict) -> List[str]:
        title = topic.get("title", "")
        
        llm_prompt = f"""Generate 3 compelling hooks for a video about: "{title}"

Requirements:
- Each hook should be 8-12 words
- Start with an attention-grabbing phrase
- Be analytical and data-driven, not sensational
- Format as a JSON array of strings

Example: ["Here's what the data actually shows", "Three patterns most people miss", "The numbers tell a different story"]"""
        
        system_prompt = "You are a cold, analytical content strategist. No hype, only sourced insights."
        
        llm_result = self.llm_client.generate(llm_prompt, system_prompt)
        
        if llm_result:
            try:
                hooks = json.loads(llm_result)
                if isinstance(hooks, list) and len(hooks) >= 3:
                    logger.info("LLM hooks generated", count=len(hooks))
                    return hooks[:3]
            except:
                logger.warning("Failed to parse LLM hooks, using fallback")
        
        return self.template_engine.generate_hooks(topic)
    
    def _generate_edg(self, topic: Dict, hooks: List[str]) -> Dict:
        format_type = topic.get("format", "short")
        
        if format_type == "short":
            return self._generate_short_edg(topic, hooks)
        else:
            return self._generate_long_edg(topic, hooks)
    
    def _generate_short_edg(self, topic: Dict, hooks: List[str]) -> Dict:
        title = topic.get("title", "Unknown Topic")
        hook = hooks[0] if hooks else "Here's what you need to know"
        
        edg = {
            "video_id": self._generate_video_id(topic),
            "format": "short",
            "duration_seconds": 28,
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "id": "scene_1",
                    "type": "intro",
                    "start": 0.0,
                    "end": 3.0,
                    "visual": "abstract_motion",
                    "source_hint": "pexels:technology abstract",
                    "text_overlay": hook,
                    "tts_text": hook,
                    "cut_type": "hard",
                },
                {
                    "id": "scene_2",
                    "type": "main",
                    "start": 3.0,
                    "end": 12.0,
                    "visual": "data_visualization",
                    "source_hint": "pexels:data analytics",
                    "text_overlay": title,
                    "tts_text": f"Let's break down {title}",
                    "cut_type": "fade",
                },
                {
                    "id": "scene_3",
                    "type": "data",
                    "start": 12.0,
                    "end": 22.0,
                    "visual": "supporting_footage",
                    "source_hint": "pexels:business meeting",
                    "text_overlay": "Key insight",
                    "tts_text": "The data shows a clear pattern here",
                    "cut_type": "fade",
                },
                {
                    "id": "scene_4",
                    "type": "conclusion",
                    "start": 22.0,
                    "end": 28.0,
                    "visual": "call_to_action",
                    "source_hint": "abstract:gradient",
                    "text_overlay": "Follow for more insights",
                    "tts_text": "That's the reality",
                    "cut_type": "hard",
                },
            ],
            "thumbnail_frame_hint": 3.5,
            "metadata": {
                "tone": "analytical",
                "persona": "cold_skeptic",
            }
        }
        
        logger.info("Short EDG generated", duration=edg["duration_seconds"])
        return edg
    
    def _generate_long_edg(self, topic: Dict, hooks: List[str]) -> Dict:
        edg = {
            "video_id": self._generate_video_id(topic),
            "format": "long",
            "duration_seconds": 440,
            "aspect_ratio": "16:9",
            "scenes": [
                {
                    "id": "scene_intro",
                    "type": "intro",
                    "start": 0.0,
                    "end": 15.0,
                    "visual": "intro_sequence",
                    "text_overlay": hooks[0] if hooks else "Deep dive analysis",
                    "tts_text": hooks[0] if hooks else "Let's analyze this in detail",
                },
            ],
            "thumbnail_frame_hint": 5.0,
        }
        
        logger.info("Long EDG generated", duration=edg["duration_seconds"])
        return edg
    
    def _generate_metadata(self, topic: Dict, hooks: List[str]) -> Dict:
        title = topic.get("title", "Untitled")
        niche = topic.get("niche", "general")
        
        metadata = {
            "titles": [
                f"{title}",
                f"{hooks[0] if hooks else title}",
            ],
            "description": f"{hooks[0] if hooks else ''}\n\nAnalysis of {title}.\n\nSubscribe for data-driven insights.\n\n#analysis #data #insights",
            "tags": [
                niche,
                "analysis",
                "data",
                "insights",
                "trending",
            ],
        }
        
        return metadata
    
    def _generate_video_id(self, topic: Dict) -> str:
        content = f"{topic.get('title', '')}_{topic.get('id', '')}"
        hash_digest = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"vid_{hash_digest}"
