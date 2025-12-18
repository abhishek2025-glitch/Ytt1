import time
from threading import Lock
from typing import Optional
from .logger import get_logger

logger = get_logger(__name__)

class TokenBucket:
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_period: float = 3600.0,
    ):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.last_refill = time.time()
        self.lock = Lock()
        
        logger.info(
            "TokenBucket initialized",
            capacity=capacity,
            refill_rate=refill_rate,
            refill_period=refill_period,
        )
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed >= self.refill_period:
            periods = elapsed / self.refill_period
            tokens_to_add = periods * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            logger.debug(
                "TokenBucket refilled",
                tokens_added=tokens_to_add,
                current_tokens=self.tokens,
            )
    
    def consume(self, tokens: int = 1, blocking: bool = False, timeout: Optional[float] = None) -> bool:
        start_time = time.time()
        
        while True:
            with self.lock:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(
                        "Tokens consumed",
                        consumed=tokens,
                        remaining=self.tokens,
                    )
                    return True
                
                if not blocking:
                    logger.warning(
                        "Insufficient tokens",
                        requested=tokens,
                        available=self.tokens,
                    )
                    return False
            
            if timeout and (time.time() - start_time) >= timeout:
                logger.warning(
                    "Token consumption timeout",
                    requested=tokens,
                    timeout=timeout,
                )
                return False
            
            time.sleep(0.1)
    
    def get_tokens(self) -> float:
        with self.lock:
            self._refill()
            return self.tokens
    
    def reset(self):
        with self.lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.time()
            logger.info("TokenBucket reset")

class RateLimiter:
    def __init__(self):
        self.buckets = {}
        self.lock = Lock()
    
    def get_bucket(self, name: str, capacity: int, refill_rate: float, refill_period: float = 3600.0) -> TokenBucket:
        with self.lock:
            if name not in self.buckets:
                self.buckets[name] = TokenBucket(capacity, refill_rate, refill_period)
            return self.buckets[name]
    
    def consume(self, name: str, tokens: int = 1, **bucket_kwargs) -> bool:
        bucket = self.get_bucket(
            name,
            bucket_kwargs.get("capacity", 100),
            bucket_kwargs.get("refill_rate", 100),
            bucket_kwargs.get("refill_period", 3600.0),
        )
        return bucket.consume(tokens, blocking=bucket_kwargs.get("blocking", False))

rate_limiter = RateLimiter()
