from typing import List, Dict, Optional
from ..shared import get_logger

logger = get_logger(__name__)

class TrendValidator:
    def __init__(self):
        self.base_rules = {
            "min_source_count": 2,
            "max_explainability_seconds": 60,
            "min_relevance": 0.5,
            "valid_emotions": ["surprise", "concern", "curiosity", "opportunity"],
        }
        self.active_rules = self.base_rules.copy()
        logger.info("TrendValidator initialized")
    
    def validate_batch(self, candidates: List[Dict]) -> List[Dict]:
        # Reset rules
        self.active_rules = self.base_rules.copy()
        
        # First pass
        validated = self._run_validation(candidates)
        pass_count = sum(1 for v in validated if v["passed"])
        pass_rate = pass_count / len(validated) if validated else 0
        
        logger.info(
            "Validation pass 1 complete",
            total=len(validated),
            passed=pass_count,
            pass_rate=round(pass_rate, 2)
        )
        
        # Adaptive relaxation if < 50% pass
        if pass_rate < 0.5:
            logger.warning("Low pass rate, relaxing rules for second pass", pass_rate=pass_rate)
            self._relax_rules()
            validated = self._run_validation(candidates)
            pass_count = sum(1 for v in validated if v["passed"])
            
            logger.info(
                "Validation pass 2 complete",
                passed=pass_count,
                pass_rate=round(pass_count / len(validated) if validated else 0, 2)
            )
            
        return validated
        
    def _run_validation(self, candidates: List[Dict]) -> List[Dict]:
        return [self.validate_single(c) for c in candidates]
    
    def _relax_rules(self):
        self.active_rules["max_explainability_seconds"] = 90
        self.active_rules["min_relevance"] = 0.3
        self.active_rules["min_source_count"] = 1 # Allow single source if needed
    
    def validate_single(self, candidate: Dict) -> Dict:
        result = candidate.copy()
        result["passed"] = True
        result["validation_notes"] = []
        
        # 1. Source Count
        source_count = candidate.get("origin_count", 1)
        if source_count < self.active_rules["min_source_count"]:
            result["passed"] = False
            result["validation_notes"].append(f"Insufficient sources: {source_count}")
        
        # 2. Explainability
        explainability = self._estimate_explainability(candidate)
        result["explainability_seconds"] = explainability
        if explainability > self.active_rules["max_explainability_seconds"]:
            result["passed"] = False
            result["validation_notes"].append(f"Too complex: {explainability}s")
        
        # 3. Emotion
        emotion = self._detect_emotion(candidate)
        result["emotional_vector"] = emotion
        if emotion not in self.active_rules["valid_emotions"]:
            # Check if we should fail or just note it. Ticket says "emotional_vector ∈ {set}"
            # I'll make it a soft requirement or strict? "Multi-check validation" implies strict.
            # But maybe relaxed?
            # Let's keep it strict but allow "neutral" if relaxed? No, stay strict for now.
            result["passed"] = False
            result["validation_notes"].append(f"Weak emotion: {emotion}")
        
        # 4. Relevance
        relevance = self._calculate_relevance(candidate)
        result["relevance"] = relevance
        if relevance < self.active_rules["min_relevance"]:
            result["passed"] = False
            result["validation_notes"].append(f"Low relevance: {relevance}")
            
        # 5. Financial Accuracy (Basic check)
        if not self._check_financial_accuracy(candidate):
            result["passed"] = False
            result["validation_notes"].append("Financial accuracy check failed")
        
        result["id"] = f"validated_{candidate.get('id', 'unknown')}"
        result["trend_id"] = candidate.get("id")
        
        return result
    
    def _estimate_explainability(self, candidate: Dict) -> int:
        title = candidate.get("title", "")
        description = candidate.get("description", "")
        word_count = len(title.split()) + len(description.split())
        
        # Rough heuristic
        if word_count < 15: return 30
        elif word_count < 30: return 45
        elif word_count < 60: return 60
        else: return 90
    
    def _detect_emotion(self, candidate: Dict) -> str:
        text = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        
        emotion_keywords = {
            "surprise": ["unexpected", "shocking", "surprising", "sudden", "breakthrough", "unknown"],
            "concern": ["warning", "crisis", "risk", "threat", "danger", "concern", "crash", "collapse", "recession"],
            "curiosity": ["why", "how", "what", "secret", "hidden", "revealed", "myth", "truth"],
            "opportunity": ["opportunity", "profit", "gain", "growth", "bull", "buy", "surge", "boom", "rally"],
        }
        
        scores = {}
        for emotion, keywords in emotion_keywords.items():
            scores[emotion] = sum(1 for kw in keywords if kw in text)
        
        if max(scores.values()) == 0:
            return "neutral"
        
        return max(scores, key=scores.get)
    
    def _calculate_relevance(self, candidate: Dict) -> float:
        # Finance specific keywords
        keywords = [
            "stock", "market", "economy", "finance", "money", "invest", "crypto", 
            "bitcoin", "fed", "inflation", "rate", "tax", "wealth", "debt", 
            "bank", "recession", "growth", "earning", "dividend", "portfolio"
        ]
        
        text = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        matches = sum(1 for kw in keywords if kw in text)
        
        relevance = min(matches / 2.0, 1.0) # 2 keywords = 100%
        
        if candidate.get("origin_count", 1) >= 3:
            relevance = min(relevance + 0.2, 1.0)
            
        return round(relevance, 2)

    def _check_financial_accuracy(self, candidate: Dict) -> bool:
        # Simple check for obvious red flags or fake claims
        text = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        
        red_flags = [
            "guaranteed return", "free money", "instant profit", 
            "nigerian prince", "send me bitcoin", "1000x guaranteed"
        ]
        
        for flag in red_flags:
            if flag in text:
                return False
        return True
