import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
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
        
        # 1. Generate Hooks
        hooks = self._generate_hooks(topic)
        
        # 2. Generate Script
        script = self._generate_script(topic, hooks)
        
        # 3. Generate EDG (Scene breakdown)
        edg = self._generate_edg(topic, hooks, script)
        
        # 4. Generate Metadata
        metadata = self._generate_metadata(topic, hooks)
        
        result = {
            "video_id": self._generate_video_id(topic),
            "topic": topic,
            "hooks": hooks,
            "script": script,
            "edg": edg,
            "metadata": metadata,
            "status": "pending_approval" # As per requirement for human gate
        }
        
        logger.info("Content generation complete", video_id=result["video_id"])
        return result
    
    def _generate_hooks(self, topic: Dict) -> List[str]:
        title = topic.get("title", "")
        niche = topic.get("niche", "finance")
        
        llm_prompt = f"""Generate 3 compelling hooks for a {niche} video about: "{title}"

Requirements:
- Each hook should be 8-12 words
- Start with an attention-grabbing phrase
- Be analytical and data-driven, not sensational
- Format as a JSON array of strings
- Tone: Serious, curious, or warning

Templates to consider adapting:
- "You probably don't know..."
- "This is counterintuitive..."
- "The data shows something unexpected..."
- "Everyone is looking at X, but Y is the real story..."

Example: ["Here's what the data actually shows about inflation", "Three patterns most investors are missing today", "The numbers tell a different story about the recession"]"""
        
        system_prompt = "You are a top-tier finance content strategist. Optimized for CTR and retention."
        
        llm_result = self.llm_client.generate(llm_prompt, system_prompt)
        
        if llm_result:
            try:
                # Clean up potential markdown formatting
                cleaned = llm_result.replace("```json", "").replace("```", "").strip()
                hooks = json.loads(cleaned)
                if isinstance(hooks, list) and len(hooks) >= 3:
                    logger.info("LLM hooks generated", count=len(hooks))
                    return hooks[:3]
            except Exception as e:
                logger.warning("Failed to parse LLM hooks, using fallback", error=str(e))
        
        return self.template_engine.generate_hooks(topic)
    
    def _generate_script(self, topic: Dict, hooks: List[str]) -> str:
        title = topic.get("title", "")
        format_type = topic.get("format", "short")
        hook = hooks[0] if hooks else title
        lane = topic.get("narrative_lane", "general")
        
        # Determine Tone
        tone = "Serious analyst" # Default
        if lane in ["investing_psychology", "crypto_blockchain"]:
            tone = "Casual educator"
        elif lane in ["hidden_data", "contrarian"]:
            tone = "Data nerd"
            
        prompt = f"""Write a full script for a YouTube {format_type} video about: "{title}"

Tone: {tone}
Hook: "{hook}"
Structure: Problem -> Data -> Solution -> CTA

Requirements:
- Pattern interrupts every 5-10 seconds (mark with [VISUAL CHANGE])
- Total duration: {'30-50 seconds' if format_type == 'short' else '6-8 minutes'}
- Include timing markers like [0:00], [0:15]
- Ending CTA: "Subscribe for more insights"
- No sensationalism without attribution
- Focus on facts, data, and clear analysis

Output the script directly."""

        system_prompt = f"You are an expert scriptwriter for a finance channel. Tone: {tone}."
        
        script = self.llm_client.generate(prompt, system_prompt)
        
        if script:
            return script
        else:
            return self.template_engine.generate_script(topic, format_type)
            
    def _generate_edg(self, topic: Dict, hooks: List[str], script: str) -> Dict:
        format_type = topic.get("format", "short")
        
        # In a real system, we might parse the script to build the EDG scenes.
        # For now, we'll stick to a structured template but inject the script/hooks.
        
        if format_type == "short":
            return self._generate_short_edg(topic, hooks, script)
        else:
            return self._generate_long_edg(topic, hooks, script)
    
    def _generate_short_edg(self, topic: Dict, hooks: List[str], script: str) -> Dict:
        title = topic.get("title", "Unknown Topic")
        hook = hooks[0] if hooks else "Here's what you need to know"
        
        edg = {
            "video_id": self._generate_video_id(topic),
            "format": "short",
            "duration_seconds": 45, # Est
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "id": "scene_1",
                    "type": "intro",
                    "start": 0.0,
                    "end": 3.0,
                    "visual": "abstract_motion",
                    "source_hint": "pexels:money finance",
                    "text_overlay": hook,
                    "tts_text": hook,
                    "cut_type": "hard",
                },
                {
                    "id": "scene_2",
                    "type": "main",
                    "start": 3.0,
                    "end": 15.0,
                    "visual": "data_visualization",
                    "source_hint": "pexels:stock chart",
                    "text_overlay": title,
                    "tts_text": script[:100] + "...", # Placeholder, normally full segment
                    "cut_type": "fade",
                },
                {
                    "id": "scene_3",
                    "type": "data",
                    "start": 15.0,
                    "end": 35.0,
                    "visual": "supporting_footage",
                    "source_hint": "pexels:business office",
                    "text_overlay": "Key Insight",
                    "tts_text": "...", # Placeholder
                    "cut_type": "fade",
                },
                {
                    "id": "scene_4",
                    "type": "conclusion",
                    "start": 35.0,
                    "end": 45.0,
                    "visual": "call_to_action",
                    "source_hint": "abstract:gradient",
                    "text_overlay": "Subscribe",
                    "tts_text": "Subscribe for more insights.",
                    "cut_type": "hard",
                },
            ],
            "thumbnail_frame_hint": 3.5,
            "metadata": {
                "tone": "analytical",
                "script_full": script
            }
        }
        
        return edg
    
    def _generate_long_edg(self, topic: Dict, hooks: List[str], script: str) -> Dict:
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
                # Detailed scenes would be generated by parsing the script
            ],
            "thumbnail_frame_hint": 5.0,
            "metadata": {
                "script_full": script
            }
        }
        
        return edg
    
    def _generate_metadata(self, topic: Dict, hooks: List[str]) -> Dict:
        title = topic.get("title", "Untitled")
        niche = topic.get("niche", "general")
        
        # 2 Title variants per ticket
        titles = []
        if hooks:
            titles.append(f"{hooks[0]}") # Pattern: Hook as title
        
        titles.append(f"Why {title} Matters") # Fallback
        
        # Description with 150 char hook + timestamps + resources
        description = f"""{hooks[0] if hooks else title}

SUBSCRIBE for daily finance insights.

TIMESTAMPS:
0:00 Intro
1:00 The Data
3:00 The Solution
5:00 Conclusion

RESOURCES:
- Market Data: Yahoo Finance
- Analysis Tools: TradingView

#finance #investing #{niche} #stockmarket
"""
        
        tags = [
            "finance", "investing", "stock market", "economy", "wealth",
            "passive income", "money", "crypto", "trading", "business",
            topic.get("narrative_lane", "finance"),
            title.split()[0], # First word of title
        ]
        
        metadata = {
            "titles": titles[:2],
            "description": description,
            "tags": tags[:20],
        }
        
        return metadata
    
    def _generate_video_id(self, topic: Dict) -> str:
        content = f"{topic.get('title', '')}_{topic.get('id', '')}"
        hash_digest = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"vid_{hash_digest}"
