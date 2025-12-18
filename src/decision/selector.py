import json
from pathlib import Path
from typing import List, Dict
from ..shared import get_logger

logger = get_logger(__name__)

class NarrativeSelector:
    def __init__(self):
        self.narrative_config = self._load_narrative_config()
        self.lanes = self.narrative_config.get("lanes", {})
        logger.info("NarrativeSelector initialized", lanes=list(self.lanes.keys()))
    
    def _load_narrative_config(self) -> Dict:
        config_path = Path("config/narrative_lanes.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"lanes": {}, "allocation_rules": {}}
    
    def select_daily_content(self, scored_candidates: List[Dict], shorts_count: int = 6, long_count: int = 1) -> Dict:
        if not scored_candidates:
            logger.warning("No candidates to select from")
            return {"shorts": [], "long": []}
        
        candidates_above_threshold = [c for c in scored_candidates if c.get("final_score", 0) >= 70]
        
        if len(candidates_above_threshold) < shorts_count + long_count:
            logger.warning(
                "Insufficient candidates above threshold",
                available=len(candidates_above_threshold),
                needed=shorts_count + long_count
            )
            candidates_above_threshold = scored_candidates[:shorts_count + long_count]
        
        lane_allocated = []
        for candidate in candidates_above_threshold[:shorts_count + long_count]:
            lane = self._assign_lane(candidate)
            candidate["narrative_lane"] = lane
            candidate["format"] = "short"
            lane_allocated.append(candidate)
        
        if len(lane_allocated) > long_count:
            lane_allocated[0]["format"] = "long"
        
        shorts = [c for c in lane_allocated if c["format"] == "short"][:shorts_count]
        longs = [c for c in lane_allocated if c["format"] == "long"][:long_count]
        
        selection_plan = {
            "shorts": shorts,
            "long": longs,
            "total_selected": len(shorts) + len(longs),
            "lane_distribution": self._get_lane_distribution(shorts + longs),
        }
        
        logger.info(
            "Content selection complete",
            shorts=len(shorts),
            longs=len(longs),
            lanes=selection_plan["lane_distribution"]
        )
        
        return selection_plan
    
    def _assign_lane(self, candidate: Dict) -> str:
        title_lower = candidate.get("title", "").lower()
        niche = candidate.get("niche", "general")
        
        lane_scores = {}
        for lane_id, lane_data in self.lanes.items():
            score = 0
            keywords = lane_data.get("keywords", [])
            
            for keyword in keywords:
                if keyword in title_lower:
                    score += 1
            
            lane_scores[lane_id] = score
        
        if max(lane_scores.values()) == 0:
            if niche in ["finance", "crypto"]:
                return "market_inflection"
            elif niche in ["ai_tech"]:
                return "ai_power"
            elif niche in ["business"]:
                return "competitive"
            else:
                return "hidden_data"
        
        return max(lane_scores, key=lane_scores.get)
    
    def _get_lane_distribution(self, selected: List[Dict]) -> Dict:
        distribution = {}
        for item in selected:
            lane = item.get("narrative_lane", "unknown")
            distribution[lane] = distribution.get(lane, 0) + 1
        return distribution
