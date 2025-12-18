from pathlib import Path
from typing import List, Dict, Optional
from ..shared import get_logger, cache_manager

logger = get_logger(__name__)

class AssetManager:
    def __init__(self):
        self.asset_dir = Path("data/assets")
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        logger.info("AssetManager initialized")
    
    def fetch_assets(self, scene_hints: List[str]) -> List[Dict]:
        assets = []
        
        for hint in scene_hints:
            asset = self._fetch_single_asset(hint)
            if asset:
                assets.append(asset)
        
        logger.info("Assets fetched", requested=len(scene_hints), found=len(assets))
        return assets
    
    def _fetch_single_asset(self, hint: str) -> Optional[Dict]:
        cached = cache_manager.get("assets", hint, max_age_hours=168)
        if cached:
            return cached
        
        asset = {
            "hint": hint,
            "type": "stock_video",
            "source": "placeholder",
            "url": None,
            "license": "free_commercial",
        }
        
        cache_manager.set("assets", hint, asset, ttl_hours=168)
        return asset
