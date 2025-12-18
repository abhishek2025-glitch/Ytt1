import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from ..shared import get_logger

logger = get_logger(__name__)

class CanaryMonitor:
    def __init__(self):
        self.metrics_dir = Path("data/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = Path("data/history/performance_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load history percentiles or defaults
        self.percentiles = self._load_percentiles()
        logger.info("CanaryMonitor initialized")
        
    def _load_percentiles(self) -> Dict:
        # In a real system, load from history.json and calculate P50, P80.
        # Here we use static baselines from the ticket (Phase 1/2 stats).
        return {
            "ctr": {"p50": 0.04, "p80": 0.06}, # 4%, 6%
            "retention": {"p50": 0.35, "p80": 0.50}, # 35%, 50%
            "velocity": {"p50": 10, "p80": 50}, # views per min
        }
    
    def check_active_canaries(self) -> List[Dict]:
        decisions = []
        
        # Find all publish records that are "active" canaries
        for record_file in self.metrics_dir.glob("publish_*.json"):
            try:
                with open(record_file, 'r') as f:
                    record = json.load(f)
                
                if record.get("canary_status") != "active":
                    continue
                    
                publish_time = datetime.fromisoformat(record["actual_publish_time"])
                now = datetime.utcnow()
                age_minutes = (now - publish_time).total_seconds() / 60
                
                if age_minutes >= 30:
                    decision = self._evaluate_canary(record)
                    decisions.append(decision)
                    
                    # Update record
                    record["canary_status"] = "completed"
                    record["canary_result"] = decision["action"]
                    record["public_status"] = "public" if decision["action"] == "promote" else "private"
                    
                    with open(record_file, 'w') as f:
                        json.dump(record, f, indent=2)
                        
                    logger.info("Canary evaluation complete", video_id=record["video_id"], action=decision["action"])
            except Exception as e:
                logger.error("Error checking canary", file=str(record_file), error=str(e))
                
        return decisions
    
    def _evaluate_canary(self, record: Dict) -> Dict:
        # Simulate fetching metrics from YouTube API
        # in a real system: self.youtube_client.get_video_metrics(record['youtube_video_id'])
        metrics = self._simulate_metrics(record)
        
        score = 0
        reasons = []
        
        # CTR Check
        if metrics["ctr"] >= self.percentiles["ctr"]["p80"]:
            score += 2
            reasons.append(f"High CTR ({metrics['ctr']:.1%})")
        elif metrics["ctr"] >= self.percentiles["ctr"]["p50"]:
            score += 1
            reasons.append(f"Good CTR ({metrics['ctr']:.1%})")
            
        # Retention Check
        if metrics["retention"] >= self.percentiles["retention"]["p80"]:
            score += 2
            reasons.append(f"High Retention ({metrics['retention']:.1%})")
        elif metrics["retention"] >= self.percentiles["retention"]["p50"]:
            score += 1
            reasons.append(f"Good Retention ({metrics['retention']:.1%})")
            
        # Decision Logic
        action = "suppress"
        if score >= 3: # Top tier
            action = "promote"
        elif score >= 1: # Mid tier
            action = "promote" # Ticket says P50-P80 promote
        else:
            action = "suppress"
            
        return {
            "video_id": record["video_id"],
            "metrics": metrics,
            "score": score,
            "reasons": reasons,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _simulate_metrics(self, record: Dict) -> Dict:
        # Deterministic simulation based on video ID hash for consistency
        import hashlib
        h = int(hashlib.md5(record["video_id"].encode()).hexdigest(), 16)
        
        # Bias towards decent metrics 
        base_ctr = 0.03 + (h % 50) / 1000.0 # 0.03 - 0.08
        base_ret = 0.30 + (h % 40) / 100.0 # 0.30 - 0.70
        
        return {
            "ctr": base_ctr,
            "retention": base_ret,
            "views": 100 + (h % 500),
            "likes": 5 + (h % 50),
            "comments": 1 + (h % 10)
        }
