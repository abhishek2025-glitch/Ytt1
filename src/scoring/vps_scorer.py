import json
from pathlib import Path
from typing import List, Dict
from ..shared import get_logger, embedding_service

logger = get_logger(__name__)

class VPSScorer:
    def __init__(self):
        self.niche_config = self._load_niche_config()
        self.weights = {
            "emotional_charge": 0.15,
            "curiosity_gap": 0.20,
            "timeliness": 0.10,
            "shareability": 0.15,
            "simplicity": 0.10,
            "historical_pattern": 0.10,
            "narrative_continuity": 0.15,
        }
        logger.info("VPSScorer initialized")
    
    def _load_niche_config(self) -> Dict:
        config_path = Path("config/niche_multipliers.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"niches": {}, "default_multiplier": 1.0}
    
    def score_batch(self, candidates: List[Dict]) -> List[Dict]:
        scored = []
        
        for candidate in candidates:
            score_record = self.score_single(candidate)
            scored.append(score_record)
        
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        
        logger.info(
            "Scoring complete",
            count=len(scored),
            top_score=scored[0]["final_score"] if scored else 0,
            threshold_70_count=sum(1 for s in scored if s["final_score"] >= 70)
        )
        
        return scored
    
    def score_single(self, candidate: Dict) -> Dict:
        components = {
            "emotional_charge": self._score_emotional_charge(candidate),
            "curiosity_gap": self._score_curiosity_gap(candidate),
            "timeliness": self._score_timeliness(candidate),
            "shareability": self._score_shareability(candidate),
            "simplicity": self._score_simplicity(candidate),
            "historical_pattern": self._score_historical_pattern(candidate),
            "narrative_continuity": self._score_narrative_continuity(candidate),
        }
        
        base_vps = sum(
            components[component] * self.weights[component]
            for component in components
        )
        
        niche = self._detect_niche(candidate)
        niche_multiplier = self._get_niche_multiplier(niche)
        
        saturation_factor = self._calculate_saturation_factor(candidate)
        
        final_score = base_vps * niche_multiplier * saturation_factor
        
        return {
            "candidate_id": candidate.get("id"),
            "title": candidate.get("title"),
            "base_vps": round(base_vps, 2),
            "components": {k: round(v, 2) for k, v in components.items()},
            "niche": niche,
            "niche_multiplier": niche_multiplier,
            "saturation_factor": saturation_factor,
            "competitor_count": 0,
            "final_score": round(final_score, 2),
        }
    
    def _score_emotional_charge(self, candidate: Dict) -> float:
        emotion = candidate.get("emotional_vector", "neutral")
        emotion_scores = {
            "surprise": 85,
            "concern": 80,
            "curiosity": 90,
            "awe": 75,
            "neutral": 40,
        }
        return emotion_scores.get(emotion, 50)
    
    def _score_curiosity_gap(self, candidate: Dict) -> float:
        title = candidate.get("title", "").lower()
        
        curiosity_triggers = ["why", "how", "what", "secret", "hidden", "revealed", "truth"]
        trigger_count = sum(1 for trigger in curiosity_triggers if trigger in title)
        
        return min(50 + (trigger_count * 15), 100)
    
    def _score_timeliness(self, candidate: Dict) -> float:
        import datetime
        timestamp_str = candidate.get("timestamp", "")
        
        try:
            if timestamp_str:
                timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age_hours = (datetime.datetime.now(datetime.timezone.utc) - timestamp).total_seconds() / 3600
                
                if age_hours < 6:
                    return 95
                elif age_hours < 24:
                    return 80
                elif age_hours < 48:
                    return 60
                else:
                    return 40
        except:
            pass
        
        return 50
    
    def _score_shareability(self, candidate: Dict) -> float:
        title = candidate.get("title", "")
        
        shareable_elements = ["data", "study", "research", "reveals", "shows", "proves"]
        element_count = sum(1 for elem in shareable_elements if elem in title.lower())
        
        base_score = 60
        bonus = element_count * 10
        
        return min(base_score + bonus, 100)
    
    def _score_simplicity(self, candidate: Dict) -> float:
        explainability = candidate.get("explainability_seconds", 60)
        
        if explainability <= 30:
            return 95
        elif explainability <= 45:
            return 80
        elif explainability <= 60:
            return 65
        else:
            return 40
    
    def _score_historical_pattern(self, candidate: Dict) -> float:
        return 70
    
    def _score_narrative_continuity(self, candidate: Dict) -> float:
        return 65
    
    def _detect_niche(self, candidate: Dict) -> str:
        combined = f"{candidate.get('title', '')} {candidate.get('description', '')}".lower()
        
        for niche_name, niche_data in self.niche_config.get("niches", {}).items():
            keywords = niche_data.get("keywords", [])
            if any(kw in combined for kw in keywords):
                return niche_name
        
        return "general"
    
    def _get_niche_multiplier(self, niche: str) -> float:
        niche_data = self.niche_config.get("niches", {}).get(niche, {})
        return niche_data.get("multiplier", self.niche_config.get("default_multiplier", 1.0))
    
    def _calculate_saturation_factor(self, candidate: Dict) -> float:
        competitor_count = 0
        
        if competitor_count <= 2:
            return 1.8
        elif competitor_count <= 5:
            return 1.0
        elif competitor_count <= 15:
            return 0.7
        elif competitor_count <= 50:
            return 0.3
        else:
            return 0.1
