import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..shared import get_logger

logger = get_logger(__name__)

class RCIManager:
    def __init__(self):
        self.memory_dir = Path("memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.half_life_days = 90
        self.max_age_days = 270
        
        logger.info("RCIManager initialized", half_life=self.half_life_days)
    
    def add_record(self, record: Dict):
        today = datetime.utcnow().strftime("%Y%m%d")
        archive_file = self.memory_dir / f"rci_archive_{today}.json"
        
        records = []
        if archive_file.exists():
            with open(archive_file, 'r') as f:
                records = json.load(f)
        
        records.append(record)
        
        with open(archive_file, 'w') as f:
            json.dump(records, f, indent=2)
        
        logger.info("RCI record added", video_id=record.get("video_id"), date=today)
    
    def get_recent_records(self, days: int = 7) -> List[Dict]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = []
        for archive_file in sorted(self.memory_dir.glob("rci_archive_*.json")):
            try:
                date_str = archive_file.stem.split("_")[-1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date >= cutoff_date:
                    with open(archive_file, 'r') as f:
                        file_records = json.load(f)
                        records.extend(file_records)
            except Exception as e:
                logger.error("Error reading archive", file=str(archive_file), error=str(e))
        
        logger.info("Recent records retrieved", days=days, count=len(records))
        return records
    
    def prune_old_records(self):
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_age_days)
        
        deleted = 0
        for archive_file in self.memory_dir.glob("rci_archive_*.json"):
            try:
                date_str = archive_file.stem.split("_")[-1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    archive_file.unlink()
                    deleted += 1
                    logger.info("Deleted old archive", file=str(archive_file))
            except Exception as e:
                logger.error("Error pruning archive", file=str(archive_file), error=str(e))
        
        logger.info("Pruning complete", deleted=deleted, max_age_days=self.max_age_days)
    
    def search(self, filters: Dict) -> List[Dict]:
        all_records = self.get_recent_records(days=30)
        
        filtered = []
        for record in all_records:
            match = True
            
            for key, value in filters.items():
                if key in record and record[key] != value:
                    match = False
                    break
            
            if match:
                filtered.append(record)
        
        logger.info("Search complete", filters=filters, results=len(filtered))
        return filtered
