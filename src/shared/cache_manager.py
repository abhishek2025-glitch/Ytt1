import json
import time
from pathlib import Path
from typing import Any, Optional, Dict
import hashlib
from datetime import datetime, timedelta
from .logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = "data/cache", max_size_gb: float = 2.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()
        
        logger.info("CacheManager initialized", cache_dir=str(cache_dir), max_size_gb=max_size_gb)
    
    def _load_index(self) -> Dict:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_cache_key(self, namespace: str, key: str) -> str:
        combined = f"{namespace}:{key}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, namespace: str, key: str, max_age_hours: Optional[float] = None) -> Optional[Any]:
        cache_key = self._get_cache_key(namespace, key)
        
        if cache_key not in self.index:
            return None
        
        entry = self.index[cache_key]
        
        if max_age_hours:
            age_hours = (time.time() - entry['timestamp']) / 3600
            if age_hours > max_age_hours:
                logger.debug("Cache entry expired", namespace=namespace, age_hours=age_hours)
                return None
        
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            del self.index[cache_key]
            self._save_index()
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            entry['hits'] = entry.get('hits', 0) + 1
            entry['last_access'] = time.time()
            self._save_index()
            
            logger.debug("Cache hit", namespace=namespace, key=key[:50])
            return data
        except Exception as e:
            logger.error("Cache read error", error=str(e), cache_key=cache_key)
            return None
    
    def set(self, namespace: str, key: str, value: Any, ttl_hours: Optional[float] = None):
        cache_key = self._get_cache_key(namespace, key)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(value, f)
            
            size = cache_path.stat().st_size
            
            self.index[cache_key] = {
                'namespace': namespace,
                'key': key[:100],
                'timestamp': time.time(),
                'last_access': time.time(),
                'size': size,
                'hits': 0,
                'ttl_hours': ttl_hours,
            }
            
            self._save_index()
            self._enforce_size_limit()
            
            logger.debug("Cache set", namespace=namespace, key=key[:50], size=size)
        except Exception as e:
            logger.error("Cache write error", error=str(e), namespace=namespace)
    
    def delete(self, namespace: str, key: str):
        cache_key = self._get_cache_key(namespace, key)
        
        if cache_key in self.index:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            
            del self.index[cache_key]
            self._save_index()
            logger.debug("Cache entry deleted", namespace=namespace, key=key[:50])
    
    def clear_namespace(self, namespace: str):
        to_delete = [k for k, v in self.index.items() if v.get('namespace') == namespace]
        
        for cache_key in to_delete:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            del self.index[cache_key]
        
        self._save_index()
        logger.info("Namespace cleared", namespace=namespace, count=len(to_delete))
    
    def _enforce_size_limit(self):
        total_size = sum(entry.get('size', 0) for entry in self.index.values())
        
        if total_size <= self.max_size_bytes:
            return
        
        entries = list(self.index.items())
        entries.sort(key=lambda x: (
            x[1].get('hits', 0) / max((time.time() - x[1].get('timestamp', time.time())) / 3600, 1),
            x[1].get('last_access', 0)
        ))
        
        while total_size > self.max_size_bytes and entries:
            cache_key, entry = entries.pop(0)
            cache_path = self._get_cache_path(cache_key)
            
            if cache_path.exists():
                cache_path.unlink()
            
            total_size -= entry.get('size', 0)
            del self.index[cache_key]
        
        self._save_index()
        logger.info("Cache size limit enforced", final_size_mb=total_size / (1024 * 1024))
    
    def cleanup_expired(self):
        now = time.time()
        to_delete = []
        
        for cache_key, entry in self.index.items():
            ttl_hours = entry.get('ttl_hours')
            if ttl_hours:
                age_hours = (now - entry['timestamp']) / 3600
                if age_hours > ttl_hours:
                    to_delete.append(cache_key)
        
        for cache_key in to_delete:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            del self.index[cache_key]
        
        if to_delete:
            self._save_index()
            logger.info("Expired cache entries cleaned", count=len(to_delete))
    
    def get_stats(self) -> Dict:
        total_size = sum(entry.get('size', 0) for entry in self.index.values())
        total_hits = sum(entry.get('hits', 0) for entry in self.index.values())
        
        return {
            'total_entries': len(self.index),
            'total_size_mb': total_size / (1024 * 1024),
            'total_hits': total_hits,
            'namespaces': len(set(e.get('namespace') for e in self.index.values())),
        }

cache_manager = CacheManager()
