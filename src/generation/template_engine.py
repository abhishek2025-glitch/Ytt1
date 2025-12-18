from typing import Dict, List
from ..shared import get_logger

logger = get_logger(__name__)

class TemplateEngine:
    def __init__(self):
        self.hook_templates = [
            "Here's what the data actually shows about {topic}",
            "Three patterns emerging in {topic}",
            "The numbers behind {topic}",
            "What most miss about {topic}",
            "The reality of {topic}",
        ]
        logger.info("TemplateEngine initialized")
    
    def generate_hooks(self, topic: Dict) -> List[str]:
        title = topic.get("title", "this topic")
        
        hooks = [
            f"Here's what the data shows about {title[:30]}",
            f"Three things to know about {title[:30]}",
            f"The reality behind {title[:30]}",
        ]
        
        logger.info("Template hooks generated", count=len(hooks))
        return hooks
    
    def generate_script(self, topic: Dict, format_type: str = "short") -> str:
        title = topic.get("title", "Unknown")
        
        if format_type == "short":
            script = f"""
HOOK: Let's talk about {title}.

MAIN: The data shows some interesting patterns here.

KEY POINT: This is what actually matters.

CONCLUSION: That's the analysis.
"""
        else:
            script = f"""
INTRODUCTION: Today we're analyzing {title} in depth.

[Section continues with detailed analysis]

CONCLUSION: Those are the key takeaways.
"""
        
        return script.strip()
