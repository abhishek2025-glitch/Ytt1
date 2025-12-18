#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from datetime import datetime

from shared import get_logger, resource_monitor, cache_manager
from sense import TrendAggregator, SemanticDeduplicator
from validation import TrendValidator
from scoring import VPSScorer
from decision import NarrativeSelector
from generation import ContentGenerator
from production import VideoAssembler, AssetManager
from publishing import YouTubePublisher
from memory import RCIManager
from learning import PatternAnalyzer
from governor import SafetyChecker

logger = get_logger(__name__)

class ViralosPrime:
    def __init__(self):
        self.aggregator = TrendAggregator()
        self.deduplicator = SemanticDeduplicator()
        self.validator = TrendValidator()
        self.scorer = VPSScorer()
        self.selector = NarrativeSelector()
        self.generator = ContentGenerator()
        self.assembler = VideoAssembler()
        self.asset_manager = AssetManager()
        self.publisher = YouTubePublisher()
        self.rci_manager = RCIManager()
        self.pattern_analyzer = PatternAnalyzer()
        self.safety_checker = SafetyChecker()
        
        logger.info("VIRALOS PRIME v2.0 initialized")
    
    def run_daily_production(self):
        logger.info("=== STARTING DAILY PRODUCTION ===")
        start_time = datetime.utcnow()
        
        try:
            logger.info("STAGE 1: SENSE - Discovering trends")
            trends = self.aggregator.aggregate_all()
            logger.info(f"Discovered {len(trends)} trends")
            
            logger.info("STAGE 2: DEDUPLICATION")
            unique_trends = self.deduplicator.deduplicate(trends)
            logger.info(f"Deduplicated to {len(unique_trends)} unique trends")
            
            self._save_output("trend_records.json", unique_trends)
            
            logger.info("STAGE 3: VALIDATION")
            validated = self.validator.validate_batch(unique_trends)
            passed_validation = [v for v in validated if v.get("passed", False)]
            logger.info(f"Validated: {len(passed_validation)}/{len(validated)} passed")
            
            self._save_output("validated_candidates.json", passed_validation)
            
            logger.info("STAGE 4: VPS SCORING")
            scored = self.scorer.score_batch(passed_validation)
            logger.info(f"Scored {len(scored)} candidates")
            
            self._save_output("scored_candidates.json", scored)
            
            logger.info("STAGE 5: DECISION - Selecting content")
            selection = self.selector.select_daily_content(scored, shorts_count=6, long_count=1)
            logger.info(f"Selected {selection['total_selected']} items for production")
            
            self._save_output("selection_plan.json", selection)
            
            logger.info("STAGE 6: GENERATION - Creating content")
            all_selected = selection["shorts"] + selection["long"]
            generated_content = []
            
            for topic in all_selected:
                content = self.generator.generate_content(topic)
                generated_content.append(content)
            
            logger.info(f"Generated {len(generated_content)} content items")
            
            logger.info("STAGE 7: SAFETY CHECK")
            safety_results = self.safety_checker.batch_check([
                {"video_id": c["video_id"], "title": c["metadata"]["titles"][0], "description": c["metadata"]["description"]}
                for c in generated_content
            ])
            
            approved_content = [
                c for c, s in zip(generated_content, safety_results)
                if s["action"] in ["approve", "add_attribution"]
            ]
            logger.info(f"Safety check: {len(approved_content)}/{len(generated_content)} approved")
            
            logger.info("STAGE 8: PRODUCTION - Assembling videos")
            assembled = self.assembler.batch_assemble(approved_content)
            logger.info(f"Assembled {len(assembled)} videos")
            
            self._save_output("assembled_videos.json", assembled)
            
            logger.info("STAGE 9: PUBLISHING")
            published_count = 0
            
            for i, item in enumerate(assembled):
                if item["status"] == "success" and item["video_path"]:
                    privacy = "unlisted" if i < 6 else "public"
                    
                    result = self.publisher.publish_video(
                        item["video_path"],
                        item["metadata"],
                        privacy
                    )
                    
                    if result:
                        published_count += 1
                        
                        rci_record = {
                            "video_id": item["video_id"],
                            "hook": generated_content[i]["hooks"][0] if generated_content[i]["hooks"] else "",
                            "title": item["metadata"]["titles"][0],
                            "format": item["metadata"].get("format", "short"),
                            "posting_time": datetime.utcnow().isoformat(),
                            "publishing_hour": datetime.utcnow().hour,
                            "day_of_week": datetime.utcnow().strftime("%A"),
                            "niche": generated_content[i]["topic"].get("niche", "general"),
                            "narrative_lane": generated_content[i]["topic"].get("narrative_lane", "unknown"),
                            "vps_score": generated_content[i]["topic"].get("final_score", 0),
                        }
                        
                        self.rci_manager.add_record(rci_record)
            
            logger.info(f"Published {published_count} videos")
            
            logger.info("STAGE 10: CLEANUP")
            cache_manager.cleanup_expired()
            resource_monitor.log_stats()
            
            elapsed = (datetime.utcnow() - start_time).total_seconds() / 60
            logger.info(f"=== DAILY PRODUCTION COMPLETE === ({elapsed:.1f} minutes)")
            
            summary = {
                "status": "success",
                "elapsed_minutes": round(elapsed, 1),
                "trends_discovered": len(trends),
                "videos_published": published_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            self._save_output("daily_summary.json", summary)
            return summary
            
        except Exception as e:
            logger.error(f"Daily production failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    def run_weekly_learning(self):
        logger.info("=== STARTING WEEKLY LEARNING ===")
        
        try:
            recent_records = self.rci_manager.get_recent_records(days=7)
            logger.info(f"Analyzing {len(recent_records)} records from past 7 days")
            
            rules = self.pattern_analyzer.analyze_weekly(recent_records)
            logger.info(f"Generated {len(rules)} learned rules")
            
            self.rci_manager.prune_old_records()
            
            logger.info("=== WEEKLY LEARNING COMPLETE ===")
            return {"status": "success", "rules_generated": len(rules)}
            
        except Exception as e:
            logger.error(f"Weekly learning failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    def run_recovery(self):
        logger.info("=== STARTING RECOVERY WORKER ===")
        
        try:
            processed = self.publisher.process_queue()
            logger.info(f"Processed {processed} queued items")
            
            logger.info("=== RECOVERY COMPLETE ===")
            return {"status": "success", "processed": processed}
            
        except Exception as e:
            logger.error(f"Recovery failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    def _save_output(self, filename: str, data):
        output_dir = Path("data/metrics")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved output to {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [daily|weekly|recovery]")
        sys.exit(1)
    
    mode = sys.argv[1]
    viralos = ViralosPrime()
    
    if mode == "daily":
        result = viralos.run_daily_production()
    elif mode == "weekly":
        result = viralos.run_weekly_learning()
    elif mode == "recovery":
        result = viralos.run_recovery()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)

if __name__ == "__main__":
    main()
