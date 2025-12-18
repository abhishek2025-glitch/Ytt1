import json
from pathlib import Path
from typing import Dict, List, Tuple
from ..shared import get_logger

logger = get_logger(__name__)

class SafetyChecker:
    def __init__(self):
        self.safety_config = self._load_safety_config()
        self.hard_blocklist = self._extract_keywords(self.safety_config.get("hard_blocklist", {}))
        self.soft_blacklist = self._extract_keywords(self.safety_config.get("soft_blacklist", {}))
        
        logger.info("SafetyChecker initialized", hard_rules=len(self.hard_blocklist), soft_rules=len(self.soft_blacklist))
    
    def _load_safety_config(self) -> Dict:
        config_path = Path("config/safety_rules.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _extract_keywords(self, blocklist_config: Dict) -> List[str]:
        keywords = []
        for category in blocklist_config.get("categories", []):
            keywords.extend(category.get("keywords", []))
        return keywords
    
    def check_content(self, content: Dict) -> Tuple[bool, List[str]]:
        violations = []
        
        title = content.get("title", "").lower()
        description = content.get("description", "").lower()
        combined = f"{title} {description}"
        
        for keyword in self.hard_blocklist:
            if keyword.lower() in combined:
                violations.append(f"hard_violation: {keyword}")
        
        if violations:
            logger.warning("Hard violations detected", count=len(violations), video_id=content.get("video_id"))
            return False, violations
        
        for keyword in self.soft_blacklist:
            if keyword.lower() in combined:
                violations.append(f"soft_violation: {keyword}")
        
        if violations:
            logger.info("Soft violations detected", count=len(violations), video_id=content.get("video_id"))
        
        return True, violations
    
    def batch_check(self, contents: List[Dict]) -> List[Dict]:
        results = []
        
        for content in contents:
            passed, violations = self.check_content(content)
            
            results.append({
                "video_id": content.get("video_id"),
                "passed": passed,
                "violations": violations,
                "action": "suppress" if not passed else ("add_attribution" if violations else "approve"),
            })
        
        total_violations = sum(1 for r in results if not r["passed"])
        logger.info("Batch safety check complete", total=len(results), violations=total_violations)
        
        return results
