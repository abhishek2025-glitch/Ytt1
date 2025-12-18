import json
from pathlib import Path
from typing import List, Dict, Optional
from ..shared import get_logger

logger = get_logger(__name__)

class NarrativeSelector:
    def __init__(self):
        self.narrative_config = self._load_narrative_config()
        self.lanes = self.narrative_config.get("lanes", {})
        self.allocation_rules = self.narrative_config.get("allocation_rules", {})
        logger.info("NarrativeSelector initialized", lanes=list(self.lanes.keys()))
    
    def _load_narrative_config(self) -> Dict:
        config_path = Path("config/narrative_lanes.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"lanes": {}, "allocation_rules": {}}
    
    def select_daily_content(self, scored_candidates: List[Dict], count: int = 3) -> Dict:
        if not scored_candidates:
            logger.warning("No candidates to select from")
            return {"shorts": [], "long": []}
        
        # 1. Assign Lanes and Filter
        candidates_with_lanes = []
        for c in scored_candidates:
            if c.get("final_score", 0) < 50: # Minimum viability
                continue
            c["narrative_lane"] = self._assign_lane(c)
            candidates_with_lanes.append(c)
            
        # Sort by score
        candidates_with_lanes.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 2. Select with Quotas and Dedup
        selected = []
        selected_titles = set()
        lane_usage = {lane: 0 for lane in self.lanes}
        total_quota = count
        
        # Calculate target counts per lane
        lane_targets = {}
        for lane, data in self.lanes.items():
            min_pct = data.get("percentage_min", 0)
            target = max(1, int(total_quota * (min_pct / 100.0)))
            lane_targets[lane] = target

        # Selection Loop
        for candidate in candidates_with_lanes:
            if len(selected) >= count:
                break
                
            title = candidate.get("title", "")
            lane = candidate.get("narrative_lane")
            score = candidate.get("final_score", 0)
            
            # Semantic Dedup (Simple title check for now)
            if any(self._is_semantically_similar(title, t) for t in selected_titles):
                continue
            
            # Quota Check
            current_lane_count = lane_usage.get(lane, 0)
            is_lane_full = current_lane_count >= lane_targets.get(lane, 99)
            
            # Override if High Score
            soft_quota_override = self.allocation_rules.get("soft_quota_override_vps", 85)
            if is_lane_full and score < soft_quota_override:
                # Try to find another candidate unless we are desperate
                # But we iterate in score order, so skipping might mean lower score later.
                # If we skip, we might find a candidate for an under-filled lane.
                # Check if other lanes are under-filled
                under_filled_lanes = [l for l, t in lane_targets.items() if lane_usage.get(l, 0) < t]
                if under_filled_lanes:
                    continue # Skip this high score to fill quota elsewhere
            
            # Add to selection
            selected.append(candidate)
            selected_titles.add(title)
            lane_usage[lane] = lane_usage.get(lane, 0) + 1
            
        # 3. Format Assignment (1 Long, rest Shorts)
        # Best candidate gets Long form if suitable, or random?
        # Usually highest score = Long form candidate
        if selected:
            # Sort selected by score again just to be sure
            selected.sort(key=lambda x: x["final_score"], reverse=True)
            selected[0]["format"] = "long"
            for item in selected[1:]:
                item["format"] = "short"
        
        shorts = [c for c in selected if c["format"] == "short"]
        longs = [c for c in selected if c["format"] == "long"]
        
        selection_plan = {
            "shorts": shorts,
            "long": longs,
            "total_selected": len(shorts) + len(longs),
            "lane_distribution": lane_usage,
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
        
        lane_scores = {}
        for lane_id, lane_data in self.lanes.items():
            score = 0
            keywords = lane_data.get("keywords", [])
            
            for keyword in keywords:
                if keyword in title_lower:
                    score += 1
            
            lane_scores[lane_id] = score
        
        if max(lane_scores.values()) == 0:
            # Default fallback based on basic keywords if config keywords fail
            if "crypto" in title_lower or "bitcoin" in title_lower:
                return "crypto_blockchain"
            elif "stock" in title_lower or "market" in title_lower:
                return "stock_market"
            elif "fed" in title_lower or "economy" in title_lower:
                return "macro_economics"
            elif "psychology" in title_lower or "mind" in title_lower:
                return "investing_psychology"
            else:
                return "stock_market" # Default to biggest lane
        
        return max(lane_scores, key=lane_scores.get)
    
    def _is_semantically_similar(self, title1: str, title2: str) -> bool:
        # Simple Jaccard similarity on words
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return (intersection / union) > 0.5 if union > 0 else False
