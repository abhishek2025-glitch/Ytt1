import os
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from ..shared import get_logger, handle_errors

logger = get_logger(__name__)

class YouTubePublisher:
    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
        self.queue_dir = Path("data/queue")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("YouTubePublisher initialized", has_credentials=bool(self.client_id))
    
    @handle_errors(fallback_value=None)
    def publish_video(self, video_path: str, metadata: Dict, privacy: str = "unlisted") -> Optional[Dict]:
        video_id = metadata.get("video_id", "unknown")
        title = metadata.get("titles", ["Untitled"])[0]
        
        logger.info(
            "Publishing video",
            video_id=video_id,
            title=title[:50],
            privacy=privacy
        )
        
        if not self.client_id or not Path(video_path).exists():
            logger.warning("Cannot publish: missing credentials or video file")
            return self._queue_for_retry(video_path, metadata, privacy)
        
        publish_record = {
            "video_id": video_id,
            "format": metadata.get("format", "short"),
            "title": title,
            "scheduled_time": datetime.utcnow().isoformat(),
            "actual_publish_time": datetime.utcnow().isoformat(),
            "status": "published",
            "youtube_video_id": f"yt_{video_id}",
            "privacy_status": privacy,
            "canary_status": "active" if privacy == "unlisted" else "none",
            "attempts": 1,
            "error_log": [],
        }
        
        self._save_publish_record(publish_record)
        
        logger.info("Video published (simulated)", youtube_id=publish_record["youtube_video_id"])
        return publish_record
    
    def _queue_for_retry(self, video_path: str, metadata: Dict, privacy: str) -> Dict:
        queue_item = {
            "video_path": video_path,
            "metadata": metadata,
            "privacy": privacy,
            "queued_at": datetime.utcnow().isoformat(),
            "attempts": 0,
        }
        
        queue_file = self.queue_dir / f"queue_{metadata.get('video_id', 'unknown')}.json"
        with open(queue_file, 'w') as f:
            json.dump(queue_item, f, indent=2)
        
        logger.info("Video queued for retry", queue_file=str(queue_file))
        return queue_item
    
    def _save_publish_record(self, record: Dict):
        records_dir = Path("data/metrics")
        records_dir.mkdir(parents=True, exist_ok=True)
        
        record_file = records_dir / f"publish_{record['video_id']}.json"
        with open(record_file, 'w') as f:
            json.dump(record, f, indent=2)
    
    def process_queue(self) -> int:
        queue_files = list(self.queue_dir.glob("queue_*.json"))
        
        processed = 0
        for queue_file in queue_files:
            try:
                with open(queue_file, 'r') as f:
                    queue_item = json.load(f)
                
                result = self.publish_video(
                    queue_item["video_path"],
                    queue_item["metadata"],
                    queue_item.get("privacy", "unlisted")
                )
                
                if result and result.get("status") == "published":
                    queue_file.unlink()
                    processed += 1
            except Exception as e:
                logger.error("Queue processing error", file=str(queue_file), error=str(e))
        
        logger.info("Queue processed", processed=processed, remaining=len(list(self.queue_dir.glob("queue_*.json"))))
        return processed
