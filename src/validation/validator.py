from typing import List, Dict, Optional
from ..shared import get_logger

logger = get_logger(__name__)

class TrendValidator:
    def __init__(self):
        self.base_rules = {
            "min_source_count": 2,
            "max_explainability_seconds": 60,
            "min_relevance": 0.5,
            "valid_emotions": ["surprise", "concern", "curiosity", "awe"],
        }
        self.relaxed_rules = self.base_rules.copy()
        logger.info("TrendValidator initialized")
    
    def validate_batch(self, candidates: List[Dict]) -> List[Dict]:
        validated = []
        
        for candidate in candidates:
            result = self.validate_single(candidate)
            validated.append(result)
        
        pass_count = sum(1 for v in validated if v["passed"])
        pass_rate = pass_count / len(validated) if validated else 0
        
        logger.info(
            "Validation batch complete",
            total=len(validated),
            passed=pass_count,
            pass_rate=round(pass_rate, 2)
        )
        
        if pass_rate < 0.4:
            logger.warning("Low pass rate, consider relaxing rules", pass_rate=pass_rate)
        
        return validated
    
    def validate_single(self, candidate: Dict) -> Dict:
        result = candidate.copy()
        result["passed"] = True
        result["validation_notes"] = []
        
        source_count = candidate.get("origin_count", 1)
        if source_count < self.base_rules["min_source_count"]:
            result["passed"] = False
            result["validation_notes"].append(f"Insufficient sources: {source_count}")
        
        explainability = self._estimate_explainability(candidate)
        result["explainability_seconds"] = explainability
        if explainability > self.base_rules["max_explainability_seconds"]:
            result["passed"] = False
            result["validation_notes"].append(f"Too complex: {explainability}s")
        
        emotion = self._detect_emotion(candidate)
        result["emotional_vector"] = emotion
        if emotion not in self.base_rules["valid_emotions"]:
            result["validation_notes"].append(f"Weak emotion: {emotion}")
        
        relevance = self._calculate_relevance(candidate)
        result["relevance"] = relevance
        if relevance < self.base_rules["min_relevance"]:
            result["passed"] = False
            result["validation_notes"].append(f"Low relevance: {relevance}")
        
        result["id"] = f"validated_{candidate.get('id', 'unknown')}"
        result["trend_id"] = candidate.get("id")
        
        return result
    
    def _estimate_explainability(self, candidate: Dict) -> int:
        title = candidate.get("title", "")
        description = candidate.get("description", "")
        
        word_count = len(title.split()) + len(description.split())
        
        if word_count < 10:
            return 30
        elif word_count < 20:
            return 45
        elif word_count < 40:
            return 60
        else:
            return 90
    
    def _detect_emotion(self, candidate: Dict) -> str:
        title_lower = candidate.get("title", "").lower()
        desc_lower = candidate.get("description", "").lower()
        combined = f"{title_lower} {desc_lower}"
        
        emotion_keywords = {
            "surprise": ["unexpected", "shocking", "surprising", "sudden", "breakthrough"],
            "concern": ["warning", "crisis", "risk", "threat", "danger", "concern"],
            "curiosity": ["why", "how", "what", "secret", "hidden", "revealed"],
            "awe": ["revolutionary", "incredible", "amazing", "unprecedented", "historic"],
        }
        
        scores = {}
        for emotion, keywords in emotion_keywords.items():
            scores[emotion] = sum(1 for kw in keywords if kw in combined)
        
        if max(scores.values()) == 0:
            return "neutral"
        
        return max(scores, key=scores.get)
    
    def _calculate_relevance(self, candidate: Dict) -> float:
        high_value_keywords = [
            "ai", "market", "economy", "investment", "business", "technology",
            "automation", "data", "strategy", "growth", "money", "crypto"
        ]
        
        combined = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        
        matches = sum(1 for kw in high_value_keywords if kw in combined)
        
        relevance = min(matches / 3.0, 1.0)
        
        if candidate.get("origin_count", 1) >= 3:
            relevance = min(relevance + 0.2, 1.0)
        
        return round(relevance, 2)
    
    def relax_rules(self):
        self.relaxed_rules["max_explainability_seconds"] = 90
        self.relaxed_rules["min_relevance"] = 0.3
        logger.info("Validation rules relaxed", rules=self.relaxed_rules)
