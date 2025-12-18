import psutil
import time
from typing import Dict
from pathlib import Path
from .logger import get_logger

logger = get_logger(__name__)

class ResourceMonitor:
    def __init__(self, max_memory_gb: float = 4.5):
        self.max_memory_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
        self.start_time = time.time()
        
        logger.info("ResourceMonitor initialized", max_memory_gb=max_memory_gb)
    
    def get_memory_usage(self) -> Dict:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / (1024 * 1024),
            'vms_mb': memory_info.vms / (1024 * 1024),
            'percent': process.memory_percent(),
        }
    
    def get_disk_usage(self, path: str = "/home/engine/project") -> Dict:
        disk = psutil.disk_usage(path)
        
        return {
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'percent': disk.percent,
        }
    
    def get_directory_size(self, path: str) -> float:
        directory = Path(path)
        if not directory.exists():
            return 0.0
        
        total_size = 0
        for item in directory.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except:
                    pass
        
        return total_size / (1024 * 1024)
    
    def check_memory_limit(self) -> bool:
        memory = self.get_memory_usage()
        memory_bytes = memory['rss_mb'] * 1024 * 1024
        
        if memory_bytes > self.max_memory_bytes:
            logger.warning(
                "Memory limit exceeded",
                current_mb=memory['rss_mb'],
                limit_mb=self.max_memory_bytes / (1024 * 1024),
            )
            return False
        
        return True
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time
    
    def get_stats(self) -> Dict:
        memory = self.get_memory_usage()
        disk = self.get_disk_usage()
        
        cache_size = self.get_directory_size("data/cache")
        assets_size = self.get_directory_size("data/assets")
        memory_size = self.get_directory_size("memory")
        
        return {
            'uptime_seconds': self.get_uptime(),
            'memory': memory,
            'disk': disk,
            'directories': {
                'cache_mb': cache_size,
                'assets_mb': assets_size,
                'memory_mb': memory_size,
            },
            'within_limits': self.check_memory_limit(),
        }
    
    def log_stats(self):
        stats = self.get_stats()
        logger.info("Resource stats", **stats)

resource_monitor = ResourceMonitor()
